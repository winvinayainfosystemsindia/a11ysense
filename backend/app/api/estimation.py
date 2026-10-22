"""
A11ySense AI — Audit Estimation API.
Crawl, inspect element complexity, and compute costs, manual efforts, and final quotes with 30% profit margin.
Supports persistent database storage, retrieval, and detail viewing.
"""
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from common.database.connection import get_db
from backend.app.core.audit.browser_manager import browser_manager
from backend.app.core.skills.implementations.browser import browser_skill
from backend.app.core.estimation.analyzer import analyze_page_complexity
from backend.app.core.estimation.calculator import (
    calculate_total_estimate,
    DEFAULT_HOURLY_RATE,
    DEFAULT_PLATFORM_FEE_PER_PAGE,
    DEFAULT_PROFIT_MARGIN_PCT
)
from backend.app.repository.estimation_repo import estimation_repo

logger = logging.getLogger("a11ysense.api.estimation")
router = APIRouter(prefix="/api/estimation", tags=["Estimation"])


class EstimationRequest(BaseModel):
    url: Optional[str] = None
    urls: Optional[List[str]] = None
    depth: int = Field(default=1, ge=1, le=5)
    max_pages: Optional[int] = Field(default=None, ge=1)
    hourly_rate: float = Field(default=DEFAULT_HOURLY_RATE, ge=0.0)
    platform_fee: float = Field(default=DEFAULT_PLATFORM_FEE_PER_PAGE, ge=0.0)
    profit_margin_pct: float = Field(default=DEFAULT_PROFIT_MARGIN_PCT, ge=0.0)
    title: Optional[str] = "Website Audit Estimation"
    base_url: Optional[str] = None
    mode: Optional[str] = "discover"
    save_to_db: bool = True
    org_id: Optional[str] = None


class DiscoverRequest(BaseModel):
    url: str
    depth: int = Field(default=1, ge=1, le=5)
    max_pages: Optional[int] = Field(default=None, ge=1)


class RecalculateRequest(BaseModel):
    pages: List[Dict[str, Any]]
    hourly_rate: float = Field(default=DEFAULT_HOURLY_RATE, ge=0.0)
    platform_fee: float = Field(default=DEFAULT_PLATFORM_FEE_PER_PAGE, ge=0.0)
    profit_margin_pct: float = Field(default=DEFAULT_PROFIT_MARGIN_PCT, ge=0.0)


class SaveEstimateRequest(BaseModel):
    title: str = "Website Audit Estimation"
    base_url: str
    mode: str = "discover"
    hourly_rate: float = DEFAULT_HOURLY_RATE
    platform_fee: float = DEFAULT_PLATFORM_FEE_PER_PAGE
    profit_margin_pct: float = DEFAULT_PROFIT_MARGIN_PCT
    pages: List[Dict[str, Any]]
    summary: Dict[str, Any]
    org_id: Optional[str] = None


class UpdateEstimateRequest(BaseModel):
    title: Optional[str] = None
    hourly_rate: Optional[float] = None
    platform_fee: Optional[float] = None
    profit_margin_pct: Optional[float] = None
    pages: Optional[List[Dict[str, Any]]] = None


def _format_fallback_title(path: str, url: str) -> str:
    if not path or path == "/":
        try:
            netloc = urlparse(url).netloc.replace("www.", "")
            parts = netloc.split(".")
            brand = parts[0].capitalize() if parts else "Home"
            return f"{brand} Home"
        except Exception:
            return "Home Page"
    segments = [s for s in path.strip("/").split("/") if s]
    if not segments:
        return "Home Page"
    last_seg = segments[-1]
    last_seg = last_seg.replace(".html", "").replace(".php", "").replace(".asp", "")
    words = [w.capitalize() for w in last_seg.replace("-", " ").replace("_", " ").split()]
    return " ".join(words) if words else "Page"


def _normalize_discovered_link(href: str, base_netloc: str) -> Optional[str]:
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


