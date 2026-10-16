import sys
import os
import uuid
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from common.database.connection import get_session_local
from common.database.models import Organization, Project, AuditSession, Defect, DefectEvent, SuccessCriterion
from app.core.regression.reconciler import (
    normalize_url,
    compute_fingerprint,
    compute_loose_fingerprint,
    reconciler,
)
from app.repository.project_repo import project_repo
from app.repository.defect_repo import defect_repo
from app.repository.session_repo import audit_session_repo


# ── 1. Unit Tests for URL & Fingerprint Normalization ───────────────────────────

def test_normalize_url():
    assert normalize_url("https://example.com/login/") == "example.com/login"
    assert normalize_url("http://example.com/login?tab=1#section") == "example.com/login"
    assert normalize_url("HTTPS://EXAMPLE.COM/ABOUT") == "example.com/about"
    assert normalize_url("") == ""
    assert normalize_url("https://example.com:443/test") == "example.com:443/test"


def test_compute_fingerprint():
    fp1 = compute_fingerprint("button-name", "<button class='btn'>Click</button>", "https://example.com/page")
    # Same content with varied spacing or query param in URL
    fp2 = compute_fingerprint("button-name", "<button   class='btn'>Click</button>", "https://example.com/page?ref=home")
    assert fp1 == fp2
    assert len(fp1) == 40  # SHA-1 hex digest length


def test_compute_loose_fingerprint():
    lfp1 = compute_loose_fingerprint("button-name", "https://example.com/checkout", "Submit Payment Button")
    lfp2 = compute_loose_fingerprint("button-name", "http://example.com/checkout/", "submit payment button")
    assert lfp1 == lfp2
    assert len(lfp1) == 40


