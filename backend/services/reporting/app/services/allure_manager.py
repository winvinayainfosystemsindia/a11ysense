import uuid
import time
import json
import os
from typing import List, Dict, Any, Tuple
from app.schemas.audit import AuditResult, Violation

class AllureManager:
    """
    Manages the creation of industry-standard Allure reports.
    Follows a structured approach: Scenarios -> Test Cases -> Execution Steps -> Defect Reports.
    """
    
    def __init__(self, results_dir: str):
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)

    def map_severity(self, severity: str) -> str:
        mapping = {
            "critical": "blocker",
            "high": "critical",
            "medium": "normal",
            "low": "minor"
        }
        return mapping.get(severity.lower(), "normal")

    def _generate_tc_id(self, url: str, page_title: str, counter: int) -> str:
        from urllib.parse import urlparse
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.split(':')[0]
            if domain.startswith("www."):
                domain = domain[4:]
            domain_parts = domain.split('.')
            if domain_parts:
                website = domain_parts[0]
                if website.lower() in ["localhost", "127", "10", "192", "172"]:
                    website = "Website"
                else:
                    website = website.capitalize()
            else:
                website = "Website"
        except Exception:
            website = "Website"
            
        title = (page_title or "Page").strip()
        title = " ".join(title.split())
        if len(title) > 30:
            title = title[:27] + "..."
            
        counter_str = f"{counter:03d}"
        return f"TC-{website}-{title} -{counter_str}"

    def generate_allure_json(self, result: AuditResult, custom_task_id: str = None) -> str:
        task_id = custom_task_id or str(uuid.uuid4())
        # Use a stable start time for Allure
        start_time = int(time.time() * 1000)
        
        # 1. Create Environment Metadata
        self._write_environment_properties(result)

        # 2. Build the main test result
        allure_result = {
            "uuid": task_id,
            "historyId": f"{result.url}-audit",
            "name": f"Accessibility Audit: {result.metadata.get('page_title', result.url)}",
            "status": "failed" if result.violations else "passed",
            "statusDetails": {
                "message": f"Audit Summary: {len(result.violations)} Violations | {len(result.passes or [])} Passed"
            },
            "stage": "finished",
            "steps": [],
            "attachments": [],
            "parameters": [
                {"name": "Target URL", "value": str(result.url)},
                {"name": "Page Title", "value": str(result.metadata.get("page_title", "Unknown"))}
            ],
            "labels": [
                {"name": "feature", "value": "Compliance Audit"},
                {"name": "epic", "value": "Enterprise Accessibility"},
                {"name": "story", "value": "WCAG 2.2 Standards Verification"},
                {"name": "suite", "value": "A11ySense Audit Suite"},
                {"name": "subSuite", "value": result.url},
                {"name": "owner", "value": "A11ySense-Reporting-Service"}
            ],
            "links": [{"name": "Audited Page", "url": str(result.url)}],
            "start": start_time,
            "stop": start_time + 5000
        }

        # 3. Scenario 1: Automated Compliance Verification (Passes)
        counter = 1
        if result.passes:
            pass_scenario, counter = self._build_scenario_step(
                "Scenario: Automated Compliance Verification", 
                "Verifying page elements against automated WCAG rules.",
                result.passes, 
                "passed",
                start_time,
                result,
                counter
            )
            allure_result["steps"].append(pass_scenario)

        # 4. Scenario 2: Accessibility Defect Reporting (Failures)
        if result.violations:
            fail_scenario, counter = self._build_defect_scenario(
                "Scenario: Accessibility Defect Reporting",
                "Identifying and documenting barriers for assistive technology users.",
                result.violations,
                start_time,
                result,
                counter
            )
            allure_result["steps"].append(fail_scenario)

        # 5. Save and Return
        result_path = os.path.join(self.results_dir, f"{task_id}-result.json")
        with open(result_path, "w") as f:
            json.dump(allure_result, f, indent=4)
            
        self._attach_raw_data(allure_result, result, result_path)
        
        return task_id

    def _build_scenario_step(self, name: str, description: str, items: List[Any], status: str, start_time: int, result: AuditResult, start_counter: int) -> Tuple[Dict[str, Any], int]:
        """Builds a high-level test scenario step."""
        scenario = {
            "name": name,
            "status": status,
            "statusDetails": {"message": str(description)},
            "steps": [],
            "start": start_time,
            "stop": start_time + 100
        }
        counter = start_counter
        for item in items:
            # Safely handle items which could be dicts or objects
            item_id = item.get('id', 'Unknown') if isinstance(item, dict) else getattr(item, 'id', 'Unknown')
            item_help = item.get('help', item_id) if isinstance(item, dict) else getattr(item, 'help', item_id)
            item_desc = item.get('description', 'Standard followed.') if isinstance(item, dict) else getattr(item, 'description', 'Standard followed.')
            
            page_title = result.metadata.get("page_title", "Page")
            tc_custom_id = self._generate_tc_id(result.url, page_title, counter)
            
            scenario["steps"].append({
                "name": f"{tc_custom_id} [{item_id}]: {item_help}",
                "status": status,
                "statusDetails": {"message": str(item_desc)},
                "start": start_time,
                "stop": start_time + 10
            })
            counter += 1
        return scenario, counter

    def _build_defect_scenario(self, name: str, description: str, violations: List[Violation], start_time: int, result: AuditResult, start_counter: int) -> Tuple[Dict[str, Any], int]:
        """Builds a defect-heavy scenario step with full execution details."""
        scenario = {
            "name": name,
            "status": "failed",
            "statusDetails": {"message": str(description)},
            "steps": [],
            "start": start_time,
            "stop": start_time + 1000
        }
        
        counter = start_counter
        for v in violations:
            metadata = v.metadata or {}
            
            nodes = v.nodes or []
            if not isinstance(nodes, list):
                nodes = [nodes]
                
            for node in nodes:
                node_data = node if isinstance(node, dict) else (node.model_dump(mode='json') if hasattr(node, 'model_dump') else vars(node))
                
                # Extract fields
                page_title = node_data.get('page_title', 'N/A')
                if page_title == 'N/A':
                    page_title = result.metadata.get('page_title', 'Page')
                url = node_data.get('page_url', result.url)
                criteria = metadata.get('wcag_criteria', 'N/A')
                level = metadata.get('wcag_level', 'N/A')
                severity = metadata.get('severity', getattr(v, 'impact', 'N/A'))
                desc = metadata.get('description', getattr(v, 'description', 'N/A'))
                business_impact = metadata.get('business_impact', 'N/A')
                exp_res = metadata.get('expected_result', 'N/A')
                act_res = metadata.get('actual_result', 'N/A')
                repro = metadata.get('steps_to_reproduce', 'N/A')
                remedy = metadata.get('remediation', 'N/A')
                refined_by = metadata.get('refined_by', 'N/A')
                help_url = getattr(v, 'helpUrl', getattr(v, 'help_url', 'N/A'))
                html_snippet = node_data.get('html', 'N/A')

                friendly_name = metadata.get('friendly_name', desc)
                testcase_id = getattr(v, 'id', 'Unknown')
                help_text = metadata.get('help', getattr(v, 'help', 'N/A'))
                
                tc_custom_id = self._generate_tc_id(result.url, page_title, counter)

                # Convert to string if they are complex objects
                if not isinstance(remedy, str): remedy = json.dumps(remedy, indent=2)
                if not isinstance(repro, str): repro = json.dumps(repro, indent=2)
                if not isinstance(act_res, str): act_res = json.dumps(act_res, indent=2)
                if not isinstance(html_snippet, str): html_snippet = json.dumps(html_snippet, indent=2)

                attachments = []
                screenshot_filename = metadata.get("screenshot")
                if screenshot_filename:
                    audit_dir = os.path.dirname(self.results_dir)
                    source_path = os.path.join(audit_dir, screenshot_filename)
                    if os.path.exists(source_path):
                        import shutil
                        dest_path = os.path.join(self.results_dir, screenshot_filename)
                        try:
                            shutil.copy2(source_path, dest_path)
                            attachments.append({
                                "name": "Defect Screenshot Evidence",
                                "source": screenshot_filename,
                                "type": "image/png"
                            })
                        except Exception as copy_err:
                            print(f"Failed to copy screenshot to allure results: {copy_err}")

                test_case = {
                    "name": f"{tc_custom_id} [{testcase_id}]: {friendly_name}",
                    "status": "failed",
                    "defects": [
                        {
                            "defect_id": f"DEF-{testcase_id}",
                            "page_title": page_title,
                            "url": url,
                            "criteria": criteria,
                            "level": level,
                            "severity": severity,
                            "description": desc,
                            "expected_result": exp_res,
                            "actual_result": act_res,
                            "help": help_text,
                            "steps_to_reproduce": repro,
                            "remediation": remedy,
                            "html_snippet": html_snippet
                        }
                    ],
                    "steps": [
                        {
                            "name": "Defect ID",
                            "status": "passed",
                            "statusDetails": {"message": f"Defect ID: DEF-{testcase_id}"},
                            "start": start_time, "stop": start_time + 5
                        },
                        {
                            "name": "Page Title & URL",
                            "status": "passed",
                            "statusDetails": {"message": f"Page Title: {page_title}\nURL: {url}"},
                            "start": start_time, "stop": start_time + 5
                        },
                        {
                            "name": "Criteria, Level & Severity",
                            "status": "passed",
                            "statusDetails": {"message": f"Criteria: {criteria}\nLevel: {level}\nSeverity: {severity}"},
                            "start": start_time, "stop": start_time + 5
                        },
                        {
                            "name": "Description & Business Impact",
                            "status": "passed",
                            "statusDetails": {"message": f"Description: {desc}\nBusiness Impact: {business_impact}"},
                            "start": start_time, "stop": start_time + 5
                        },
                        {
                            "name": "Expected & Actual Result",
                            "status": "failed",
                            "statusDetails": {"message": f"Expected Result: {exp_res}\nActual Result: {act_res}"},
                            "start": start_time, "stop": start_time + 5
                        },
                        {
                            "name": "Help URL",
                            "status": "passed",
                            "statusDetails": {"message": f"Help: {help_text}\nURL: {help_url}"},
                            "start": start_time, "stop": start_time + 5
                        },
                        {
                            "name": "Steps To Reproduce",
                            "status": "passed",
                            "statusDetails": {"message": str(repro)},
                            "start": start_time, "stop": start_time + 5
                        },
                        {
                            "name": "Remediation & Refined By",
                            "status": "passed",
                            "statusDetails": {"message": f"Remediation: {remedy}\nRefined By: {refined_by}"},
                            "start": start_time, "stop": start_time + 5
                        },
                        {
                            "name": "HTML Snippet",
                            "status": "passed",
                            "statusDetails": {"message": str(html_snippet)},
                            "start": start_time, "stop": start_time + 5
                        }
                    ],
                    "attachments": attachments,
                    "start": start_time,
                    "stop": start_time + 100
                }
                scenario["steps"].append(test_case)
                counter += 1
            
        return scenario, counter

    def _write_environment_properties(self, result: AuditResult):
        env_path = os.path.join(self.results_dir, "environment.properties")
        with open(env_path, "w") as f:
            f.write(f"Auditor.Platform=A11ySense Enterprise\n")
            f.write(f"Auditor.Engine=Axe-Core\n")
            f.write(f"Audit.URL={result.url}\n")
            f.write(f"Audit.Timestamp={result.timestamp.isoformat()}\n")
            
            score = result.metadata.get("accessibility_score")
            if score is not None:
                f.write(f"Audit.AccessibilityScore={score}/100\n")
                
            breakdown = result.metadata.get("score_breakdown", {})
            if breakdown:
                f.write(f"Audit.Penalty.Critical={breakdown.get('critical_penalty', 0.0)}\n")
                f.write(f"Audit.Penalty.Serious={breakdown.get('serious_penalty', 0.0)}\n")
                f.write(f"Audit.Penalty.Moderate={breakdown.get('moderate_penalty', 0.0)}\n")
                f.write(f"Audit.Penalty.Minor={breakdown.get('minor_penalty', 0.0)}\n")
                
            trend = result.metadata.get("trend", {})
            if trend:
                score_diff = trend.get("score_difference")
                if score_diff is not None:
                    sign = "+" if score_diff >= 0 else ""
                    f.write(f"Audit.Trend.ScoreDifference={sign}{score_diff} points\n")
                f.write(f"Audit.Trend.ResolvedCount={trend.get('resolved_violations_count', 0)}\n")
                f.write(f"Audit.Trend.NewCount={trend.get('new_violations_count', 0)}\n")

            token_usage = result.metadata.get("token_usage", {})
            if token_usage:
                f.write(f"LLM.Provider={token_usage.get('provider', 'N/A')}\n")
                f.write(f"LLM.TotalCalls={token_usage.get('llm_calls', 0)}\n")
                f.write(f"LLM.TokensSent={token_usage.get('tokens_sent', 0)}\n")
                f.write(f"LLM.TokensReceived={token_usage.get('tokens_received', 0)}\n")
                f.write(f"LLM.TokensTotal={token_usage.get('tokens_total', 0)}\n")
                
                bd = token_usage.get("breakdown", {})
                if "manager" in bd:
                    mgr = bd["manager"]
                    f.write(f"LLM.Manager.Calls={mgr.get('calls', 0)}\n")
                    f.write(f"LLM.Manager.TokensTotal={mgr.get('tokens_total', 0)}\n")
                if "auditor" in bd:
                    aud = bd["auditor"]
                    f.write(f"LLM.Auditor.Calls={aud.get('calls', 0)}\n")
                    f.write(f"LLM.Auditor.TokensTotal={aud.get('tokens_total', 0)}\n")

    def _attach_raw_data(self, allure_result: Dict, result: AuditResult, result_path: str):
        # 1. Attach optimized raw AXE data (without passes, minified)
        attachment_id = str(uuid.uuid4())
        attachment_path = os.path.join(self.results_dir, f"{attachment_id}-attachment.json")
        
        raw_data = result.model_dump(mode='json')
        # Strip heavy passes list to save massive storage space (95%+ savings)
        if "passes" in raw_data:
            raw_data["passes"] = []
            
        with open(attachment_path, "w", encoding='utf-8') as f:
            json.dump(raw_data, f, separators=(',', ':'), ensure_ascii=False)
        
        allure_result["attachments"].append({
            "name": "Full Technical Evidence",
            "source": f"{attachment_id}-attachment.json",
            "type": "application/json"
        })
        
        # Save allure_result (minified to save space)
        with open(result_path, "w", encoding='utf-8') as f:
            json.dump(allure_result, f, separators=(',', ':'), ensure_ascii=False)
