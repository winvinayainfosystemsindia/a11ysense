from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from common.schemas.audit import PageCredentialConfig

class PageDiscovery(BaseModel):
    """Represents a single discovered page with its crawl depth and auth status."""
    url: str
    depth: int = 1
    is_authenticated: bool = False

class CrawlRequest(BaseModel):
    url: str = Field(..., description="The absolute starting URL for the crawl")
    depth: int = Field(default=1, ge=1, le=5, description="Traversal depth, from 1 to 5")
    max_pages: int = Field(default=100, ge=1, le=500, description="Max limit of pages to crawl")
    exclude_patterns: List[str] = Field(default_factory=list, description="Wildcard or substring patterns to exclude")
    respect_robots_txt: bool = Field(default=True, description="Whether to fetch and respect robots.txt")
    crawl_delay: float = Field(default=0.5, ge=0.0, description="Default delay in seconds between requests")
    cookies: Dict[str, str] = Field(default_factory=dict, description="Authentication cookies to inject")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom request headers to inject")
    strategy: str = Field(default="bfs", pattern="^(bfs|dfs)$", description="Traversal strategy: bfs or dfs")
    credential_config: Optional[PageCredentialConfig] = None
    landed_url: Optional[str] = None

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
