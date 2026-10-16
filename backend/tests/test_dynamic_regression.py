"""
Tests for live/dynamic content normalization, stable fingerprinting, group matching,
and regression reconciliation.
"""
import glob
import io
import json
import os
import re
import sys
import uuid
import openpyxl
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from common.database.connection import get_session_local
from common.database.models import Organization, Project, AuditSession, Defect, DefectEvent, SuccessCriterion
from app.core.regression.fingerprint import (
    normalize_url,
    normalize_href,
    normalize_dynamic_text,
    fingerprint_batch,
    get_rules,
)
from app.core.regression.matcher import MatchItem, match_groups
from app.core.regression.reconciler import reconciler, compute_fingerprint, compute_loose_fingerprint
from app.core.reporting.excel_generator import generate_excel_report


@pytest.fixture
def db_session():
    """Provides a transactional database session for tests, cleaned up after."""
    db = get_session_local()()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def test_project(db_session):
    """Provides a test organization and project."""
    org = db_session.query(Organization).first()
    if not org:
        org = Organization(name=f"Dynamic Test Org {uuid.uuid4().hex[:6]}")
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)

    proj = Project(
        name=f"Dynamic Test Project {uuid.uuid4().hex[:6]}",
        organization_id=org.id,
        base_url="https://lemonn.co.in",
        project_type="web_page",
        status="active"
    )
    db_session.add(proj)
    db_session.commit()
    db_session.refresh(proj)
    yield proj

    # Cleanup
    db_session.query(DefectEvent).filter(DefectEvent.defect.has(project_id=proj.id)).delete(synchronize_session=False)
    db_session.query(Defect).filter(Defect.project_id == proj.id).delete(synchronize_session=False)
    db_session.query(AuditSession).filter(AuditSession.project_id == proj.id).delete(synchronize_session=False)
    db_session.query(Project).filter(Project.id == proj.id).delete(synchronize_session=False)
    db_session.commit()


def _create_mock_session(db, project_id: uuid.UUID, run_number: int, url: str = "https://lemonn.co.in") -> AuditSession:
    proj = db.query(Project).filter(Project.id == project_id).first()
    sess = AuditSession(
        task_id=f"test-dyn-{run_number}-{uuid.uuid4().hex[:6]}",
        project_id=project_id,
        organization_id=proj.organization_id if proj else None,
        run_number=run_number,
        run_type="baseline" if run_number == 1 else "regression",
        url=url,
        status="completed",
        score=85.0
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)
    return sess


# ── 1. Unit Tests for Normalization Rules ─────────────────────────────────────

def test_normalize_dynamic_text_patterns():
    rules = get_rules()

    # Price normalization (normalized text is lowercased)
    assert "<price>" in normalize_dynamic_text("Price ₹948.30", rules=rules)
    assert "<price>" in normalize_dynamic_text("Price $1,250.00", rules=rules)
    assert "<price>" in normalize_dynamic_text("Price €50", rules=rules)
    assert "<price>" in normalize_dynamic_text("Rs. 100", rules=rules)
    assert "<price>" in normalize_dynamic_text("INR 5,000", rules=rules)

    # Percentage normalization
    assert "<pct>" in normalize_dynamic_text("Return 69.32%", rules=rules)
    assert "<pct>" in normalize_dynamic_text("+12.5%", rules=rules)
    assert "<pct>" in normalize_dynamic_text("-3.42 %", rules=rules)

    # Trend normalization
    assert "<trend>" in normalize_dynamic_text("Increased by 3.42%", rules=rules)
    assert "<trend>" in normalize_dynamic_text("Decreased by 1.20%", rules=rules)
    assert "<trend>" in normalize_dynamic_text("Gained by 0.5%", rules=rules)

    # Ordinal normalization
    assert "<n> of <m>" in normalize_dynamic_text("Stock 1 of 5", rules=rules)
    assert "<n> of <m>" in normalize_dynamic_text("Card 10 of 25", rules=rules)


