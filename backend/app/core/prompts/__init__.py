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
PROMPT_VERSION = "2"


def load_prompt_template(relative_path: str) -> str:
    """Loads a prompt template string from backend/app/core/prompts/."""
    file_path = PROMPTS_ROOT / relative_path
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt template not found at {file_path}")
    return file_path.read_text(encoding="utf-8")


def get_testcase_prompt(context: Dict[str, Any]) -> str:
    """
    Renders the testcase prompt template, filling ALL placeholders with defaults '(not captured)'.
    Placeholders:
      rule_summary, technical_description, sc_code, sc_name, level, principle,
      page_url, page_title, current_announcement, element_context,
      screen_reader_quick_key, repeat_count, element_html
    """
    template = load_prompt_template("testcases/testcase_prompt.xml")
    defaults = {
        "rule_summary": "(not captured)",
        "technical_description": "(not captured)",
        "sc_code": "(not captured)",
        "sc_name": "(not captured)",
        "level": "(not captured)",
        "principle": "(not captured)",
        "page_url": "(not captured)",
        "page_title": "(not captured)",
        "current_announcement": "(not captured)",
        "element_context": "(not captured)",
        "screen_reader_quick_key": "Tab",
        "repeat_count": "1",
        "element_html": "(not captured)",
    }
    merged = {**defaults, **{k: str(v) if v is not None and str(v).strip() else defaults[k] for k, v in context.items() if k in defaults}}
    return template.format(**merged)


def get_defect_prompt(context: Dict[str, Any]) -> str:
    """
    Renders the defect prompt template, filling ALL placeholders with defaults '(not captured)'.
    Placeholders:
      rule_summary, technical_description, sc_code, sc_name, level, principle,
      severity, page_url, current_announcement, element_context, help_url,
      testcase_description, testcase_actual_result, element_html
    """
    template = load_prompt_template("defects/defect_prompt.xml")
    defaults = {
        "rule_summary": "(not captured)",
        "technical_description": "(not captured)",
        "sc_code": "(not captured)",
        "sc_name": "(not captured)",
        "level": "(not captured)",
        "principle": "(not captured)",
        "severity": "(not captured)",
        "page_url": "(not captured)",
        "current_announcement": "(not captured)",
        "element_context": "(not captured)",
        "help_url": "(not captured)",
        "testcase_description": "(not captured)",
        "testcase_actual_result": "(not captured)",
        "element_html": "(not captured)",
    }
    merged = {**defaults, **{k: str(v) if v is not None and str(v).strip() else defaults[k] for k, v in context.items() if k in defaults}}
    return template.format(**merged)
