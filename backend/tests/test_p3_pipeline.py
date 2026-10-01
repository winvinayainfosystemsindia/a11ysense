import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from backend.app.core.audit.auditor import AuditorAgent
from common.schemas.audit import Violation
from backend.app.core.reporting.narrative import validate_testcase, validate_defect


@pytest.fixture
def mock_auditor():
    auditor = AuditorAgent()
    return auditor


@pytest.mark.asyncio
async def test_valid_json_used_as_is(mock_auditor):
    # Valid testcase and defect JSON
    valid_tc_json = (
        '{"description": "The search button has no visible label or announcement.", '
        '"expected_result": "The button should have a clear text label. When focused, a screen reader announces search button. This saves time and avoids guessing.", '
        '"actual_result": "The button has no label at all. When focused, a screen reader hears only button. This makes navigation confusing and slow.", '
        '"steps_to_reproduce": ["Open the home page.", "Start NVDA.", "Press B to jump to the search button.", "Listen to the announcement.", "Notice that only button is announced."]}'
    )
    valid_def_json = (
        '{"friendly_name": "Search button missing label", '
        '"business_impact": "Blind users cannot find the search field, causing frustration.", '
        '"fix_steps": ["Locate the search button in header.", "Add an accessible label to the button.", "Test with keyboard navigation."], '
        '"code_before": "<button class=\\"search\\"></button>", '
        '"code_after": "<button class=\\"search\\">Search</button>", '
        '"verify_steps": ["Press Tab to focus search.", "Confirm screen reader says search.", "Re-run audit."], '
        '"false_positive_note": ""}'
    )

    call_count = 0
    async def mock_call_llm(prompt, **kwargs):
        nonlocal call_count
        call_count += 1
        if "role>" in prompt and "accessibility tester" in prompt:
            return valid_tc_json
        return valid_def_json

    mock_auditor.call_llm = mock_call_llm

    v = Violation(
        id="screen-reader-missing-label",
        impact="critical",
        description="Missing accessible label",
        help="Provide accessible label",
        nodes=[{"html": '<button class="search"></button>', "target": ["button.search"]}]
    )

    refined = await mock_auditor.refine_violation(v)
    assert refined.metadata["testcase"]["description"] == "The search button has no visible label or announcement."
    assert refined.metadata["remarks"] == ""
    assert call_count == 2  # 1 for TC, 1 for DEF


@pytest.mark.asyncio
async def test_banned_word_aria_triggers_retry_then_fallback(mock_auditor):
    # JSON with banned word 'ARIA' in description
    bad_tc_json = (
        '{"description": "The button is missing an ARIA label.", '
        '"expected_result": "The button should have a label.", '
        '"actual_result": "No label exists.", '
        '"steps_to_reproduce": ["Open page.", "Start NVDA.", "Press Tab.", "Notice error."]}'
    )

    attempts = 0
    async def mock_call_llm(prompt, **kwargs):
        nonlocal attempts
        attempts += 1
        return bad_tc_json

    mock_auditor.call_llm = mock_call_llm

    v = Violation(
        id="screen-reader-missing-label",
        impact="critical",
        description="Missing accessible label",
        help="Provide accessible label",
        nodes=[{"html": '<button class="search"></button>', "target": ["button.search"]}]
    )

    refined = await mock_auditor.refine_violation(v)
    # Should have attempted twice (initial + 1 retry) then fallen back to template
    assert attempts == 2
    assert refined.metadata["remarks"] == "AI text unavailable: template wording used"
    # Fallback narrative must not contain "ARIA"
    assert "aria" not in refined.metadata["testcase"]["description"].lower()


@pytest.mark.asyncio
async def test_garbage_text_triggers_fallback(mock_auditor):
    async def mock_call_llm(prompt, **kwargs):
        return "I am an AI and I cannot output JSON right now."

    mock_auditor.call_llm = mock_call_llm

    v = Violation(
        id="keyboard-non-focusable-interactive",
        impact="serious",
        description="Interactive control cannot be focused via keyboard.",
        help="Ensure keyboard accessibility",
        nodes=[{"html": '<div role="button">Click me</div>', "target": ["div.btn"]}]
    )

    refined = await mock_auditor.refine_violation(v)
    assert refined.metadata["remarks"] == "AI text unavailable: template wording used"
    assert refined.metadata["wcag_criteria"] == "2.1.1 Keyboard"
    assert refined.metadata["severity"] == "Serious"


@pytest.mark.asyncio
async def test_identical_elements_trigger_only_one_llm_call(mock_auditor):
    valid_tc_json = (
        '{"description": "The link has no text description.", '
        '"expected_result": "The link should name its destination. Screen readers announce the name clearly. This helps users navigate with ease.", '
        '"actual_result": "The link contains no text. Screen readers hear nothing or unhelpful filenames. Users feel confused.", '
        '"steps_to_reproduce": ["Open the page.", "Start NVDA.", "Press K to reach the link.", "Listen to the announcement.", "Notice that no name is spoken."]}'
    )
    valid_def_json = (
        '{"friendly_name": "Link missing label", '
        '"business_impact": "Users cannot tell where link goes.", '
        '"fix_steps": ["Locate link.", "Add visible text.", "Verify with Tab."], '
        '"code_before": "<a></a>", '
        '"code_after": "<a>Home</a>", '
        '"verify_steps": ["Press Tab.", "Listen for Home link.", "Re-scan."], '
        '"false_positive_note": ""}'
    )

    llm_calls = 0
    async def mock_call_llm(prompt, **kwargs):
        nonlocal llm_calls
        llm_calls += 1
        if "role>" in prompt and "accessibility tester" in prompt:
            return valid_tc_json
        return valid_def_json

    mock_auditor.call_llm = mock_call_llm

    v1 = Violation(
        id="screen-reader-missing-label",
        impact="critical",
        description="Missing label",
        help="Missing label",
        nodes=[{"html": '<a href="/playstore"></a>', "target": ["a.ps"]}]
    )
    v2 = Violation(
        id="screen-reader-missing-label",
        impact="critical",
        description="Missing label",
        help="Missing label",
        nodes=[{"html": '<a href="/playstore"></a>', "target": ["a.ps"]}]
    )

    await mock_auditor.refine_violation(v1)
    await mock_auditor.refine_violation(v2)

    # v1 took 2 calls (1 TC + 1 DEF). v2 has identical element html + rule_id, so it reused cached results!
    assert llm_calls == 2
