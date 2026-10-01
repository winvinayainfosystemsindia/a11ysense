from playwright.async_api import Page
import base64
import logging

logger = logging.getLogger(__name__)

class VisionSkill:
    """
    Skill for visual accessibility analysis.
    """
    
    async def capture_for_ai(self, page: Page) -> str:
        """Captures a screenshot and returns it as a base64 string."""
        screenshot_bytes = await page.screenshot(full_page=False)
        return base64.b64encode(screenshot_bytes).decode('utf-8')

vision_skill = VisionSkill()