def test_normalize_href():
    rules = get_rules()
    # Dynamic stock URLs collapse to wildcard prefix
    assert normalize_href("https://lemonn.co.in/stocks/bajfinance", rules) == "lemonn.co.in/stocks/*"
    assert normalize_href("/stocks/techm", rules) == "/stocks/*"
    assert normalize_href("/stocks/hikal?ref=home#top", rules) == "/stocks/*"

    # Static routes remain stable
    assert normalize_href("https://lemonn.co.in/about", rules) == "lemonn.co.in/about"
    assert normalize_href("/contact-us/", rules) == "/contact-us"


# ── 2. Card Fingerprint Equivalence Tests ────────────────────────────────────

def test_bajaj_finance_vs_tech_mahindra_card_same_fingerprint():
    """
    Run #1: BAJAJ FINANCE LIMITED, Price ₹948.30, Increased by 3.42%, view details
    Run #2: TECH MAHINDRA LIMITED, Price ₹1,650.00, Increased by 2.69%, view details
    Both should yield the identical stable group fingerprint!
    """
    # 3+ cards on the page to trigger repeating template normalization
    recs_run1 = [
        {
            "rule_id": "screen-reader-label-in-name-mismatch",
            "page_url": "https://lemonn.co.in/",
            "html": '<a href="/stocks/bajfinance" aria-label="BAJAJ FINANCE LIMITED, Price ₹948.30, Increased by 3.42%, view details"></a>'
        },
        {
            "rule_id": "screen-reader-label-in-name-mismatch",
            "page_url": "https://lemonn.co.in/",
            "html": '<a href="/stocks/infy" aria-label="INFOSYS LIMITED, Price ₹1,800.00, Increased by 1.15%, view details"></a>'
        },
        {
            "rule_id": "screen-reader-label-in-name-mismatch",
            "page_url": "https://lemonn.co.in/",
            "html": '<a href="/stocks/tcs" aria-label="TATA CONSULTANCY SERVICES, Price ₹4,200.00, Decreased by 0.50%, view details"></a>'
        }
    ]

    recs_run2 = [
        {
            "rule_id": "screen-reader-label-in-name-mismatch",
            "page_url": "https://lemonn.co.in/",
            "html": '<a href="/stocks/techm" aria-label="TECH MAHINDRA LIMITED, Price ₹1,650.00, Increased by 2.69%, view details"></a>'
        },
        {
            "rule_id": "screen-reader-label-in-name-mismatch",
            "page_url": "https://lemonn.co.in/",
            "html": '<a href="/stocks/wipro" aria-label="WIPRO LIMITED, Price ₹550.00, Increased by 0.85%, view details"></a>'
        },
        {
            "rule_id": "screen-reader-label-in-name-mismatch",
            "page_url": "https://lemonn.co.in/",
            "html": '<a href="/stocks/hcltech" aria-label="HCL TECHNOLOGIES, Price ₹1,720.00, Decreased by 0.30%, view details"></a>'
        }
    ]

    fps1 = fingerprint_batch(recs_run1)
    fps2 = fingerprint_batch(recs_run2)

    # All cards in both runs normalize to the same entity template and same stable group fp
    assert fps1[0].dynamic is True
    assert fps2[0].dynamic is True
    assert fps1[0].fp == fps2[0].fp


def test_ordinal_stock_carousel_same_fingerprint():
    """
    Run #1: Stock 1 of 5: ANTONY WASTE HANDLING CELL LIMITED, Return 69.32%, view details
    Run #2: Stock 1 of 5: HIKAL LIMITED, Return 79.14%, view details
    Both should yield the identical stable group fingerprint.
    """
    rec1 = {
        "rule_id": "screen-reader-label-in-name-mismatch",
        "page_url": "https://lemonn.co.in/",
        "html": '<a href="/stocks/antony" aria-label="Stock 1 of 5: ANTONY WASTE HANDLING CELL LIMITED, Return 69.32%, view details"></a>'
    }
    rec2 = {
        "rule_id": "screen-reader-label-in-name-mismatch",
        "page_url": "https://lemonn.co.in/",
        "html": '<a href="/stocks/hikal" aria-label="Stock 1 of 5: HIKAL LIMITED, Return 79.14%, view details"></a>'
    }

    res1 = fingerprint_batch([rec1])[0]
    res2 = fingerprint_batch([rec2])[0]

    assert res1.dynamic is True
    assert res2.dynamic is True
    assert res1.fp == res2.fp


