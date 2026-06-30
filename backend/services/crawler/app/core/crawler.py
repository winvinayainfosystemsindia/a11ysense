import asyncio
import time
import urllib.parse
import fnmatch
import xml.etree.ElementTree as ET
import logging
from collections import deque
from typing import List, Dict, Set
import httpx
from bs4 import BeautifulSoup

from app.schemas.crawl import CrawlRequest, CrawlResponse, PageDiscovery

logger = logging.getLogger(__name__)

# Many sites front their traffic with a WAF/load balancer that 403s requests
# carrying a non-browser User-Agent (e.g. AWS WAF Bot Control). Identify as a
# real browser so the static fetch path doesn't get blocked outright.
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

# Non-HTML Extensions to skip
NON_HTML_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp', '.tiff', '.ico',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp',
    '.zip', '.tar', '.gz', '.rar', '.7z', '.exe', '.dmg', '.pkg',
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.mp3', '.wav', '.ogg', '.m4a',
    '.css', '.js', '.json', '.xml', '.txt', '.woff', '.woff2', '.ttf', '.otf', '.eot'
}

def normalize_url(url: str) -> str:
    """
    Standardizes a URL to ensure reliable deduplication.
    Lowercases the host, removes standard ports, strips fragments, 
    and sorts query parameters.
    """
    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # Remove default ports
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]
        
    path = parsed.path
    # Standardize empty path or trailing slash (remove trailing slash except for root path)
    if not path or path == "/":
        path = ""
    elif len(path) > 1 and path.endswith("/"):
        path = path[:-1]
        
    # Sort query parameters
    query = ""
    if parsed.query:
        params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        params.sort()
        query = urllib.parse.urlencode(params)
        
    # Reassemble without fragments
    return urllib.parse.urlunparse((scheme, netloc, path, parsed.params, query, ""))

class RobotsParser:
    def __init__(self, sitemaps: List[str] = None, disallows: List[str] = None, crawl_delay: float = None):
        self.sitemaps = sitemaps or []
        self.disallows = disallows or []
        self.crawl_delay = crawl_delay

    @classmethod
    async def fetch_and_parse(cls, client: httpx.AsyncClient, base_url: str):
        """
        Fetches the website's robots.txt and parses its contents.
        """
        parsed_base = urllib.parse.urlparse(base_url)
        robots_url = f"{parsed_base.scheme}://{parsed_base.netloc}/robots.txt"
        
        disallows = []
        sitemaps = []
        crawl_delay = None
        
        try:
            response = await client.get(robots_url, timeout=5.0)
            if response.status_code == 200:
                lines = response.text.splitlines()
                current_agent_applies = False
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(':', 1)
                    if len(parts) < 2:
                        continue
                    
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    
                    if key == "user-agent":
                        agent = value.lower()
                        # Apply to our crawler if wildcard or matches specific user agent
                        if agent == "*" or "a11ysense" in agent or "crawler" in agent:
                            current_agent_applies = True
                        else:
                            current_agent_applies = False
                            
                    elif current_agent_applies:
                        if key == "disallow":
                            if value:
                                disallows.append(value)
                        elif key == "crawl-delay":
                            try:
                                crawl_delay = float(value)
                            except ValueError:
                                pass
                                
                    # Sitemap directive is global, not agent specific
                    if key == "sitemap":
                        sitemaps.append(value)
                        
        except Exception as e:
            logger.warning(f"Failed to fetch robots.txt from {robots_url}: {str(e)}")
            
        return cls(sitemaps=sitemaps, disallows=disallows, crawl_delay=crawl_delay)

    def can_fetch(self, url: str) -> bool:
        """
        Checks if a URL path is allowed to be crawled by the robots.txt rules.
        """
        parsed = urllib.parse.urlparse(url)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
            
        for pattern in self.disallows:
            if "*" not in pattern and "?" not in pattern:
                if path.startswith(pattern):
                    return False
            else:
                if fnmatch.fnmatch(path, pattern):
                    return False
        return True

class SitemapParser:
    @staticmethod
    async def fetch_and_extract_urls(client: httpx.AsyncClient, sitemap_url: str, allowed_domain: str) -> List[str]:
        """
        Fetches a sitemap, parsing and extracting loc URLs recursively (handling Sitemap Indexes).
        """
        urls = []
        try:
            response = await client.get(sitemap_url, timeout=10.0)
            if response.status_code != 200:
                return []
                
            root = ET.fromstring(response.content)
            
            # Extract nested sitemaps and URLs
            for elem in root.iter():
                if elem.tag.endswith("loc"):
                    loc_url = elem.text.strip() if elem.text else ""
                    if loc_url:
                        parsed_loc = urllib.parse.urlparse(loc_url)
                        if parsed_loc.netloc.lower() == allowed_domain:
                            if "sitemap" in loc_url.lower() and (loc_url.endswith(".xml") or ".xml" in loc_url):
                                nested_urls = await SitemapParser.fetch_and_extract_urls(client, loc_url, allowed_domain)
                                urls.extend(nested_urls)
                            else:
                                urls.append(loc_url)
        except Exception as e:
            logger.warning(f"Error parsing sitemap {sitemap_url}: {str(e)}")
            
        return list(set(urls))

