from pydantic import BaseModel, Field
from typing import List, Optional, Dict

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

class CrawlResponse(BaseModel):
    start_url: str
    pages_discovered: List[str] = Field(default_factory=list, description="Successfully crawled URLs")
    ignored_urls: List[str] = Field(default_factory=list, description="URLs ignored (e.g. domain mismatch, exclusions, robots.txt)")
    failed_urls: Dict[str, str] = Field(default_factory=dict, description="Failed URLs mapped to error details")
    sitemaps_found: List[str] = Field(default_factory=list, description="Discovered sitemaps")
    duration_seconds: float
