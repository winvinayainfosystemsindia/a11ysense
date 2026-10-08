"""
A11ySense AI — Audit Estimation API.
Crawl, inspect element complexity, and compute costs, manual efforts, and final quotes with 30% profit margin.
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from backend.app.core.audit.browser_manager import browser_manager
from backend.app.core.skills.implementations.browser import browser_skill
from backend.app.core.estimation.analyzer import analyze_page_complexity
from backend.app.core.estimation.calculator import (
    calculate_total_estimate,
    DEFAULT_HOURLY_RATE,
    DEFAULT_PLATFORM_FEE_PER_PAGE,
    DEFAULT_PROFIT_MARGIN_PCT
)

logger = logging.getLogger("a11ysense.api.estimation")
router = APIRouter(prefix="/api/estimation", tags=["Estimation"])


class EstimationRequest(BaseModel):
    url: Optional[str] = None
    urls: Optional[List[str]] = None
    depth: int = Field(default=1, ge=1, le=3)
    max_pages: int = Field(default=10, ge=1, le=50)
    hourly_rate: float = Field(default=DEFAULT_HOURLY_RATE, ge=0.0)
    platform_fee: float = Field(default=DEFAULT_PLATFORM_FEE_PER_PAGE, ge=0.0)
    profit_margin_pct: float = Field(default=DEFAULT_PROFIT_MARGIN_PCT, ge=0.0)


class DiscoverRequest(BaseModel):
    url: str
    depth: int = Field(default=1, ge=1, le=3)
    max_pages: int = Field(default=30, ge=1, le=100)


class RecalculateRequest(BaseModel):
    pages: List[Dict[str, Any]]
    hourly_rate: float = Field(default=DEFAULT_HOURLY_RATE, ge=0.0)
    platform_fee: float = Field(default=DEFAULT_PLATFORM_FEE_PER_PAGE, ge=0.0)
    profit_margin_pct: float = Field(default=DEFAULT_PROFIT_MARGIN_PCT, ge=0.0)


def _normalize_discovered_link(href: str, base_netloc: str) -> Optional[str]:
    from urllib.parse import urlparse
    clean = href.split('#')[0].split('?')[0].rstrip('/')
    if not clean:
        return None
    parsed = urlparse(clean)
    if parsed.scheme not in ('http', 'https'):
        return None
    if parsed.netloc.lower() != base_netloc:
        return None
    for ext in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.pdf', '.zip', '.mp4', '.css', '.js', '.woff'):
        if clean.lower().endswith(ext):
            return None
    return clean


async def _async_discover_urls(base_url: str, depth: int = 1, max_pages: int = 30) -> List[Dict[str, Any]]:
    from playwright.async_api import async_playwright
    import asyncio
    from urllib.parse import urlparse

    target_url = base_url.strip()
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    parsed_base = urlparse(target_url)
    base_netloc = parsed_base.netloc.lower()

    discovered = {}
    clean_root = target_url.rstrip('/')
    discovered[clean_root] = "/"
    queue = [(clean_root, 0)]

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            bypass_csp=True,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        page.set_default_timeout(30000)

        while queue and len(discovered) < max_pages:
            current_url, current_depth = queue.pop(0)
            try:
                await page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(1.0)
                hrefs = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('a[href]'))
                        .map(a => a.href)
                        .filter(href => href && (href.startsWith('http') || href.startsWith('/')));
                }''')

                for h in hrefs:
                    if h.startswith('/'):
                        h = f"{parsed_base.scheme}://{parsed_base.netloc}{h}"
                    norm = _normalize_discovered_link(h, base_netloc)
                    if norm and norm not in discovered:
                        path = urlparse(norm).path or "/"
                        discovered[norm] = path
                        if current_depth + 1 < depth and len(discovered) < max_pages:
                            queue.append((norm, current_depth + 1))
                        if len(discovered) >= max_pages:
                            break
            except Exception as e:
                logger.warning(f"Error exploring {current_url}: {e}")

        await browser.close()

    result = []
    for u, p in discovered.items():
        result.append({"url": u, "path": p})
    return result


def _discover_urls_worker(base_url: str, depth: int, max_pages: int) -> List[Dict[str, Any]]:
    import sys, asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_async_discover_urls(base_url, depth, max_pages))
        finally:
            loop.close()
    else:
        return asyncio.run(_async_discover_urls(base_url, depth, max_pages))


@router.post("/discover")
async def discover_website_urls(request: DiscoverRequest):
    """
    Fast discovery of internal website URLs belonging to the base domain.
    Returns list of discovered URLs so the user can select specific pages for audit estimation.
    """
    import asyncio
    base_url = request.url.strip()
    if not base_url.startswith(("http://", "https://")):
        base_url = "https://" + base_url

    try:
        discovered = await asyncio.to_thread(_discover_urls_worker, base_url, request.depth, request.max_pages)
    except Exception as e:
        logger.error(f"URL discovery failed for {base_url}: {e}")
        discovered = [{"url": base_url, "path": "/"}]

    return {
        "base_url": base_url,
        "total_found": len(discovered),
        "urls": discovered
    }


async def _async_inspect_pages(urls: List[str]) -> List[Dict[str, Any]]:
    analyzed = []
    from playwright.async_api import async_playwright
    import asyncio

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            bypass_csp=True,
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        )

        for page_url in urls:
            page = await context.new_page()
            page.set_default_timeout(45000)
            try:
                logger.info(f"Navigating to {page_url} for complexity inspection")
                await page.goto(page_url, wait_until="domcontentloaded", timeout=45000)
                try:
                    await page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
                await asyncio.sleep(2.0)
                page_analysis = await analyze_page_complexity(page, page_url)
                analyzed.append(page_analysis)
            except Exception as page_err:
                logger.warning(f"Error inspecting {page_url}: {page_err}")
                analyzed.append({
                    "url": page_url,
                    "title": "Page (Fallback)",
                    "complexity": "medium",
                    "summary_rationale": "Automated inspection encountered barriers; estimated based on standard interaction.",
                    "triggers": ["Standard interactive controls estimated."],
                    "counts": {
                        "links": 25, "buttons": 4, "headings": 3, "paragraphs": 8,
                        "lists": 2, "images": 4, "forms": 1, "inputs": 2,
                        "tables": 0, "media": 0, "total_elements": 100
                    },
                    "status": "fallback",
                    "error": str(page_err)
                })
            finally:
                await page.close()

        await browser.close()
    return analyzed


def _inspect_pages_in_proactor_worker(urls: List[str]) -> List[Dict[str, Any]]:
    import sys
    import asyncio

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_async_inspect_pages(urls))
        finally:
            loop.close()
    else:
        return asyncio.run(_async_inspect_pages(urls))


@router.post("/analyze")
async def analyze_and_estimate(request: EstimationRequest):
    """
    Crawls URL, inspects DOM complexity per page, and computes effort, costs, and quotes.
    """
    import asyncio
    discovered_urls = []
    if request.urls and len(request.urls) > 0:
        for u in request.urls:
            raw = str(u).strip()
            if raw:
                if not raw.startswith(("http://", "https://")):
                    raw = "https://" + raw
                if raw not in discovered_urls:
                    discovered_urls.append(raw)
        logger.info(f"Direct/Selected URLs estimation requested for {len(discovered_urls)} page(s).")
    elif request.url:
        target_url = request.url.strip()
        if not target_url.startswith(("http://", "https://")):
            target_url = "https://" + target_url

        logger.info(f"Starting estimation analysis for: {target_url} (depth={request.depth})")
        discovered_urls = [target_url]
        if request.depth > 1:
            try:
                discovered_items = await asyncio.to_thread(_discover_urls_worker, target_url, request.depth, request.max_pages)
                discovered_urls = [d["url"] for d in discovered_items][:request.max_pages]
            except Exception as e:
                logger.warning(f"URL discovery fallback to root URL: {e}")
                discovered_urls = [target_url]

    if not discovered_urls:
        raise HTTPException(status_code=400, detail="Please enter or select at least one valid URL to estimate.")

    # 2. Inspect pages and analyze complexity in worker thread
    try:
        analyzed_pages = await asyncio.to_thread(_inspect_pages_in_proactor_worker, discovered_urls)
    except Exception as browser_err:
        logger.exception(f"Playwright browser initialization failed: {repr(browser_err)}")
        err_msg = f"{type(browser_err).__name__}: {str(browser_err) or repr(browser_err)}"
        analyzed_pages = []
        for page_url in discovered_urls:
            analyzed_pages.append({
                "url": page_url,
                "title": "Page (Unreachable)",
                "complexity": "medium",
                "summary_rationale": f"Browser engine could not initialize ({err_msg[:60]}); estimated based on standard interaction.",
                "triggers": ["Standard interactive controls estimated."],
                "counts": {
                    "links": 25, "buttons": 4, "headings": 3, "paragraphs": 8,
                    "lists": 2, "images": 4, "forms": 1, "inputs": 2,
                    "tables": 0, "media": 0, "total_elements": 100
                },
                "status": "error",
                "error": err_msg
            })

    # 3. Calculate financial and effort breakdown
    result = calculate_total_estimate(
        analyzed_pages,
        hourly_rate=request.hourly_rate,
        platform_fee_per_page=request.platform_fee,
        profit_margin_pct=request.profit_margin_pct
    )

    return result


@router.post("/recalculate")
async def recalculate_estimate(request: RecalculateRequest):
    """
    Recalculates summary and page line-items with updated hourly rates, platform fees, or margins.
    """
    result = calculate_total_estimate(
        request.pages,
        hourly_rate=request.hourly_rate,
        platform_fee_per_page=request.platform_fee,
        profit_margin_pct=request.profit_margin_pct
    )
    return result


class ExportQuotationRequest(BaseModel):
    summary: Dict[str, Any]
    pages: List[Dict[str, Any]]


@router.post("/export/excel")
async def export_quotation_excel(request: ExportQuotationRequest):
    """
    Generates and returns an executive 3-sheet commercial Excel Quotation report (.xlsx).
    """
    from fastapi.responses import Response
    from datetime import datetime
    from backend.app.core.reporting.quotation_generator import generate_quotation_excel

    payload = {"summary": request.summary, "pages": request.pages}
    excel_stream = generate_quotation_excel(payload)

    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"A11ySense_Quotation_{date_str}.xlsx"

    return Response(
        content=excel_stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/export/pdf")
async def export_quotation_pdf(request: ExportQuotationRequest):
    """
    Generates and returns an executive formal PDF Quotation Proposal document (.pdf).
    """
    from fastapi.responses import Response
    from datetime import datetime
    from backend.app.core.reporting.quotation_generator import generate_quotation_pdf

    payload = {"summary": request.summary, "pages": request.pages}
    pdf_stream = generate_quotation_pdf(payload)

    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"A11ySense_Quotation_{date_str}.pdf"

    return Response(
        content=pdf_stream.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

