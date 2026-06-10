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

from app.schemas.crawl import CrawlRequest, CrawlResponse

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
        self.pages_discovered: Set[str] = set()
        self.ignored_urls: Set[str] = set()
        self.failed_urls: Dict[str, str] = {}
        self.sitemaps_found: List[str] = []
        
        self.default_delay = request.crawl_delay
        self.last_request_time = 0.0
        self.exclude_patterns = request.exclude_patterns

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

    async def crawl(self) -> CrawlResponse:
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
                    
                    if response.status_code >= 400:
                        self.failed_urls[normalized_url] = f"Status Code: {response.status_code}"
                        continue
                        
                    # Follow redirects inside allowed domain
                    final_url = str(response.url)
                    normalized_final = normalize_url(final_url)
                    
                    if not self.is_same_domain(normalized_final):
                        self.ignored_urls.add(normalized_final)
                        continue
                        
                    self.pages_discovered.add(normalized_final)
                    
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
        return CrawlResponse(
            start_url=self.start_url,
            pages_discovered=list(self.pages_discovered),
            ignored_urls=list(self.ignored_urls),
            failed_urls=self.failed_urls,
            sitemaps_found=self.sitemaps_found,
            duration_seconds=round(duration, 2)
        )
