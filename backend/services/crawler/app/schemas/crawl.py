from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from common.schemas.audit import PageCredentialConfig

# Depth no longer truncates discovery for the discover-then-select flow; only
# max_pages bounds the crawl. Kept as a real (high) value rather than a magic
# "infinite" flag so existing depth-comparison logic in WebCrawler needs no changes.
UNLIMITED_DEPTH = 999

class PageDiscovery(BaseModel):
    """Represents a single discovered page with its crawl depth and auth status."""
    url: str
    depth: int = 1
    is_authenticated: bool = False

class CrawlRequest(BaseModel):
    url: str = Field(..., description="The absolute starting URL for the crawl")
    depth: int = Field(default=1, ge=1, le=999, description="Traversal depth")
    max_pages: int = Field(default=300, ge=1, le=1000, description="Max limit of pages to crawl")
    exclude_patterns: List[str] = Field(default_factory=list, description="Wildcard or substring patterns to exclude")
    respect_robots_txt: bool = Field(default=True, description="Whether to fetch and respect robots.txt")
    crawl_delay: float = Field(default=0.5, ge=0.0, description="Default delay in seconds between requests")
    cookies: Dict[str, str] = Field(default_factory=dict, description="Authentication cookies to inject")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom request headers to inject")
    strategy: str = Field(default="bfs", pattern="^(bfs|dfs)$", description="Traversal strategy: bfs or dfs")
    credential_config: Optional[PageCredentialConfig] = None
    landed_url: Optional[str] = None
    crawl_mode: str = Field(default="single", pattern="^(single|combined)$", description="single: one crawl pass; combined: merge an unauthenticated pass with an authenticated pass")

class CrawlResponse(BaseModel):
    start_url: str
    pages_discovered: List[str] = Field(default_factory=list, description="Flat list of discovered URLs (backward compat)")
    pages_with_depth: List[PageDiscovery] = Field(default_factory=list, description="Discovered pages with depth and auth metadata")
    pages_depth_map: Dict[str, int] = Field(default_factory=dict, description="URL to depth mapping")
    ignored_urls: List[str] = Field(default_factory=list, description="URLs ignored (e.g. domain mismatch, exclusions, robots.txt)")
    failed_urls: Dict[str, str] = Field(default_factory=dict, description="Failed URLs mapped to error details")
    sitemaps_found: List[str] = Field(default_factory=list, description="Discovered sitemaps")
    duration_seconds: float
    storage_state: Optional[Dict[str, Any]] = Field(default=None, description="Playwright storage state (cookies + localStorage) for auth propagation")
    auth_headers: Dict[str, str] = Field(default_factory=dict, description="Auth headers (e.g. Bearer token) extracted during login")
    url_to_menu_text: Dict[str, str] = Field(default_factory=dict, description="Discovered routes mapped to their sidebar menu text")
    unauth_pages_discovered: List[str] = Field(default_factory=list, description="Pages found without credentials (combined mode breakdown)")
    auth_pages_discovered: List[str] = Field(default_factory=list, description="Pages found while authenticated (combined mode breakdown)")