# ── 3. Group Matching Count Semantics ─────────────────────────────────────────

def test_group_matching_counts():
    # 3 items vs 3 items -> all matched, 0 new, 0 fixed
    p_items = [MatchItem(ref=f"prev-{i}", fp="fp-group-1", dynamic=True, order=i) for i in range(3)]
    c_items = [MatchItem(ref=f"cur-{i}", fp="fp-group-1", dynamic=True, order=i) for i in range(3)]

    res = match_groups(p_items, c_items)
    assert len(res.pairs) == 3
    assert len(res.new) == 0
    assert len(res.unmatched_prev) == 0
    assert res.dynamic_groups_matched == 1

    # 3 items vs 5 items (2 extra cards added) -> 3 matched, 2 new, 0 fixed
    c_items_5 = [MatchItem(ref=f"cur-{i}", fp="fp-group-1", dynamic=True, order=i) for i in range(5)]
    res2 = match_groups(p_items, c_items_5)
    assert len(res2.pairs) == 3
    assert len(res2.new) == 2
    assert len(res2.unmatched_prev) == 0

    # 5 items vs 3 items (2 cards removed) -> 3 matched, 0 new, 2 fixed
    p_items_5 = [MatchItem(ref=f"prev-{i}", fp="fp-group-1", dynamic=True, order=i) for i in range(5)]
    res3 = match_groups(p_items_5, c_items)
    assert len(res3.pairs) == 3
    assert len(res3.new) == 0
    assert len(res3.unmatched_prev) == 2


# ── 4. Reconciler Integration Lifecycle with Dynamic Cards ───────────────────

def test_reconciler_dynamic_cards_lifecycle(db_session, test_project):
    """
    Simulates Run 1 with 3 ticker cards, then Run 2 with 3 different ticker cards
    (different stock names, prices, percent changes).
    Verifies that defects_new == 0, defects_fixed == 0, defects_open == 3,
    and dynamic_groups_matched == 1.
    """
    proj_id = test_project.id
    target_url = "https://lemonn.co.in/"

    tc_run1 = [
        {
            "rule_id": "screen-reader-label-in-name-mismatch",
            "page_url": target_url,
            "html_snippet": '<a href="/stocks/bajfinance" aria-label="BAJAJ FINANCE LIMITED, Price ₹948.30, Increased by 3.42%, view details"></a>',
            "criteria": "2.5.3 Label in Name",
            "severity": "Moderate",
        },
        {
            "rule_id": "screen-reader-label-in-name-mismatch",
            "page_url": target_url,
            "html_snippet": '<a href="/stocks/infy" aria-label="INFOSYS LIMITED, Price ₹1,800.00, Increased by 1.15%, view details"></a>',
            "criteria": "2.5.3 Label in Name",
            "severity": "Moderate",
        },
        {
            "rule_id": "screen-reader-label-in-name-mismatch",
            "page_url": target_url,
            "html_snippet": '<a href="/stocks/tcs" aria-label="TATA CONSULTANCY SERVICES, Price ₹4,200.00, Decreased by 0.50%, view details"></a>',
            "criteria": "2.5.3 Label in Name",
            "severity": "Moderate",
        }
    ]

    sess1 = _create_mock_session(db_session, proj_id, 1, target_url)
    res1 = reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess1.id,
        scanned_pages=[{"url": target_url, "status": "completed"}],
        fail_testcases=tc_run1
    )
    db_session.commit()
    assert res1["defects_new"] == 3

    # Run 2: Completely different stocks and prices
    tc_run2 = [
        {
            "rule_id": "screen-reader-label-in-name-mismatch",
            "page_url": target_url,
            "html_snippet": '<a href="/stocks/techm" aria-label="TECH MAHINDRA LIMITED, Price ₹1,650.00, Increased by 2.69%, view details"></a>',
            "criteria": "2.5.3 Label in Name",
            "severity": "Moderate",
        },
        {
            "rule_id": "screen-reader-label-in-name-mismatch",
            "page_url": target_url,
            "html_snippet": '<a href="/stocks/wipro" aria-label="WIPRO LIMITED, Price ₹550.00, Increased by 0.85%, view details"></a>',
            "criteria": "2.5.3 Label in Name",
            "severity": "Moderate",
        },
        {
            "rule_id": "screen-reader-label-in-name-mismatch",
            "page_url": target_url,
            "html_snippet": '<a href="/stocks/hcltech" aria-label="HCL TECHNOLOGIES, Price ₹1,720.00, Decreased by 0.30%, view details"></a>',
            "criteria": "2.5.3 Label in Name",
            "severity": "Moderate",
        }
    ]

    sess2 = _create_mock_session(db_session, proj_id, 2, target_url)
    res2 = reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess2.id,
        scanned_pages=[{"url": target_url, "status": "completed"}],
        fail_testcases=tc_run2
    )
    db_session.commit()

    # CRITICAL CHECK: 0 false new, 0 false fixed, 3 still open
    assert res2["defects_new"] == 0
    assert res2["defects_fixed"] == 0
    assert res2["defects_open"] == 3
    assert res2["dynamic_groups_matched"] >= 1


