from playwright.async_api import async_playwright
import contextlib

class BrowserManager:
    def __init__(self):
        self.pw = None
        self.browser = None

    async def start(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(headless=True)

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()

    @contextlib.asynccontextmanager
    async def get_page(self, storage_state: dict = None):
        if not self.browser:
            await self.start()
        
        kwargs = {
            "bypass_csp": True,
            "viewport": {'width': 1280, 'height': 800},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
        if storage_state:
            kwargs["storage_state"] = storage_state

        context = await self.browser.new_context(**kwargs)
        page = await context.new_page()
        page.set_default_timeout(60000)
        try:
            yield page
        finally:
            await context.close()

browser_manager = BrowserManager()
