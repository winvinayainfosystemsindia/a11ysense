from playwright.async_api import async_playwright
import contextlib
import threading

# Thread-local storage so each audit thread gets its own Playwright browser.
# This prevents cross-event-loop errors when audits run in isolated daemon threads.
_thread_local = threading.local()

class BrowserManager:
    """
    Manages a per-thread Playwright browser instance.
    Each background audit thread gets its own browser to avoid event-loop conflicts.
    """

    async def _get_or_create_browser(self):
        """Return the browser for the current thread, starting one if needed."""
        if not getattr(_thread_local, "pw", None):
            _thread_local.pw = await async_playwright().start()
            _thread_local.browser = await _thread_local.pw.chromium.launch(headless=True)
        return _thread_local.browser

    async def stop(self):
        """Stop the browser for the current thread (call at end of audit)."""
        if getattr(_thread_local, "browser", None):
            try:
                await _thread_local.browser.close()
            except Exception:
                pass
            _thread_local.browser = None
        if getattr(_thread_local, "pw", None):
            try:
                await _thread_local.pw.stop()
            except Exception:
                pass
            _thread_local.pw = None

    @contextlib.asynccontextmanager
    async def get_page(self, storage_state: dict = None, extra_http_headers: dict = None):
        browser = await self._get_or_create_browser()

        kwargs = {
            "bypass_csp": True,
            "viewport": {"width": 1280, "height": 800},
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ),
        }
        if storage_state:
            kwargs["storage_state"] = storage_state
        if extra_http_headers:
            kwargs["extra_http_headers"] = extra_http_headers

        context = await browser.new_context(**kwargs)
        page = await context.new_page()
        page.set_default_timeout(60000)
        try:
            yield page
        finally:
            await context.close()

browser_manager = BrowserManager()