# ── 5. Genuine New and Genuine Fixed Detection ────────────────────────────────

def test_genuine_new_and_fixed_defects_detected(db_session, test_project):
    """
    Verifies that while dynamic cards are matched, genuine new defects are still
    flagged as New, and fixed defects are flagged as Fixed.
    """
    proj_id = test_project.id
    target_url = "https://lemonn.co.in/"

    # Run 1: 1 button missing name, 1 image missing alt
    tc_run1 = [
        {
            "rule_id": "button-name",
            "page_url": target_url,
            "html_snippet": '<button id="btn1"></button>',
            "criteria": "4.1.2 Name, Role, Value",
            "severity": "Critical",
        },
        {
            "rule_id": "image-alt",
            "page_url": target_url,
            "html_snippet": '<img src="/banner1.jpg">',
            "criteria": "1.1.1 Non-text Content",
            "severity": "Major",
        }
    ]

    sess1 = _create_mock_session(db_session, proj_id, 1, target_url)
    reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess1.id,
        scanned_pages=[{"url": target_url, "status": "completed"}],
        fail_testcases=tc_run1
    )
    db_session.commit()

    # Run 2:
    # - button-name is STILL present
    # - image-alt is FIXED (absent)
    # - link-name is genuinely NEW
    tc_run2 = [
        {
            "rule_id": "button-name",
            "page_url": target_url,
            "html_snippet": '<button id="btn1"></button>',
            "criteria": "4.1.2 Name, Role, Value",
            "severity": "Critical",
        },
        {
            "rule_id": "link-name",
            "page_url": target_url,
            "html_snippet": '<a href="/promo"></a>',
            "criteria": "2.4.4 Link Purpose",
            "severity": "Moderate",
        }
    ]

    sess2 = _create_mock_session(db_session, proj_id, 2, target_url)
    res2 = reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess2.id,
        scanned_pages=[{"url": target_url, "status": "completed"}],
        fail_testcases=tc_run2
    )
    db_session.commit()

    assert res2["defects_open"] == 1       # button-name still open
    assert res2["defects_fixed"] == 1      # image-alt fixed
    assert res2["defects_new"] == 1        # link-name genuinely new


# ── 6. Real Report Replay (task-7d21dd46af75 vs task-9a3e706a0aac) ───────────

