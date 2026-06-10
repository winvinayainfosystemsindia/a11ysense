from app.utils.browser import browser_manager
from common.schemas.audit import AuditRequest, AuditResult, Violation
import json
import os

class AuditService:
    def __init__(self):
        # Path to axe.min.js - in a real app, this would be bundled or downloaded
        self.axe_script_url = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.2/axe.min.js"

    async def run_audit(self, request: AuditRequest) -> AuditResult:
        async with browser_manager.get_page() as page:
            # 1. Navigate (use domcontentloaded to prevent timeout on pages with long-lived network activity)
            await page.goto(str(request.url), wait_until="domcontentloaded", timeout=60000)
            
            # 2. Inject Axe-core
            import os
            from pathlib import Path
            _PROJECT_ROOT = Path(__file__).resolve().parents[5]
            local_axe_path = str(_PROJECT_ROOT / "axe_library" / "axe.min.js")
            if os.path.exists(local_axe_path):
                await page.add_script_tag(path=local_axe_path)
            else:
                await page.add_script_tag(url=self.axe_script_url)
            
            # 3. Run Audit
            results = await page.evaluate("async () => { return await axe.run(); }")
            
            # 4. Parse Results
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
            
            return AuditResult(
                url=request.url,
                violations=violations,
                metadata={
                    "testEngine": results["testEngine"],
                    "testRunner": results["testRunner"],
                    "testEnvironment": results["testEnvironment"]
                }
            )

audit_service = AuditService()