class WebCrawler:
    def __init__(self, request: CrawlRequest):
        self.request = request
        self.start_url = request.url
        self.max_depth = request.depth
        self.max_pages = request.max_pages
        self.strategy = request.strategy
        
        # Parse domain details
        parsed_start = urllib.parse.urlparse(self.start_url)
        self.allowed_domain = parsed_start.netloc.lower()
        self.allowed_scheme = parsed_start.scheme.lower()
        
        # Crawl status sets
        self.visited_urls: Set[str] = set()
        self.pages_discovered: Dict[str, int] = {}  # url -> depth
        self.ignored_urls: Set[str] = set()
        self.failed_urls: Dict[str, str] = {}
        self.sitemaps_found: List[str] = []
        self.storage_state: Dict = None  # Playwright storage state for auth propagation
        self.auth_headers: Dict[str, str] = {}  # Auth headers extracted during login
        self.url_to_menu_text: Dict[str, str] = {}  # Discovered route -> menu text mapping
        self.clicked_sidebar_items: Set[str] = set()  # Track globally clicked menu/sub-menu texts
        
        self.default_delay = request.crawl_delay
        self.last_request_time = 0.0
        self.exclude_patterns = request.exclude_patterns
        self._relogged = False

    def is_same_domain(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        # Same domain or subdomain
        return netloc == self.allowed_domain or netloc.endswith("." + self.allowed_domain)

    def is_excluded(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
            
        for pattern in self.exclude_patterns:
            if "*" in pattern or "?" in pattern:
                if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(url, pattern):
                    return True
            else:
                if pattern in path or pattern in url:
                    return True
        return False

    def is_non_html(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.lower()
        for ext in NON_HTML_EXTENSIONS:
            if path.endswith(ext):
                return True
        return False

    def _build_response(self, duration: float) -> CrawlResponse:
        """Build CrawlResponse with depth metadata, storage_state, and backward-compat flat URL list."""
        has_creds = self.request.credential_config is not None
        login_url = None
        if has_creds and self.request.credential_config.login_url:
            login_url = normalize_url(self.request.credential_config.login_url)

        pages_with_depth = []
        for url, depth in self.pages_discovered.items():
            is_auth = has_creds and (url != login_url) if login_url else False
            pages_with_depth.append(PageDiscovery(url=url, depth=depth, is_authenticated=is_auth))

        return CrawlResponse(
            start_url=self.start_url,
            pages_discovered=list(self.pages_discovered.keys()),
            pages_with_depth=pages_with_depth,
            pages_depth_map=dict(self.pages_discovered),
            ignored_urls=list(self.ignored_urls),
            failed_urls=self.failed_urls,
            sitemaps_found=self.sitemaps_found,
            duration_seconds=round(duration, 2),
            storage_state=self.storage_state,
            auth_headers=self.auth_headers,
            url_to_menu_text=dict(self.url_to_menu_text),
        )

    def _reset_state(self) -> None:
        """Clear mutable crawl state before retrying with a different strategy."""
        self.visited_urls = set()
        self.pages_discovered = {}
        self.ignored_urls = set()
        self.failed_urls = {}
        self.sitemaps_found = []
        self.storage_state = None
        self.auth_headers = {}
        self.url_to_menu_text = {}
        self.clicked_sidebar_items = set()
        self.last_request_time = 0.0
        self._relogged = False

    async def crawl(self) -> CrawlResponse:
        if self.request.credential_config:
            return await self.crawl_with_playwright()

        response = await self._crawl_with_httpx()

        # Edge case: JS-rendered single-page apps with no sitemap and no
        # server-rendered <a href> links yield only the start page via plain
        # HTTP fetching. Retry once with a real browser so client-side routes
        # can be discovered. Most static/server-rendered sites never hit this
        # branch, so the common case stays on the fast path.
        if len(response.pages_discovered) <= 1 and not response.sitemaps_found:
            logger.info(
                "Static crawl discovered no additional pages beyond the start URL; "
                "retrying with Playwright in case the site renders links client-side."
            )
            self._reset_state()
            try:
                pw_response = await self.crawl_with_playwright()
                if len(pw_response.pages_discovered) > len(response.pages_discovered):
                    return pw_response
            except Exception as e:
                logger.warning(f"Playwright fallback crawl failed: {e}. Returning original static crawl result.")
            return response

        return response

    async def _crawl_with_httpx(self) -> CrawlResponse:
        start_time = time.time()
        
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            **self.request.headers
        }
        
        async with httpx.AsyncClient(
            cookies=self.request.cookies,
            headers=headers,
            follow_redirects=True,
            timeout=10.0
        ) as client:
            
            # 1. Fetch robots.txt and process rules
            robots_parser = None
            if self.request.respect_robots_txt:
                robots_parser = await RobotsParser.fetch_and_parse(client, self.start_url)
                self.sitemaps_found = robots_parser.sitemaps
                
                # Use robots.txt crawl delay if available and delay is not custom-set
                if robots_parser.crawl_delay is not None and self.default_delay == 0.5:
                    self.default_delay = robots_parser.crawl_delay
            
            queue = deque()
            
            # 2. Extract URLs from Sitemaps if available
            sitemap_urls_found = []
            if self.max_depth > 1:
                if self.request.respect_robots_txt and self.sitemaps_found:
                    for sitemap_url in self.sitemaps_found:
                        urls = await SitemapParser.fetch_and_extract_urls(client, sitemap_url, self.allowed_domain)
                        sitemap_urls_found.extend(urls)
                        
                # Fallback to standard `/sitemap.xml` if none is declared
                if not self.sitemaps_found:
                    default_sitemap = f"{self.allowed_scheme}://{self.allowed_domain}/sitemap.xml"
                    urls = await SitemapParser.fetch_and_extract_urls(client, default_sitemap, self.allowed_domain)
                    if urls:
                        self.sitemaps_found.append(default_sitemap)
                        sitemap_urls_found.extend(urls)
            
            # Seed start URL
            normalized_start = normalize_url(self.start_url)
            queue.append((normalized_start, 1))
            
            # Seed landed URL if different from start URL (e.g. redirected to dashboard after login)
            if hasattr(self.request, "landed_url") and self.request.landed_url:
                normalized_landed = normalize_url(self.request.landed_url)
                if normalized_landed != normalized_start:
                    logger.info(f"Seeding post-login landed URL: {normalized_landed}")
                    queue.append((normalized_landed, 1))
            
            # Seed sitemap URLs
            for s_url in sitemap_urls_found:
                norm_s_url = normalize_url(s_url)
                if norm_s_url != normalized_start:
                    queue.append((norm_s_url, 1))
            
            # Traversal Loop
            while queue and len(self.pages_discovered) < self.max_pages:
                if self.strategy == "bfs":
                    current_url, depth = queue.popleft()
                else:
                    current_url, depth = queue.pop()
                    
                normalized_url = normalize_url(current_url)
                if normalized_url in self.visited_urls:
                    continue
                    
                self.visited_urls.add(normalized_url)
                
                # Check Domain Limits
                if not self.is_same_domain(normalized_url):
                    self.ignored_urls.add(normalized_url)
                    continue
                    
                # Check Robots.txt
                if robots_parser and not robots_parser.can_fetch(normalized_url):
                    self.ignored_urls.add(normalized_url)
                    continue
                    
                # Check Exclusions
                if self.is_excluded(normalized_url):
                    self.ignored_urls.add(normalized_url)
                    continue
                    
                # Check File Type Extensions
                if self.is_non_html(normalized_url):
                    self.ignored_urls.add(normalized_url)
                    continue
                
                # Rate Limiting
                now = time.time()
                elapsed = now - self.last_request_time
                if elapsed < self.default_delay:
                    await asyncio.sleep(self.default_delay - elapsed)
                
                self.last_request_time = time.time()
                
                # Fetch URL content
                try:
                    logger.info(f"Crawling URL: {normalized_url} at depth {depth}")
                    response = await client.get(normalized_url)
                    if response.status_code in (401, 403) and self.request.credential_config and not self._relogged:
                        logger.warning(f"Received status {response.status_code} for {normalized_url}. Attempting dynamic re-login...")
                        self._relogged = True
                        from app.services.login_service import login_service
                        from app.repository.auth_repo import auth_repo
                        import hashlib
                        import json
                        
                        success, login_cookies, login_headers, error_detail, landed_url = await login_service.perform_login(self.request.credential_config)
                        if success:
                            # Update client state
                            client.cookies.update(login_cookies)
                            client.headers.update(login_headers)
                            
                            # Update Redis cache
                            cred_str = f"{self.request.credential_config.auth_type}:{self.request.credential_config.login_url}:{self.request.credential_config.username}"
                            cred_hash = hashlib.sha256(cred_str.encode()).hexdigest()
                            cache_key = f"crawler:auth:{cred_hash}"
                            session_data = {
                                "cookies": login_cookies,
                                "headers": login_headers,
                                "landed_url": landed_url
                            }
                            auth_repo.save_session_state(cache_key, json.dumps(session_data))
                            
                            # Retry the request
                            logger.info(f"Retrying request to {normalized_url} after successful re-login.")
                            response = await client.get(normalized_url)

                    if response.status_code >= 400:
                        self.failed_urls[normalized_url] = f"Status Code: {response.status_code}"
                        continue
                        
                    # Follow redirects inside allowed domain
                    final_url = str(response.url)
                    normalized_final = normalize_url(final_url)
                    
                    if not self.is_same_domain(normalized_final):
                        self.ignored_urls.add(normalized_final)
                        continue
                        
                    self.pages_discovered[normalized_final] = depth
                    
                    # Verify Content-Type before parsing HTML body
                    content_type = response.headers.get("content-type", "").lower()
                    if "text/html" not in content_type:
                        continue
                        
                    # Parse pages to find new hyperlinks
                    if depth < self.max_depth:
                        soup = BeautifulSoup(response.text, "html.parser")
                        for a_tag in soup.find_all("a", href=True):
                            href = a_tag["href"].strip()
                            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                                continue
                                
                            # Join relative URL
                            resolved_url = urllib.parse.urljoin(normalized_final, href)
                            normalized_resolved = normalize_url(resolved_url)
                            
                            if normalized_resolved not in self.visited_urls:
                                queue.append((normalized_resolved, depth + 1))
                                
                except httpx.RequestError as exc:
                    self.failed_urls[normalized_url] = f"Network Request error: {str(exc)}"
                except Exception as exc:
                    self.failed_urls[normalized_url] = f"Internal Exception: {str(exc)}"
                    
        duration = time.time() - start_time
        return self._build_response(duration)

    async def crawl_with_playwright(self) -> CrawlResponse:
        start_time = time.time()
        from playwright.async_api import async_playwright
        from app.services.login_service import login_service
        
        # Determine robots.txt restrictions first (using a standard httpx client helper)
        robots_parser = None
        if self.request.respect_robots_txt:
            try:
                async with httpx.AsyncClient(timeout=5.0, headers={"User-Agent": DEFAULT_USER_AGENT}) as client:
                    robots_parser = await RobotsParser.fetch_and_parse(client, self.start_url)
                    self.sitemaps_found = robots_parser.sitemaps
                    if robots_parser.crawl_delay is not None and self.default_delay == 0.5:
                        self.default_delay = robots_parser.crawl_delay
            except Exception as e:
                logger.warning(f"Failed to fetch robots.txt for Playwright crawl: {e}")

        pw = None
        browser = None
        try:
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(headless=True)
            
            config = self.request.credential_config

            # For form auth, start with a clean context so the login page loads
            # without pre-existing auth headers/cookies. Pre-injecting a cached
            # Authorization: Bearer token causes the server to skip the login page
            # and redirect straight to the dashboard, making the form-fill steps
            # timeout looking for fields that don't exist.
            is_form_auth = bool(config) and config.auth_type == "form"

            context_args = {
                "viewport": {'width': 1280, 'height': 800},
                "user_agent": DEFAULT_USER_AGENT
            }
            if self.request.headers and not is_form_auth:
                context_args["extra_http_headers"] = self.request.headers

            context = await browser.new_context(**context_args)

            # Inject pre-existing cookies only for non-form auth types
            if self.request.cookies and not is_form_auth:
                parsed_url = urllib.parse.urlparse(self.start_url)
                domain = parsed_url.netloc
                pw_cookies = []
                for k, v in self.request.cookies.items():
                    pw_cookies.append({
                        "name": k,
                        "value": v,
                        "domain": domain,
                        "path": "/"
                    })
                await context.add_cookies(pw_cookies)

            page = await context.new_page()
            page.set_default_timeout(120000)
            
            # Perform login steps if config is form auth
            landed_url = self.start_url
            
            if config and config.auth_type == "form":
                logger.info("Performing Playwright form login for crawl...")
                success, cookies_ext, headers_ext, error_detail, landed = await login_service.perform_login_steps(
                    config, page, context
                )
                if not success:
                    logger.error(f"Playwright crawl login failed: {error_detail}")
                    await browser.close()
                    await pw.stop()
                    raise Exception(f"Login failed: {error_detail}")
                if landed:
                    landed_url = landed
                # Inject JWT/Bearer tokens extracted from localStorage into all subsequent page requests
                if headers_ext:
                    self.auth_headers = headers_ext
                    await context.set_extra_http_headers(headers_ext)
                # Capture storage state for propagation to the audit agent
                try:
                    self.storage_state = await context.storage_state()
                    logger.info("Captured Playwright storage state after form login.")
                except Exception as ss_err:
                    logger.warning(f"Failed to capture storage state: {ss_err}")
            elif config and config.auth_type == "cookie":
                # Direct cookie injection
                pw_cookies = []
                parsed_url = urllib.parse.urlparse(self.start_url)
                domain = parsed_url.netloc
                
                cookie_dict = {}
                if config.extra_fields:
                    cookie_dict.update(config.extra_fields)
                elif config.username and config.password:
                    cookie_dict[config.username] = config.password
                    
                for k, v in cookie_dict.items():
                    pw_cookies.append({
                        "name": k,
                        "value": v,
                        "domain": domain,
                        "path": "/"
                    })
                if pw_cookies:
                    await context.add_cookies(pw_cookies)
            elif config and config.auth_type == "bearer_token":
                # Token header injection
                token = config.password or config.username
                if token:
                    self.auth_headers = {"Authorization": f"Bearer {token}"}
                    await context.set_extra_http_headers(self.auth_headers)

            # Track dynamic collapsible parent menu items that do not change the URL when clicked (self-learning toggle scanner)
            expanded_toggle_texts = set()
            item_to_parent = {}

            async def ensure_toggle_expanded(toggle_text):
                if not toggle_text:
                    return
                grandparent = item_to_parent.get(toggle_text)
                if grandparent:
                    await ensure_toggle_expanded(grandparent)
                
                try:
                    is_expanded = await page.evaluate("""(text) => {
                        const targetSel = 'nav [role="button"], aside [role="button"], ' +
                            '.MuiDrawer-root [role="button"], .MuiList-root [role="button"], ' +
                            'nav button, aside button, [role="navigation"] [role="button"], ' +
                            'nav a, aside a, .MuiDrawer-root a';
                        const elts = document.querySelectorAll(targetSel);
                        for (const el of elts) {
                            const t = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                            if (t === text) {
                                const hasAriaExpanded = el.getAttribute('aria-expanded') === 'true' || 
                                                       el.classList.contains('Mui-expanded');
                                const parentExpanded = el.parentElement && (
                                    el.parentElement.getAttribute('aria-expanded') === 'true' ||
                                    el.parentElement.classList.contains('Mui-expanded')
                                );
                                return !!(hasAriaExpanded || parentExpanded);
                            }
                        }
                        return false;
                    }""", toggle_text)
                    
                    if not is_expanded:
                        logger.info(f"[Playwright Crawl] Ensuring parent toggle '{toggle_text}' is expanded...")
                        clicked = await page.evaluate("""(text) => {
                            const targetSel = 'nav [role="button"], aside [role="button"], ' +
                                '.MuiDrawer-root [role="button"], .MuiList-root [role="button"], ' +
                                'nav button, aside button, [role="navigation"] [role="button"], ' +
                                'nav a, aside a, .MuiDrawer-root a';
                            const elts = document.querySelectorAll(targetSel);
                            for (const el of elts) {
                                const t = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                                if (t === text) {
                                    el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                                    return true;
                                }
                            }
                            return false;
                        }""", toggle_text)
                        
                        if clicked:
                            await page.wait_for_timeout(800)
                        else:
                            locator = page.get_by_text(toggle_text, exact=True).first
                            if await locator.count() > 0:
                                await locator.click(timeout=3000)
                                await page.wait_for_timeout(800)
                except Exception as err:
                    logger.debug(f"[Playwright Crawl] Failed to expand toggle '{toggle_text}': {err}")

            async def restore_toggles():
                if not expanded_toggle_texts:
                    return
                logger.info(f"[Playwright Crawl] Restoring expanded menu toggles: {expanded_toggle_texts}")
                for toggle_text in list(expanded_toggle_texts):
                    await ensure_toggle_expanded(toggle_text)

            async def get_menu_items():
                return await page.evaluate("""() => {
                    const items = [];
                    const seenTexts = new Set();
                    const targetSel = 'nav [role="button"], aside [role="button"], ' +
                        '.MuiDrawer-root [role="button"], .MuiList-root [role="button"], ' +
                        '.MuiListItemButton-root, .MuiMenuItem-root, [role="menuitem"], ' +
                        'nav button, aside button, [role="navigation"] [role="button"], ' +
                        'nav a, aside a, .MuiDrawer-root a';
                    const elts = document.querySelectorAll(targetSel);
                    elts.forEach((el) => {
                        const text = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                        const lowerText = text.toLowerCase();
                        if (text && text.length > 1 && text.length < 60 && 
                            !lowerText.includes("log out") && !lowerText.includes("logout") && 
                            !lowerText.includes("sign out") && !lowerText.includes("signout") && 
                            !lowerText.includes("exit")) {
                            if (!seenTexts.has(text)) {
                                seenTexts.add(text);
                                items.push({ text: text });
                            }
                        }
                    });
                    return items;
                }""")

            queue = deque()
            
            # Seed start URL
            normalized_start = normalize_url(self.start_url)
            queue.append((normalized_start, 1))
            
            # Seed landed URL
            if landed_url:
                normalized_landed = normalize_url(landed_url)
                if normalized_landed != normalized_start:
                    logger.info(f"Seeding post-login landed URL: {normalized_landed}")
                    queue.append((normalized_landed, 1))
                    
            while queue and len(self.pages_discovered) < self.max_pages:
                if self.strategy == "bfs":
                    current_url, depth = queue.popleft()
                else:
                    current_url, depth = queue.pop()
                    
                normalized_url = normalize_url(current_url)
                if normalized_url in self.visited_urls:
                    continue
                    
                self.visited_urls.add(normalized_url)
                
                # Check domain
                if not self.is_same_domain(normalized_url):
                    self.ignored_urls.add(normalized_url)
                    continue
                    
                # Check robots
                if robots_parser and not robots_parser.can_fetch(normalized_url):
                    self.ignored_urls.add(normalized_url)
                    continue
                    
                # Check exclusions
                if self.is_excluded(normalized_url):
                    self.ignored_urls.add(normalized_url)
                    continue
                    
                # Check extension
                if self.is_non_html(normalized_url):
                    self.ignored_urls.add(normalized_url)
                    continue
                    
                # Delay
                now = time.time()
                elapsed = now - self.last_request_time
                if elapsed < self.default_delay:
                    await asyncio.sleep(self.default_delay - elapsed)
                self.last_request_time = time.time()
                
                try:
                    logger.info(f"[Playwright Crawl] Navigating to: {normalized_url} at depth {depth}")
                    # Try to navigate client-side first to avoid SPA full-page reload bugs
                    navigated_client_side = False
                    if normalize_url(page.url) != normalized_url:
                        # Only expand the specific parent toggle of the target menu item if needed
                        target_menu_text = self.url_to_menu_text.get(normalized_url)
                        if target_menu_text:
                            parent_toggle = item_to_parent.get(target_menu_text)
                            if parent_toggle:
                                await ensure_toggle_expanded(parent_toggle)
                        
                        # Attempt click-based client-side navigation
                        try:
                            clicked = await page.evaluate("""(args) => {
                                const targetUrl = args.targetUrl;
                                const targetMenuText = args.targetMenuText;
                                const targetSel = 'nav [role="button"], aside [role="button"], ' +
                                    '.MuiDrawer-root [role="button"], .MuiList-root [role="button"], ' +
                                    '.MuiListItemButton-root, .MuiMenuItem-root, [role="menuitem"], ' +
                                    'nav button, aside button, [role="navigation"] [role="button"], ' +
                                    'nav a, aside a, .MuiDrawer-root a, a[href]';
                                const elts = document.querySelectorAll(targetSel);
                                
                                // First try by menu text if available
                                if (targetMenuText) {
                                    for (const el of elts) {
                                        const t = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                                        if (t === targetMenuText) {
                                            el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                                            return true;
                                        }
                                    }
                                }
                                
                                // Second try by exact href
                                for (const el of elts) {
                                    if (el.href === targetUrl) {
                                        el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                                        return true;
                                    }
                                }
                                return false;
                            }""", {"targetUrl": normalized_url, "targetMenuText": target_menu_text})
                            
                            if clicked:
                                await page.wait_for_timeout(2000)
                                if normalize_url(page.url) == normalized_url:
                                    logger.info(f"[Playwright Crawl] Successfully navigated client-side to: {normalized_url}")
                                    navigated_client_side = True
                        except Exception as e:
                            logger.debug(f"[Playwright Crawl] Failed client-side navigation attempt: {e}")
                    
                    response = None
                    if not navigated_client_side and normalize_url(page.url) != normalized_url:
                        logger.info(f"[Playwright Crawl] Client-side navigation unavailable/failed. Falling back to page.goto for: {normalized_url}")
                        response = await page.goto(normalized_url, wait_until="domcontentloaded")

                    # Wait for React SPA to render and load completely
                    # Wait for any loaders or spinners to disappear
                    try:
                        await page.wait_for_selector("[class*='loader'], [class*='spinner'], [id*='loader'], [id*='spinner'], :has-text('Loading')", state="hidden", timeout=15000)
                    except Exception:
                        pass
                    # Wait for key elements to be visible
                    try:
                        await page.wait_for_selector("li, nav a, aside a, a, p, h1, h2, h3, main, #root", state="visible", timeout=5000)
                        await page.wait_for_timeout(1000)
                    except Exception:
                        await page.wait_for_timeout(2000)

                    current_items = await get_menu_items()
                    if any(m["text"] not in self.clicked_sidebar_items for m in current_items):
                        await restore_toggles()

                    # Mid-crawl login detection: if this page is showing a login form, authenticate and continue
                    if config and config.auth_type == "form":
                        has_login_form = await page.evaluate(
                            "() => !!document.querySelector('input[type=password]')"
                        )
                        if has_login_form and not self._relogged:
                            logger.info(f"[Playwright Crawl] Login form detected at {page.url}. Logging in with stored credentials...")
                            self._relogged = True
                            ok, _, headers_ext, err, landed = await login_service.perform_login_steps(config, page, context)
                            if ok:
                                if headers_ext:
                                    await context.set_extra_http_headers(headers_ext)
                                if landed:
                                    norm_landed = normalize_url(landed)
                                    self.visited_urls.discard(norm_landed)
                                    queue.append((norm_landed, depth))
                                # Re-queue the page we were trying to reach, now authenticated
                                self.visited_urls.discard(normalized_url)
                                queue.append((normalized_url, depth))
                                continue
                            else:
                                logger.error(f"Mid-crawl login failed: {err}")

                    status = response.status if response else 200
                    if status >= 400:
                        self.failed_urls[normalized_url] = f"Status Code: {status}"
                        continue
                        
                    current_page_url = page.url
                    normalized_current = normalize_url(current_page_url)

                    if not self.is_same_domain(normalized_current):
                        self.ignored_urls.add(normalized_current)
                        continue

                    # If a redirect happened, mark the final URL as visited so the
                    # queue doesn't re-process it as a separate entry (e.g. root → /dashboard).
                    if normalized_current != normalized_url:
                        self.visited_urls.add(normalized_current)

                    self.pages_discovered[normalized_current] = depth
                    
                    # Extract all links via URL-depth discovery (anchor hrefs)
                    if depth < self.max_depth:
                        links = await page.evaluate("""() => {
                            const anchors = Array.from(document.querySelectorAll('a[href]'));
                            return anchors.map(a => a.href);
                        }""")
                        for href in links:
                            href = href.strip()
                            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                                continue
                            normalized_resolved = normalize_url(href)
                            if normalized_resolved not in self.visited_urls:
                                queue.append((normalized_resolved, depth + 1))

                    # Dynamic sidebar menu click route discovery (for SPAs)
                    # This runs regardless of depth — sidebar items are sibling-level
                    # navigation, not child pages, and are the primary discovery
                    # mechanism for React SPAs where routes use onClick + navigate().
                    try:
                        # get_menu_items is defined above

                        # Pre-extract all hrefs from sidebar/nav before click loop
                        # This catches React Router <Link> components that render as <a>
                        try:
                            sidebar_hrefs = await page.evaluate("""() => {
                                const sel = 'nav a[href], aside a[href], .MuiDrawer-root a[href], ' +
                                    '[role="navigation"] a[href], .MuiList-root a[href]';
                                const anchors = document.querySelectorAll(sel);
                                const results = [];
                                anchors.forEach(a => {
                                    const href = a.href;
                                    const text = (a.textContent || '').replace(/\\s+/g, ' ').trim();
                                    if (href && !href.startsWith('javascript:') && !href.startsWith('mailto:') && !href.startsWith('#')) {
                                        results.push({ href: href, text: text });
                                    }
                                });
                                return results;
                            }""")
                            for item in sidebar_hrefs:
                                href = item.get('href', '').strip()
                                text = item.get('text', '')
                                if not href:
                                    continue
                                norm_href = normalize_url(href)
                                if self.is_same_domain(norm_href) and not self.is_excluded(norm_href) and not self.is_non_html(norm_href):
                                    if norm_href not in self.visited_urls and norm_href not in self.pages_discovered:
                                        logger.info(f"[Playwright Crawl] Pre-extracted sidebar href: {norm_href} ('{text}')")
                                        if text:
                                            self.url_to_menu_text[norm_href] = text
                                        queue.append((norm_href, depth))
                        except Exception as href_err:
                            logger.debug(f"[Playwright Crawl] Sidebar href pre-extraction failed: {href_err}")

                        clicked_texts = set()
                        menu_items = [{"text": m["text"], "parent_toggle": None} for m in await get_menu_items()]
                        logger.info(f"[Playwright Crawl] Sidebar menu items found: {[m['text'] for m in menu_items]}")
                        
                        idx = 0
                        while idx < len(menu_items):
                            item = menu_items[idx]
                            idx += 1
                            item_text = item['text']
                            parent_toggle = item.get('parent_toggle')
                            if item_text in self.clicked_sidebar_items:
                                continue
                            if item_text in clicked_texts:
                                continue
                            clicked_texts.add(item_text)
                            
                            if parent_toggle:
                                await ensure_toggle_expanded(parent_toggle)
                            
                            logger.info(f"[Playwright Crawl] Clicking menu item '{item_text}' to discover route...")
                            eval_res = await page.evaluate("""(targetText) => {
                                const targetSel = 'nav [role="button"], aside [role="button"], ' +
                                    '.MuiDrawer-root [role="button"], .MuiList-root [role="button"], ' +
                                    '.MuiListItemButton-root, .MuiMenuItem-root, [role="menuitem"], ' +
                                    'nav button, aside button, [role="navigation"] [role="button"], ' +
                                    'nav a, aside a, .MuiDrawer-root a';
                                const elts = document.querySelectorAll(targetSel);
                                for (const el of elts) {
                                    const t = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                                    if (t === targetText) {
                                        const href = el.getAttribute('href') || (el.closest('a') ? el.closest('a').getAttribute('href') : null);
                                        let isCurrentLink = false;
                                        if (href && !href.startsWith('#') && !href.startsWith('javascript:')) {
                                            try {
                                                const absoluteHref = new URL(href, window.location.href).href;
                                                const normCurrent = window.location.href.split('#')[0].split('?')[0].replace(/\/$/, '');
                                                const normAbsolute = absoluteHref.split('#')[0].split('?')[0].replace(/\/$/, '');
                                                if (normCurrent === normAbsolute) {
                                                    isCurrentLink = true;
                                                }
                                            } catch (e) {}
                                        }
                                        el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                                        return { clicked: true, isCurrentLink: isCurrentLink };
                                    }
                                }
                                return { clicked: false, isCurrentLink: false };
                            }""", item_text)
                            
                            clicked = eval_res.get("clicked", False)
                            is_current_link = eval_res.get("isCurrentLink", False)
                            
                            # If evaluate couldn't find the element, it may be because a
                            # parent toggle collapsed. Restore toggles, wait, then retry.
                            if not clicked:
                                await restore_toggles()
                                await page.wait_for_timeout(1500)
                                
                                # Retry the evaluate after toggles are restored
                                try:
                                    eval_res2 = await page.evaluate("""(targetText) => {
                                        const targetSel = 'nav [role="button"], aside [role="button"], ' +
                                            '.MuiDrawer-root [role="button"], .MuiList-root [role="button"], ' +
                                            '.MuiListItemButton-root, .MuiMenuItem-root, [role="menuitem"], ' +
                                            'nav button, aside button, [role="navigation"] [role="button"], ' +
                                            'nav a, aside a, .MuiDrawer-root a';
                                        const elts = document.querySelectorAll(targetSel);
                                        for (const el of elts) {
                                            const t = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                                            if (t === targetText) {
                                                el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
                                                return { clicked: true };
                                            }
                                        }
                                        return { clicked: false };
                                    }""", item_text)
                                    clicked = eval_res2.get("clicked", False)
                                    if clicked:
                                        logger.info(f"[Playwright Crawl] Clicked '{item_text}' after restoring toggles")
                                except Exception:
                                    pass
                            
                            # Final fallback: Playwright's locator-based click
                            if not clicked:
                                try:
                                    locator = page.get_by_text(item_text, exact=True).first
                                    if await locator.count() > 0:
                                        await locator.click(timeout=3000)
                                        clicked = True
                                        logger.info(f"[Playwright Crawl] Clicked '{item_text}' via Playwright locator fallback")
                                except Exception as loc_err:
                                    logger.debug(f"[Playwright Crawl] Locator fallback also failed for '{item_text}': {loc_err}")
                            
                            if not clicked:
                                logger.debug(f"[Playwright Crawl] Could not click '{item_text}' - element not found in DOM")
                                continue
                                
                            self.clicked_sidebar_items.add(item_text)
                            await page.wait_for_timeout(1500) # Wait for route transition
                            
                            new_url = page.url
                            norm_new = normalize_url(new_url)
                            
                            if norm_new != normalized_current:
                                if self.is_same_domain(norm_new) and not self.is_excluded(norm_new):
                                    logger.info(f"[Playwright Crawl] Discovered route: {norm_new} from '{item_text}'")
                                    self.url_to_menu_text[norm_new] = item_text
                                    # Immediately register in pages_discovered so it's counted
                                    # even if later queue processing has navigation issues
                                    if norm_new not in self.pages_discovered:
                                        self.pages_discovered[norm_new] = depth
                                if norm_new not in self.visited_urls:
                                    queue.append((norm_new, depth))
                                    
                                # Navigate back to original page by direct goto (more reliable than go_back for SPAs)
                                try:
                                    await page.goto(normalized_current, wait_until="domcontentloaded")
                                except Exception as nav_err:
                                    logger.debug(f"[Playwright Crawl] Back-navigation failed: {nav_err}")
                                
                                # Wait for page to be ready after navigating back
                                try:
                                    await page.wait_for_selector("[class*='loader'], [class*='spinner'], [id*='loader'], [id*='spinner'], :has-text('Loading')", state="hidden", timeout=10000)
                                except Exception:
                                    pass
                                try:
                                    await page.wait_for_selector("li, nav a, aside a", state="visible", timeout=8000)
                                except Exception:
                                    pass
                                await page.wait_for_timeout(1500)
                                await restore_toggles()
                            else:
                                # URL did not change -> it might have expanded a sub-menu!
                                if not is_current_link and item_text.lower() not in ("home", "dashboard"):
                                    if item_text not in expanded_toggle_texts:
                                        logger.info(f"[Playwright Crawl] Menu toggle detected: '{item_text}'")
                                        expanded_toggle_texts.add(item_text)
                                        # Wait for sub-menu animation to complete after toggle expansion
                                        await page.wait_for_timeout(1500)
                                else:
                                    logger.info(f"[Playwright Crawl] Clicked link pointing to current page or home/dashboard: '{item_text}' (not treated as toggle)")
                                
                                # Scan for new sub-menu items that appeared!
                                sub_items = await get_menu_items()
                                new_sub_count = 0
                                for sub in sub_items:
                                    sub_text = sub['text']
                                    if sub_text not in clicked_texts and not any(m['text'] == sub_text for m in menu_items):
                                        menu_items.append({"text": sub_text, "parent_toggle": item_text})
                                        item_to_parent[sub_text] = item_text
                                        new_sub_count += 1
                                if new_sub_count > 0:
                                    logger.info(f"[Playwright Crawl] Found {new_sub_count} new sub-menu items after expanding '{item_text}'")
                                        
                    except Exception as click_err:
                        logger.error(f"[Playwright Crawl] Error clicking menu items on {normalized_current}: {click_err}")

                except Exception as exc:
                    logger.error(f"[Playwright Crawl] Failed on {normalized_url}: {exc}")
                    self.failed_urls[normalized_url] = str(exc)
                    
            await browser.close()
            await pw.stop()
            
        except Exception as outer_exc:
            logger.exception("Error in Playwright crawl flow")
            try:
                if browser:
                    await browser.close()
                if pw:
                    await pw.stop()
            except Exception:
                pass
            raise outer_exc

        # Ensure the start URL and the login URL are in discovered pages
        norm_start = normalize_url(self.start_url)
        if norm_start not in self.pages_discovered:
            self.pages_discovered[norm_start] = 0
        if self.request.credential_config and self.request.credential_config.login_url:
            norm_login = normalize_url(self.request.credential_config.login_url)
            if norm_login not in self.pages_discovered:
                self.pages_discovered[norm_login] = 0

        duration = time.time() - start_time
        return self._build_response(duration)
