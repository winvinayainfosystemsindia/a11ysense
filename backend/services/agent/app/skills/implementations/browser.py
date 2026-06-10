from playwright.async_api import Page
from app.utils.browser import browser_manager
import logging

logger = logging.getLogger(__name__)

class BrowserSkill:
    """
    Skill for interacting with a web browser.
    Provides autonomous-friendly methods for navigation and interaction.
    """
    
    async def navigate(self, page: Page, url: str):
        logger.info(f"Navigating to {url}")
        # Use a more relaxed wait condition and longer timeout
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
    async def click(self, page: Page, selector: str):
        logger.info(f"Clicking {selector}")
        await page.click(selector)
        
    async def get_screenshot(self, page: Page) -> bytes:
        return await page.screenshot(full_page=False)
        
    async def get_accessibility_tree(self, page: Page):
        """Returns the browser's accessibility tree for visual analysis."""
        return await page.accessibility.snapshot()

browser_skill = BrowserSkill()
