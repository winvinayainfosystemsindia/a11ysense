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
        )

    async def crawl(self) -> CrawlResponse:
        if self.request.credential_config:
            return await self.crawl_with_playwright()
            
        start_time = time.time()
        
        headers = {
            "User-Agent": "A11ySenseCrawler/1.0",
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
                async with httpx.AsyncClient(timeout=5.0) as client:
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
            is_form_auth = config.auth_type == "form"

            context_args = {
                "viewport": {'width': 1280, 'height': 800},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
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
            page.set_default_timeout(60000)
            
            # Perform login steps if config is form auth
            landed_url = self.start_url
            
            if config.auth_type == "form":
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
            elif config.auth_type == "cookie":
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
            elif config.auth_type == "bearer_token":
                # Token header injection
                token = config.password or config.username
                if token:
                    self.auth_headers = {"Authorization": f"Bearer {token}"}
                    await context.set_extra_http_headers(self.auth_headers)

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
                    response = await page.goto(normalized_url, wait_until="domcontentloaded")

                    # Wait for React SPA to render navigation content.
                    # Many SPAs have two-stage loading: first API call (auth check) fires
                    # networkidle early, then a second wave (dashboard/page data) renders
                    # the actual nav items. We wait for networkidle then watch for li/nav
                    # elements to appear, which is the reliable signal that content is ready.
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass
                    try:
                        await page.wait_for_selector("li, nav a, aside a", state="visible", timeout=8000)
                        # React fills text content progressively; give it a moment to finish
                        await page.wait_for_timeout(3000)
                    except Exception:
                        await page.wait_for_timeout(5000)

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
                    
                    if depth < self.max_depth:
                        # Extract all links via URL-depth discovery (anchor hrefs)
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
                                
                        # NOTE: Click-based SPA route discovery has been removed.
                        # URL-depth discovery via anchor href extraction is more reliable
                        # and deterministic. Click-based discovery was unreliable for
                        # collapsed menus, dynamic loading, and non-standard SPA routing.
                                
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
