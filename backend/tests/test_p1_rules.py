import pytest
from backend.common.constants.rule_catalog import (
    RULE_CATALOG,
    normalize_severity,
    principle_for,
    resolve_rule,
)


def test_normalize_severity():
    assert normalize_severity("Medium") == "Moderate"
    assert normalize_severity("medium") == "Moderate"
    assert normalize_severity("moderate") == "Moderate"
    assert normalize_severity("High") == "Serious"
    assert normalize_severity("serious") == "Serious"
    assert normalize_severity("critical") == "Critical"
    assert normalize_severity("low") == "Minor"
    assert normalize_severity("minor") == "Minor"
    assert normalize_severity(None) == "Moderate"
    # Never returns "Medium"
    assert normalize_severity("Medium") != "Medium"


def test_principle_for():
    assert principle_for("1.1.1") == "Perceivable"
    assert principle_for("2.1.1") == "Operable"
    assert principle_for("3.3.2") == "Understandable"
    assert principle_for("4.1.2") == "Robust"
    assert principle_for(None) == "N/A"
    assert principle_for("Best Practice") == "N/A"


def test_menuitem_tabindex_negative_finding():
    # role=menuitem tabindex=-1 finding (keyboard-non-focusable-interactive)
    res = resolve_rule(
        rule_id="keyboard-non-focusable-interactive",
        tags=[],
        impact="serious"
    )
    assert "2.1.1" in res["criteria"]
    assert "Keyboard" in res["criteria"]
    assert res["level"] == "A"
    assert res["principle"] == "Operable"
    assert res["severity"] == "Serious"
    assert res["severity"] != "Medium"


def test_label_in_name_mismatch_finding():
    # screen-reader-label-in-name-mismatch shows 2.5.3 Label in Name
    res = resolve_rule(
        rule_id="screen-reader-label-in-name-mismatch",
        tags=[],
        impact="moderate"
    )
    assert "2.5.3" in res["criteria"]
    assert "Label in Name" in res["criteria"]
    assert res["level"] == "A"
    assert res["principle"] == "Operable"
    assert res["severity"] == "Moderate"
    assert res["severity"] != "Medium"


def test_heading_order_shows_best_practice():
    # heading-order axe rule with tag best-practice
    res = resolve_rule(
        rule_id="heading-order",
        tags=["best-practice"],
        impact="moderate"
    )
    assert res["criteria"] == "Best Practice"
    assert res["level"] == "Best Practice"
    assert res["principle"] == "N/A"
    assert res["kind"] == "best-practice"
    assert res["severity"] == "Moderate"
    assert res["severity"] != "Medium"


def test_no_medium_severity_in_catalog():
    for rule_id, data in RULE_CATALOG.items():
        sev = data.get("default_severity")
        assert sev in ("Critical", "Serious", "Moderate", "Minor"), f"Rule {rule_id} has invalid severity: {sev}"
        assert sev != "Medium", f"Rule {rule_id} has severity 'Medium'!"


def test_radio_button_element_context_and_quick_key():
    from backend.app.core.skills.implementations.element_context import (
        extract_context_from_html,
        quick_key_for
    )

    # 1. Button element styled with role="radio" (e.g. Stocks, Mutual Funds, Months)
    stocks_snippet = '<button role="radio" aria-checked="true" class="tab-pill">Stocks</button>'
    ctx_stocks = extract_context_from_html(stocks_snippet)
    assert ctx_stocks["is_radio"] is True
    assert ctx_stocks["type_name"] == "radio button"
    assert "Stocks" in ctx_stocks["clean_name"]
    assert quick_key_for(ctx_stocks) == "R"
    assert quick_key_for(ctx_stocks) != "B"

    # 2. Native radio input
    input_snippet = '<input type="radio" id="mutual-funds" name="category" value="mf">'
    ctx_mf = extract_context_from_html(input_snippet)
    assert ctx_mf["is_radio"] is True
    assert ctx_mf["type_name"] == "radio button"
    assert quick_key_for(ctx_mf) == "R"
    assert quick_key_for(ctx_mf) != "B"

    # 3. Div with role="radio" (e.g. Months duration filter)
    months_snippet = '<div role="radio" aria-checked="false">Months</div>'
    ctx_months = extract_context_from_html(months_snippet)
    assert ctx_months["is_radio"] is True
    assert ctx_months["type_name"] == "radio button"
    assert quick_key_for(ctx_months) == "R"
    assert quick_key_for(ctx_months) != "B"


def test_radio_button_narrative_uses_key_r_not_b():
    from backend.app.core.reporting.narrative import fallback_narrative

    fb = fallback_narrative(
        "aria-required-parent",
        {
            "element_html": '<button role="radio" aria-checked="false">Stocks</button>',
            "visible_text": "Stocks",
            "page_url": "https://example.com"
        }
    )
    steps_joined = " ".join(fb["steps_to_reproduce"])
    # Must instruct using key R, NOT key B
    assert "Press R" in steps_joined
    assert "Press B" not in steps_joined
    assert "radio button" in fb["description"].lower() or "radio" in fb["description"].lower()


def test_dropdown_menuitem_narrative_tab_not_required():
    from backend.app.core.reporting.narrative import fallback_narrative

    fb = fallback_narrative(
        "keyboard-non-focusable-interactive",
        {
            "element_html": '<a role="menuitem" tabindex="-1" href="/stocks">Stocks</a>',
            "visible_text": "Stocks",
            "page_url": "https://example.com",
            "parent_menu": "Trade"
        }
    )
    # Verifies tab navigation is explicitly noted as not required for dropdowns
    assert "Tab navigation is not required for dropdowns" in fb["remarks"] or "Tab navigation is not required for dropdowns" in fb["description"] or "Tab navigation is not required" in fb["actual_result"]
    steps_joined = " ".join(fb["steps_to_reproduce"])
    assert "Down Arrow" in steps_joined

