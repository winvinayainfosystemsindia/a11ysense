from playwright.async_api import Page
from app.schemas import Violation
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)

# Resolve storage directory relative to this source file.
# Path: implementations/scanner.py → up 6 levels → project root (A11ySense_AI/)
_PROJECT_ROOT = Path(__file__).resolve().parents[6]
_STORAGE_DIR = _PROJECT_ROOT / "axe_library"

class ScannerSkill:
    """
    Skill for performing automated accessibility scans using axe-core.
    """
    
    def __init__(self):
        self.axe_script_url = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.2/axe.min.js"

    async def run_axe(self, page: Page):
        logger.info("Running Axe-core scan")
        # Inject Axe locally if available to support 100% offline environments with 0ms network latency
        local_axe_path = str(_STORAGE_DIR / "axe.min.js")
        if Path(local_axe_path).exists():
            await page.add_script_tag(path=local_axe_path)
            logger.debug(f"Axe-core loaded from local storage: {local_axe_path}")
        else:
            await page.add_script_tag(url=self.axe_script_url)
            logger.debug(f"Axe-core loaded from CDN: {self.axe_script_url}")
        
        # Run Audit
        results = await page.evaluate("async () => { return await axe.run(); }")
        
        violations = []
        for v in results.get("violations", []):
            violations.append(Violation(
                id=v["id"],
                impact=v.get("impact"),
                description=v["description"],
                help=v["help"],
                helpUrl=v["helpUrl"],
                nodes=v["nodes"]
            ))
            
        return {
            "violations": violations,
            "passes": results.get("passes", []),
            "incomplete": results.get("incomplete", []),
            "inapplicable": results.get("inapplicable", []),
            "summary": {
                "total_violations": len(violations),
                "total_passes": len(results.get("passes", [])),
                "total_incomplete": len(results.get("incomplete", [])),
                "total_inapplicable": len(results.get("inapplicable", [])),
                "engine": results.get("testEngine", {}).get("name", "axe-core")
            }
        }

scanner_skill = ScannerSkill()

