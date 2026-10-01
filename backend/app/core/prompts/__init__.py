"""
Centralized Prompt Repository for A11ySense AI.
Maintains prompts for:
- System Prompts (auditor.xml, manager.xml)
- Test Cases (testcases/testcase_prompt.xml)
- Defects (defects/defect_prompt.xml)
"""
from pathlib import Path
from typing import Dict, Any

PROMPTS_ROOT = Path(__file__).parent


def load_prompt_template(relative_path: str) -> str:
    """Loads a prompt template string from backend/app/core/prompts/."""
    file_path = PROMPTS_ROOT / relative_path
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt template not found at {file_path}")
    return file_path.read_text(encoding="utf-8")


def get_testcase_prompt(context: Dict[str, Any]) -> str:
    """Renders the test case prompt template with violation context."""
    template = load_prompt_template("testcases/testcase_prompt.xml")
    return template.format(
        rule_id=context.get("rule_id", "unknown"),
        impact=context.get("impact", "unknown"),
        description=context.get("description", ""),
        help=context.get("help", ""),
        help_url=context.get("help_url", ""),
        element_selector=context.get("element_selector", "(not available)"),
        page_url=context.get("page_url", ""),
        nodes_html=context.get("nodes_html", "(no HTML nodes captured)")
    )


def get_defect_prompt(context: Dict[str, Any]) -> str:
    """Renders the defect prompt template with violation context."""
    template = load_prompt_template("defects/defect_prompt.xml")
    return template.format(
        rule_id=context.get("rule_id", "unknown"),
        impact=context.get("impact", "unknown"),
        description=context.get("description", ""),
        help=context.get("help", ""),
        help_url=context.get("help_url", ""),
        element_selector=context.get("element_selector", "(not available)"),
        page_url=context.get("page_url", ""),
        nodes_html=context.get("nodes_html", "(no HTML nodes captured)")
    )