def test_real_reports_replay():
    """
    Replays the real lemonn.co.in Run #1 and Run #2 testcase reports.
    Verifies:
      - 0 ticker/recommendation card defects flagged as New
      - 0 ticker/recommendation card defects flagged as Fixed
      - aria-prohibited-attr (DEF-0001..DEF-0007) all 7 matched as Still Open
      - dynamic_groups_matched > 0
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage"))
    r1_files = glob.glob(os.path.join(base_dir, "**", "testcase_report_task-7d21dd46af75.json"), recursive=True)
    r2_files = glob.glob(os.path.join(base_dir, "**", "testcase_report_task-9a3e706a0aac.json"), recursive=True)

    if not r1_files or not r2_files:
        pytest.skip("Real testcase report storage files not found; skipping storage replay test.")

    with open(r1_files[0], encoding="utf-8") as f:
        r1_fails = [t for t in json.load(f) if t.get("status") == "FAIL"]
    with open(r2_files[0], encoding="utf-8") as f:
        r2_fails = [t for t in json.load(f) if t.get("status") == "FAIL"]

    CARD_PATTERN = re.compile(r"(Price \u20b9|Stock \d of \d)")

    # Prepare batches
    recs1 = [{"rule_id": t["rule_id"], "html": t["html_snippet"], "page_url": t["page_url"], "criteria": t["criteria"]} for t in r1_fails]
    recs2 = [{"rule_id": t["rule_id"], "html": t["html_snippet"], "page_url": t["page_url"], "criteria": t["criteria"]} for t in r2_fails]

    fps1 = fingerprint_batch(recs1)
    fps2 = fingerprint_batch(recs2)

    items1 = [MatchItem(ref=t, fp=r.fp, dynamic=r.dynamic, order=i) for i, (t, r) in enumerate(zip(r1_fails, fps1))]
    items2 = [MatchItem(ref=t, fp=r.fp, dynamic=r.dynamic, order=i) for i, (t, r) in enumerate(zip(r2_fails, fps2))]

    result = match_groups(items1, items2)

    card_new = [i for i in result.new if CARD_PATTERN.search(i.ref.get("html_snippet", ""))]
    card_fixed = [i for i in result.unmatched_prev if CARD_PATTERN.search(i.ref.get("html_snippet", ""))]

    # 17 ticker/recommendation card "New" defects drop to 0!
    assert len(card_new) == 0, f"Expected 0 card new defects, got {len(card_new)}"
    assert len(card_fixed) == 0, f"Expected 0 card fixed defects, got {len(card_fixed)}"

    # DEF-0001..DEF-0007 (aria-prohibited-attr) matched 7 of 7 as Still Open
    aria_prohibited_pairs = [p for p in result.pairs if p[1].ref.get("rule_id") == "aria-prohibited-attr"]
    assert len(aria_prohibited_pairs) == 7

    assert result.dynamic_groups_matched >= 5


# ── 7. Excel Report Dynamic Groups Cell Verification ──────────────────────────

def test_excel_report_dynamic_groups_summary():
    """
    Verifies that Regression Summary sheet in Excel contains:
    'Dynamic-content groups matched: <n>'
    """
    summary_data = {
        "project_name": "Lemonn Regression Test",
        "target_url": "https://lemonn.co.in",
        "total_rules": 25,
        "total_testcases": 100,
        "passed": 80,
        "failed": 20,
        "compliance_score": 80.0
    }
    regression_info = {
        "run_number": 2,
        "previous_run_number": 1,
        "defects_new": 0,
        "defects_open": 20,
        "defects_fixed": 0,
        "defects_reopened": 0,
        "defects_not_retested": 0,
        "dynamic_groups_matched": 7
    }

    excel_bytes = generate_excel_report({
        "summary": summary_data,
        "regression": regression_info,
        "testcases": []
    })

    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes), data_only=True)
    assert "Regression Summary" in wb.sheetnames
    sheet = wb["Regression Summary"]

    found = False
    for row in range(1, 20):
        val = sheet.cell(row=row, column=1).value
        if val and "Dynamic-content groups matched:" in str(val):
            assert "7" in str(val)
            found = True
            break

    assert found, "Did not find 'Dynamic-content groups matched: 7' in Regression Summary sheet"