# ── 2. Integration Tests with Database State Machine ───────────────────────────

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
    """Creates a temporary Project for regression testing."""
    org = db_session.query(Organization).first()
    if not org:
        org = Organization(name="Test Regression Org")
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)

    proj = Project(
        name=f"Test Regression Project {uuid.uuid4().hex[:6]}",
        base_url="https://regression.example.com",
        project_type="web_page",
        status="active",
        organization_id=org.id
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


def _create_mock_session(db, project_id: uuid.UUID, run_number: int, url: str = "https://regression.example.com") -> AuditSession:
    proj = db.query(Project).filter(Project.id == project_id).first()
    sess = AuditSession(
        task_id=f"test-run-{run_number}-{uuid.uuid4().hex[:6]}",
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


def test_reconciler_full_lifecycle(db_session, test_project):
    """
    Validates complete defect lifecycle:
    Run 1 (Baseline): Defect detected -> Status 'New'
    Run 2 (Regression): Defect still present -> Status 'Open'
    Run 3 (Regression): Defect absent on scanned page -> Status 'Fixed' (clean_runs = 1)
    Run 4 (Regression): Defect absent again -> Status 'Closed' (clean_runs = 2)
    Run 5 (Regression): Defect re-appears -> Status 'Reopened' (reopen_count = 1)
    """
    proj_id = test_project.id
    target_url = "https://regression.example.com/checkout"
    scanned_pages = [{"url": target_url, "status": "completed"}]

    tc_fail = {
        "rule_id": "button-name",
        "page_url": target_url,
        "html_snippet": "<button id='pay-btn'></button>",
        "criteria": "4.1.2 Name, Role, Value",
        "testcase_name": "Button missing accessible name",
        "severity": "Serious",
        "steps_to_reproduce": "Inspect pay-btn button",
        "code_before": "<button id='pay-btn'></button>",
        "code_after": "<button id='pay-btn'>Pay Now</button>",
        "fix_steps": ["Add accessible text inside button"],
        "verify_steps": ["Ensure screen reader reads Pay Now"]
    }

    # ── RUN 1: Baseline ────────────────────────────────────────────────────────
    sess1 = _create_mock_session(db_session, proj_id, 1, target_url)
    res1 = reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess1.id,
        scanned_pages=scanned_pages,
        fail_testcases=[tc_fail],
        is_run_successful=True
    )
    db_session.commit()

    assert res1["defects_new"] == 1
    assert res1["defects_open"] == 0
    assert res1["defects_fixed"] == 0

    # Verify defect in DB
    defects = db_session.query(Defect).filter(Defect.project_id == proj_id).all()
    assert len(defects) == 1
    d = defects[0]
    assert d.status == "New"
    assert d.times_seen == 1
    assert d.first_seen_run_id == sess1.id
    assert d.last_seen_run_id == sess1.id
    assert d.reopen_count == 0

    # Verify detected event
    events = defect_repo.get_defect_timeline(db_session, d.id)
    assert len(events) == 1
    assert events[0].event == "detected"
    assert events[0].to_status == "New"

    # ── RUN 2: Regression (Still Present) ──────────────────────────────────────
    sess2 = _create_mock_session(db_session, proj_id, 2, target_url)
    res2 = reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess2.id,
        scanned_pages=scanned_pages,
        fail_testcases=[tc_fail],
        is_run_successful=True
    )
    db_session.commit()

    assert res2["defects_new"] == 0
    assert res2["defects_open"] == 1
    db_session.refresh(d)
    assert d.status == "Open"
    assert d.times_seen == 2
    assert d.last_seen_run_id == sess2.id

    events = defect_repo.get_defect_timeline(db_session, d.id)
    assert len(events) == 2
    assert events[-1].event == "still_open"
    assert events[-1].to_status == "Open"

    # ── RUN 3: Fixed (Defect absent on scanned page) ───────────────────────────
    sess3 = _create_mock_session(db_session, proj_id, 3, target_url)
    res3 = reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess3.id,
        scanned_pages=scanned_pages,
        fail_testcases=[],  # Passed / absent
        is_run_successful=True
    )
    db_session.commit()

    assert res3["defects_fixed"] == 1
    db_session.refresh(d)
    assert d.status == "Fixed"
    assert d.fixed_in_run_id == sess3.id
    assert d.clean_runs_count == 1

    events = defect_repo.get_defect_timeline(db_session, d.id)
    assert len(events) == 3
    assert events[-1].event == "auto_fixed"
    assert events[-1].to_status == "Fixed"

    # ── RUN 4: Closed (Second clean run) ───────────────────────────────────────
    sess4 = _create_mock_session(db_session, proj_id, 4, target_url)
    res4 = reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess4.id,
        scanned_pages=scanned_pages,
        fail_testcases=[],  # Still clean
        is_run_successful=True
    )
    db_session.commit()

    db_session.refresh(d)
    assert d.status == "Closed"
    assert d.clean_runs_count == 2

    events = defect_repo.get_defect_timeline(db_session, d.id)
    assert len(events) == 4
    assert events[-1].event == "closed"
    assert events[-1].to_status == "Closed"

    # ── RUN 5: Reopened (Defect reappears) ─────────────────────────────────────
    sess5 = _create_mock_session(db_session, proj_id, 5, target_url)
    res5 = reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess5.id,
        scanned_pages=scanned_pages,
        fail_testcases=[tc_fail],  # Defect returned!
        is_run_successful=True
    )
    db_session.commit()

    assert res5["defects_reopened"] == 1
    db_session.refresh(d)
    assert d.status == "Reopened"
    assert d.reopen_count == 1
    assert d.times_seen == 3
    assert d.clean_runs_count == 0

    events = defect_repo.get_defect_timeline(db_session, d.id)
    assert len(events) == 5
    assert events[-1].event == "reopened"
    assert events[-1].to_status == "Reopened"


def test_reconciler_safety_rules(db_session, test_project):
    """
    Safety Rules Verification:
    1. Page containing defect was not scanned -> counted in 'defects_not_retested', NOT auto-fixed!
    2. Audit run stopped / failed -> no auto-fix applied, counted in 'defects_not_retested'.
    """
    proj_id = test_project.id
    target_url = "https://regression.example.com/contact"
    other_url = "https://regression.example.com/faq"

    # Create baseline with defect on /contact
    sess1 = _create_mock_session(db_session, proj_id, 1, target_url)
    tc = {
        "rule_id": "image-alt",
        "page_url": target_url,
        "html_snippet": "<img src='logo.jpg'>",
        "criteria": "1.1.1 Non-text Content",
        "testcase_name": "Image missing alt",
        "severity": "Serious"
    }
    reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess1.id,
        scanned_pages=[{"url": target_url, "status": "completed"}],
        fail_testcases=[tc]
    )
    db_session.commit()

    d = db_session.query(Defect).filter(Defect.project_id == proj_id).first()
    assert d.status == "New"

    # Run 2: Only scanned /faq (contact was NOT scanned)
    sess2 = _create_mock_session(db_session, proj_id, 2, other_url)
    res2 = reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess2.id,
        scanned_pages=[{"url": other_url, "status": "completed"}],
        fail_testcases=[],
        is_run_successful=True
    )
    db_session.commit()

    assert res2["defects_fixed"] == 0
    assert res2["defects_not_retested"] == 1
    db_session.refresh(d)
    assert d.status == "New"  # Preserved!

    # Run 3: /contact scanned, but is_run_successful is False (e.g. runner crashed/stopped)
    sess3 = _create_mock_session(db_session, proj_id, 3, target_url)
    res3 = reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess3.id,
        scanned_pages=[{"url": target_url, "status": "failed"}],
        fail_testcases=[],
        is_run_successful=False
    )
    db_session.commit()

    assert res3["defects_fixed"] == 0
    assert res3["defects_not_retested"] == 1
    db_session.refresh(d)
    assert d.status == "New"  # Still preserved!


