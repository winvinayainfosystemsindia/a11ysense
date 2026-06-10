import pytest
import json
from common.schemas.audit import Violation
from app.schemas.analyze import ScoreBreakdown, TrendBreakdown
from app.core.heuristics import aggregate_and_deduplicate, is_node_hidden, is_node_decorative_spacer, is_dev_only_element
from app.core.scoring import calculate_accessibility_score
from app.core.history import generate_trend_analysis, _get_url_key, load_previous_audit, save_current_audit

def test_is_node_hidden():
    """
    Validates heuristic pre-filtering rules for hidden elements.
    """
    hidden_node_1 = {"html": '<div aria-hidden="true">Content</div>', "target": [".hidden"]}
    hidden_node_2 = {"html": '<span style="display: none;">Content</span>', "target": ["span"]}
    hidden_node_3 = {"html": '<input type="hidden" name="token">', "target": ["input"]}
    visible_node = {"html": '<div>Accessible content</div>', "target": ["div"]}
    
    assert is_node_hidden(hidden_node_1) is True
    assert is_node_hidden(hidden_node_2) is True
    assert is_node_hidden(hidden_node_3) is True
    assert is_node_hidden(visible_node) is False

def test_is_node_decorative_spacer():
    """
    Validates heuristic pre-filtering rules for decorative spacer tags.
    """
    spacer_node_1 = {"html": '<div class="spacer" role="presentation"></div>', "target": [".spacer"]}
    spacer_node_2 = {"html": '<span class="divider">   </span>', "target": [".divider"]}
    meaningful_node = {"html": '<span aria-label="Home Logo"></span>', "target": ["span"]}
    text_node = {"html": '<div>Hello World</div>', "target": ["div"]}
    
    assert is_node_decorative_spacer(spacer_node_1) is True
    assert is_node_decorative_spacer(spacer_node_2) is True
    assert is_node_decorative_spacer(meaningful_node) is False
    assert is_node_decorative_spacer(text_node) is False

def test_is_dev_only_element():
    """
    Validates heuristic filtering of hot-reloading dev indicators or overlays.
    """
    dev_node = {"html": '<div id="webpack-dev-server-client-overlay">Error</div>', "target": ["#webpack-dev-server-client-overlay"]}
    app_node = {"html": '<div class="app-body">Dashboard</div>', "target": [".app-body"]}
    
    assert is_dev_only_element(dev_node) is True
    assert is_dev_only_element(app_node) is False

def test_aggregate_and_deduplicate():
    """
    Validates rules de-duplication across different scanned pages.
    """
    violations = [
        Violation(
            id="color-contrast",
            impact="serious",
            description="Low color contrast",
            help="Low contrast",
            nodes=[
                {"html": '<button class="nav-link">Home</button>', "target": [".nav-link"], "page_url": "http://test.com/page1"},
                {"html": '<button class="nav-link">Home</button>', "target": [".nav-link"], "page_url": "http://test.com/page1"} # Duplicate node
            ]
        ),
        Violation(
            id="color-contrast",
            impact="serious",
            description="Low color contrast",
            help="Low contrast",
            nodes=[
                {"html": '<button class="nav-link">Home</button>', "target": [".nav-link"], "page_url": "http://test.com/page2"}, # Repeating nav on page2
                {"html": '<div aria-hidden="true">Hidden Contrast</div>', "target": [".hidden"], "page_url": "http://test.com/page2"} # False positive node
            ]
        ),
        Violation(
            id="image-alt",
            impact="critical",
            description="Images must have alt",
            help="Missing alt text",
            nodes=[
                {"html": '<img src="logo.png">', "target": ["img"], "page_url": "http://test.com/page1"}
            ]
        )
    ]
    
    deduped = aggregate_and_deduplicate(violations)
    
    assert len(deduped) == 2  # color-contrast and image-alt
    
    # Verify color-contrast has merged nodes across page1 and page2, and filtered out the hidden node
    contrast_violation = next(v for v in deduped if v.id == "color-contrast")
    assert len(contrast_violation.nodes) == 2
    assert contrast_violation.nodes[0]["page_url"] == "http://test.com/page1"
    assert contrast_violation.nodes[1]["page_url"] == "http://test.com/page2"
    assert not any("Hidden" in n.get("html", "") for n in contrast_violation.nodes)

def test_scoring_engine():
    """
    Validates weighted compliance scoring and logarithmic multipliers.
    """
    violations = [
        Violation(
            id="image-alt",
            impact="critical",
            description="Images missing alt text",
            help="Images missing alt",
            nodes=[
                {"html": '<img src="1.png">', "target": ["img"]},
                {"html": '<img src="2.png">', "target": ["img"]},
                {"html": '<img src="3.png">', "target": ["img"]}
            ]
        ),
        Violation(
            id="color-contrast",
            impact="serious",
            description="Contrast issue",
            help="Contrast",
            nodes=[
                {"html": '<div class="text">Poor Contrast</div>', "target": [".text"]}
            ]
        )
    ]
    
    score, breakdown = calculate_accessibility_score(violations)
    
    # 1. Critical Penalty: 10 * ln(1 + 3) = 10 * 1.386 = 13.86
    # 2. Serious Penalty: 6 * ln(1 + 1) = 6 * 0.693 = 4.16
    # Total Penalty: 18.02
    # Score: 100 - 18.02 = 81.98 -> rounded to 82.0
    assert score == 82.0
    assert breakdown.critical_penalty == 13.86
    assert breakdown.serious_penalty == 4.16

def test_trend_regression_engine():
    """
    Validates stateful historical trend delta compiling.
    """
    url = "https://example-regression.com"
    violations_run_1 = [
        Violation(id="color-contrast", impact="serious", description="Contrast", help="Contrast", nodes=[{"html": "div"}])
    ]
    
    # Save Run 1
    save_current_audit(url, 94.0, violations_run_1)
    
    # Run 2: score improved to 97.0, color-contrast is resolved, image-alt is new
    violations_run_2 = [
        Violation(id="image-alt", impact="critical", description="Alt text", help="Alt text", nodes=[{"html": "img"}])
    ]
    
    trend = generate_trend_analysis(url, 97.0, violations_run_2)
    
    assert trend.previous_score == 94.0
    assert trend.score_difference == 3.0
    assert trend.resolved_violations_count == 1
    assert trend.new_violations_count == 1
    assert "color-contrast" in trend.resolved_rules
    assert "image-alt" in trend.new_rules
