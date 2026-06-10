import pytest
from app.core.crawler import normalize_url, RobotsParser, WebCrawler
from app.schemas.crawl import CrawlRequest

def test_normalize_url():
    """
    Validates URL normalization including schemes, port scrubbing, trailing slashes, 
    and parameter sorting.
    """
    assert normalize_url("HTTP://Example.Com/") == "http://example.com"
    assert normalize_url("https://example.com:443/about/") == "https://example.com/about"
    assert normalize_url("http://example.com/about?b=2&a=1#section") == "http://example.com/about?a=1&b=2"
    assert normalize_url("https://example.com/path/") == "https://example.com/path"

def test_robots_parser_can_fetch():
    """
    Validates Robots.txt path rule compliance.
    """
    disallows = ["/admin", "/private*", "/secret?*"]
    parser = RobotsParser(disallows=disallows)
    
    assert parser.can_fetch("http://example.com/about") is True
    assert parser.can_fetch("http://example.com/admin") is False
    assert parser.can_fetch("http://example.com/admin/settings") is False
    assert parser.can_fetch("http://example.com/private/data") is False
    assert parser.can_fetch("http://example.com/secret?key=1") is False

def test_crawler_exclusions():
    """
    Validates custom crawl exclusion list checking.
    """
    req = CrawlRequest(
        url="https://example.com",
        exclude_patterns=["/admin", "*/login*"]
    )
    crawler = WebCrawler(req)
    
    assert crawler.is_excluded("https://example.com/admin") is True
    assert crawler.is_excluded("https://example.com/about/login/page") is True
    assert crawler.is_excluded("https://example.com/about") is False

def test_crawler_non_html():
    """
    Validates screen-out of media files and assets.
    """
    req = CrawlRequest(url="https://example.com")
    crawler = WebCrawler(req)
    
    assert crawler.is_non_html("https://example.com/logo.png") is True
    assert crawler.is_non_html("https://example.com/document.pdf") is True
    assert crawler.is_non_html("https://example.com/script.js") is True
    assert crawler.is_non_html("https://example.com/about") is False
