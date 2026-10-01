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