async def _async_discover_urls(base_url: str, depth: int = 1, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
    from playwright.async_api import async_playwright
    import asyncio

    target_url = base_url.strip()
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    parsed_base = urlparse(target_url)
    base_netloc = parsed_base.netloc.lower()

    discovered = {}  # url -> {"path": path, "title": title}
    clean_root = target_url.rstrip('/')
    discovered[clean_root] = {
        "path": "/",
        "title": _format_fallback_title("/", clean_root)
    }
    queue = [(clean_root, 0)]
    visited = set()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            bypass_csp=True,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        page.set_default_timeout(30000)

        while queue:
            if max_pages is not None and max_pages > 0 and len(discovered) >= max_pages:
                break
            current_url, current_depth = queue.pop(0)
            if current_url in visited:
                continue
            visited.add(current_url)

            try:
                await page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(0.5)

                # Capture actual DOM page title
                try:
                    actual_title = (await page.title() or "").strip()
                    if actual_title and current_url in discovered:
                        discovered[current_url]["title"] = actual_title
                except Exception:
                    pass

                # Extract internal links and their anchor text
                links_data = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('a[href]'))
                        .map(a => {
                            const text = (a.innerText || a.getAttribute('aria-label') || a.getAttribute('title') || '').trim().replace(/\\s+/g, ' ');
                            return { href: a.href, text: text };
                        })
                        .filter(item => item.href && (item.href.startsWith('http') || item.href.startsWith('/')));
                }''')

                for item in links_data:
                    h = item.get("href", "")
                    if h.startswith('/'):
                        h = f"{parsed_base.scheme}://{parsed_base.netloc}{h}"
                    norm = _normalize_discovered_link(h, base_netloc)
                    if norm and norm not in discovered:
                        path = urlparse(norm).path or "/"
                        link_text = (item.get("text") or "").strip()
                        if not link_text or len(link_text) < 2 or len(link_text) > 80:
                            link_text = _format_fallback_title(path, norm)
                        discovered[norm] = {"path": path, "title": link_text}

                        if current_depth + 1 < depth and (max_pages is None or max_pages <= 0 or len(discovered) < max_pages):
                            queue.append((norm, current_depth + 1))
                        if max_pages is not None and max_pages > 0 and len(discovered) >= max_pages:
                            break
            except Exception as e:
                logger.warning(f"Error exploring {current_url}: {e}")

        await browser.close()

    result = []
    for u, data in discovered.items():
        result.append({
            "url": u,
            "title": data.get("title") or _format_fallback_title(data.get("path", "/"), u),
            "path": data.get("path", "/")
        })
    return result


def _discover_urls_worker(base_url: str, depth: int, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
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
    Returns list of discovered URLs with Page Title and Full URL.
    """
    import asyncio
    base_url = request.url.strip()
    if not base_url.startswith(("http://", "https://")):
        base_url = "https://" + base_url

    try:
        discovered = await asyncio.to_thread(_discover_urls_worker, base_url, request.depth, request.max_pages)
    except Exception as e:
        logger.error(f"URL discovery failed for {base_url}: {e}")
        discovered = [{"url": base_url, "title": _format_fallback_title("/", base_url), "path": "/"}]

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


# ── ESTIMATION CRUD & PERSISTENCE ROUTES ──

@router.get("")
@router.get("/")
async def list_estimations(org_id: Optional[str] = None, db: Session = Depends(get_db)):
    """List all saved estimations stored in PostgreSQL."""
    records = estimation_repo.list_estimations(db, org_id=org_id)
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "base_url": r.base_url,
            "mode": r.mode,
            "status": r.status,
            "hourly_rate": r.hourly_rate,
            "platform_fee": r.platform_fee,
            "profit_margin_pct": r.profit_margin_pct,
            "total_pages": r.total_pages,
            "simple_pages": r.simple_pages,
            "medium_pages": r.medium_pages,
            "complex_pages": r.complex_pages,
            "total_manual_hours": r.total_manual_hours,
            "total_manual_cost": r.total_manual_cost,
            "total_api_cost": r.total_api_cost,
            "total_platform_cost": r.total_platform_cost,
            "total_base_cost": r.total_base_cost,
            "total_profit_margin": r.total_profit_margin,
            "total_quote": r.total_quote,
            "summary": r.summary,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in records
    ]


@router.post("/save")
async def save_estimation(request: SaveEstimateRequest, db: Session = Depends(get_db)):
    """Save an estimation calculation to the database."""
    record = estimation_repo.create_estimation(
        db=db,
        title=request.title,
        base_url=request.base_url,
        mode=request.mode,
        pages=request.pages,
        summary=request.summary,
        hourly_rate=request.hourly_rate,
        platform_fee=request.platform_fee,
        profit_margin_pct=request.profit_margin_pct,
        org_id=request.org_id
    )
    return {
        "id": str(record.id),
        "title": record.title,
        "base_url": record.base_url,
        "mode": record.mode,
        "status": record.status,
        "summary": record.summary,
        "pages": record.pages,
        "created_at": record.created_at.isoformat() if record.created_at else None
    }


@router.get("/{estimate_id}")
async def get_estimation_details(estimate_id: str, db: Session = Depends(get_db)):
    """Retrieve full details of a saved estimation."""
    record = estimation_repo.get_estimation(db, estimate_id)
    if not record:
        raise HTTPException(status_code=404, detail="Estimation record not found.")
    return {
        "id": str(record.id),
        "title": record.title,
        "base_url": record.base_url,
        "mode": record.mode,
        "status": record.status,
        "hourly_rate": record.hourly_rate,
        "platform_fee": record.platform_fee,
        "profit_margin_pct": record.profit_margin_pct,
        "total_pages": record.total_pages,
        "simple_pages": record.simple_pages,
        "medium_pages": record.medium_pages,
        "complex_pages": record.complex_pages,
        "total_manual_hours": record.total_manual_hours,
        "total_manual_cost": record.total_manual_cost,
        "total_api_cost": record.total_api_cost,
        "total_platform_cost": record.total_platform_cost,
        "total_base_cost": record.total_base_cost,
        "total_profit_margin": record.total_profit_margin,
        "total_quote": record.total_quote,
        "pages": record.pages,
        "summary": record.summary,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


@router.put("/{estimate_id}")
async def update_estimation_details(estimate_id: str, request: UpdateEstimateRequest, db: Session = Depends(get_db)):
    """Update commercial rates, manual overrides, or title of an estimation."""
    record = estimation_repo.get_estimation(db, estimate_id)
    if not record:
        raise HTTPException(status_code=404, detail="Estimation record not found.")

    new_h_rate = request.hourly_rate if request.hourly_rate is not None else record.hourly_rate
    new_p_fee = request.platform_fee if request.platform_fee is not None else record.platform_fee
    new_margin = request.profit_margin_pct if request.profit_margin_pct is not None else record.profit_margin_pct
    new_pages = request.pages if request.pages is not None else record.pages

    # Recalculate summary with updated values
    recalc_result = calculate_total_estimate(
        new_pages,
        hourly_rate=new_h_rate,
        platform_fee_per_page=new_p_fee,
        profit_margin_pct=new_margin
    )

    updated_record = estimation_repo.update_estimation(
        db=db,
        estimate_id=estimate_id,
        title=request.title,
        pages=recalc_result["pages"],
        summary=recalc_result["summary"],
        hourly_rate=new_h_rate,
        platform_fee=new_p_fee,
        profit_margin_pct=new_margin
    )
    return {
        "id": str(updated_record.id),
        "title": updated_record.title,
        "summary": updated_record.summary,
        "pages": updated_record.pages,
        "updated_at": updated_record.updated_at.isoformat() if updated_record.updated_at else None
    }


@router.delete("/{estimate_id}")
async def delete_estimation_record(estimate_id: str, db: Session = Depends(get_db)):
    """Delete a saved estimation record."""
    success = estimation_repo.delete_estimation(db, estimate_id)
    if not success:
        raise HTTPException(status_code=404, detail="Estimation record not found.")
    return {"status": "success", "message": f"Estimation {estimate_id} deleted successfully."}


@router.post("/analyze")
async def analyze_and_estimate(request: EstimationRequest, db: Session = Depends(get_db)):
    """
    Crawls URL, inspects DOM complexity per page, and computes effort, costs, and quotes.
    Automatically persists to database if save_to_db is True.
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
                discovered_urls = [d["url"] for d in discovered_items]
                if request.max_pages is not None and request.max_pages > 0:
                    discovered_urls = discovered_urls[:request.max_pages]
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

    # 4. Save to database if requested
    if request.save_to_db:
        try:
            primary_base = request.base_url or (discovered_urls[0] if discovered_urls else "")
            record = estimation_repo.create_estimation(
                db=db,
                title=request.title or "Website Audit Estimation",
                base_url=primary_base,
                mode=request.mode or "discover",
                pages=result["pages"],
                summary=result["summary"],
                hourly_rate=request.hourly_rate,
                platform_fee=request.platform_fee,
                profit_margin_pct=request.profit_margin_pct,
                org_id=request.org_id
            )
            result["id"] = str(record.id)
            result["title"] = record.title
        except Exception as save_err:
            logger.error(f"Failed to auto-save estimation record: {save_err}")

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