def test_reconciler_suppressed_defects(db_session, test_project):
    """
    Verifies that defects marked as WontFix or FalsePositive are not overridden
    back to Open or Fixed by subsequent runs.
    """
    proj_id = test_project.id
    target_url = "https://regression.example.com/settings"
    sess1 = _create_mock_session(db_session, proj_id, 1, target_url)

    tc = {
        "rule_id": "color-contrast",
        "page_url": target_url,
        "html_snippet": "<span class='hint'>Note</span>",
        "criteria": "1.4.3 Contrast (Minimum)",
        "testcase_name": "Low contrast on disabled text",
        "severity": "Minor"
    }
    reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess1.id,
        scanned_pages=[{"url": target_url, "status": "completed"}],
        fail_testcases=[tc]
    )
    db_session.commit()

    d = db_session.query(Defect).filter(Defect.project_id == proj_id).first()
    # User manually overrides status to 'FalsePositive'
    d.status = "FalsePositive"
    db_session.commit()

    # Next run detects the same issue
    sess2 = _create_mock_session(db_session, proj_id, 2, target_url)
    reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess2.id,
        scanned_pages=[{"url": target_url, "status": "completed"}],
        fail_testcases=[tc]
    )
    db_session.commit()

    db_session.refresh(d)
    assert d.status == "FalsePositive"

    events = defect_repo.get_defect_timeline(db_session, d.id)
    assert events[-1].event == "still_suppressed"


def test_reconciler_loose_matching_and_severity_update(db_session, test_project):
    """
    Verifies loose fingerprint fallback when snippet has changed slightly,
    and updates severity with event logging.
    """
    proj_id = test_project.id
    target_url = "https://regression.example.com/profile"
    sess1 = _create_mock_session(db_session, proj_id, 1, target_url)

    tc1 = {
        "rule_id": "link-name",
        "page_url": target_url,
        "html_snippet": "<a href='/edit' data-v1='1'></a>",
        "criteria": "2.4.4 Link Purpose (In Context)",
        "testcase_name": "Edit Profile Link",
        "severity": "Moderate"
    }
    reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess1.id,
        scanned_pages=[{"url": target_url, "status": "completed"}],
        fail_testcases=[tc1]
    )
    db_session.commit()

    d = db_session.query(Defect).filter(Defect.project_id == proj_id).first()
    orig_fp = d.fingerprint
    assert d.severity == "Moderate"

    # Run 2: Exact HTML snippet changed from data-v1='1' to data-v2='2',
    # and severity is updated to 'Critical'
    tc2 = {
        "rule_id": "link-name",
        "page_url": target_url,
        "html_snippet": "<a href='/edit' data-v2='2'></a>",
        "criteria": "2.4.4 Link Purpose (In Context)",
        "testcase_name": "Edit Profile Link",
        "severity": "Critical"
    }
    sess2 = _create_mock_session(db_session, proj_id, 2, target_url)
    res2 = reconciler.reconcile_run(
        db=db_session,
        project_id=proj_id,
        session_id=sess2.id,
        scanned_pages=[{"url": target_url, "status": "completed"}],
        fail_testcases=[tc2]
    )
    db_session.commit()

    assert res2["defects_new"] == 0  # Matched existing defect via loose fingerprint!
    assert res2["defects_open"] == 1

    db_session.refresh(d)
    assert d.status == "Open"
    assert d.severity == "Critical"
    assert d.fingerprint != orig_fp  # Fingerprint updated to latest markup!

    events = defect_repo.get_defect_timeline(db_session, d.id)
    # Check that severity_changed event was added
    event_names = [e.event for e in events]
    assert "severity_changed" in event_names
