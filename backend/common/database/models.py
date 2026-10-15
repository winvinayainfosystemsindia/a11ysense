import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Float, Integer, Text, Boolean,
    UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    plan_tier = Column(String, default="free", nullable=True)
    credit_balance = Column(Integer, default=0, nullable=True)
    billing_status = Column(String, default="active", nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    pay_as_you_go_enabled = Column(Boolean, default=False, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    credit_transactions = relationship("CreditTransaction", back_populates="organization", cascade="all, delete-orphan")


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Integer, nullable=False)
    transaction_type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    reference_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="credit_transactions")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="Viewer")  # Admin, Auditor, Viewer
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="users")


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)
    project_type = Column(String, default="web_page", nullable=False)  # web_page or web_application
    base_url = Column(String, nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_org_project_name"),
    )

    organization = relationship("Organization", back_populates="projects")
    audit_sessions = relationship("AuditSession", back_populates="project", cascade="all, delete-orphan")
    credentials = relationship("PageCredential", back_populates="project", cascade="all, delete-orphan")
    defects = relationship("Defect", back_populates="project", cascade="all, delete-orphan")
    testcases = relationship("TestCase", back_populates="project", cascade="all, delete-orphan")


class AuditSession(Base):
    __tablename__ = "audit_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String, unique=True, nullable=False, index=True)
    url = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, nullable=False)  # processing, crawling, auditing, completed, failed, stopped
    summary = Column(JSON, nullable=True)  # accessibility_score, passes, total violations breakdown
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    depth = Column(Integer, default=1, nullable=True)

    # Run sequencing & regression tracking
    run_number = Column(Integer, nullable=True)
    run_type = Column(String, default="baseline", nullable=False)  # baseline or regression
    previous_run_id = Column(UUID(as_uuid=True), ForeignKey("audit_sessions.id", ondelete="SET NULL"), nullable=True)
    scope_fingerprint = Column(String, nullable=True)

    # Testcase counters
    total_testcases = Column(Integer, default=0, nullable=False)
    fail_count = Column("fail", Integer, default=0, nullable=False)
    pass_count = Column("pass", Integer, default=0, nullable=False)
    na_count = Column("na", Integer, default=0, nullable=False)
    manual_count = Column("manual", Integer, default=0, nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Defect reconciliation counters
    defects_new = Column(Integer, default=0, nullable=False)
    defects_fixed = Column(Integer, default=0, nullable=False)
    defects_reopened = Column(Integer, default=0, nullable=False)
    defects_open = Column(Integer, default=0, nullable=False)
    defects_not_retested = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization")
    project = relationship("Project", back_populates="audit_sessions")
    previous_run = relationship("AuditSession", remote_side=[id])
    violations = relationship("ViolationRecord", back_populates="session", cascade="all, delete-orphan")
    pages = relationship("AuditPage", back_populates="session", cascade="all, delete-orphan")
    testcases = relationship("TestCase", back_populates="session", cascade="all, delete-orphan")
    run_criterion_results = relationship("RunCriterionResult", back_populates="session", cascade="all, delete-orphan")
    defect_events = relationship("DefectEvent", back_populates="session")
    report_artifacts = relationship("ReportArtifact", back_populates="session", cascade="all, delete-orphan")


class AuditPage(Base):
    __tablename__ = "audit_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_session_id = Column(UUID(as_uuid=True), ForeignKey("audit_sessions.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    normalized_url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    depth = Column(Integer, default=1, nullable=False)
    status = Column(String, default="scanned", nullable=False)  # scanned, error, skipped
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("audit_session_id", "url", name="uq_session_page_url"),
    )

    session = relationship("AuditSession", back_populates="pages")
    testcases = relationship("TestCase", back_populates="page", cascade="all, delete-orphan")


class SuccessCriterion(Base):
    __tablename__ = "success_criteria"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sc_code = Column(String, unique=True, nullable=False, index=True)  # e.g. "1.1.1"
    name = Column(String, nullable=False)
    level = Column(String, nullable=False)  # A, AA, AAA
    principle = Column(String, nullable=False)  # Perceivable, Operable, Understandable, Robust
    wcag_version = Column(String, default="2.2", nullable=False)
    what_we_check = Column(Text, nullable=True)
    expected = Column(Text, nullable=True)
    manual_steps = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Defect(Base):
    __tablename__ = "defects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    defect_code = Column(String, nullable=False)  # DEF-0001
    fingerprint = Column(String, nullable=False, index=True)
    loose_fingerprint = Column(String, nullable=True, index=True)

    rule_id = Column(String, nullable=False)
    success_criterion_id = Column(UUID(as_uuid=True), ForeignKey("success_criteria.id", ondelete="SET NULL"), nullable=True)
    page_url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    severity = Column(String, default="Moderate", nullable=False)

    # Remediation fields
    fix_steps = Column(JSON, nullable=True)
    code_before = Column(Text, nullable=True)
    code_after = Column(Text, nullable=True)
    verify_steps = Column(JSON, nullable=True)
    false_positive_note = Column(Text, nullable=True)

    # Lifecycle tracking
    status = Column(String, default="New", nullable=False, index=True)  # New, Open, Fixed, Reopened, Closed, WontFix, FalsePositive
    first_seen_run_id = Column(UUID(as_uuid=True), ForeignKey("audit_sessions.id", ondelete="SET NULL"), nullable=True)
    last_seen_run_id = Column(UUID(as_uuid=True), ForeignKey("audit_sessions.id", ondelete="SET NULL"), nullable=True)
    fixed_in_run_id = Column(UUID(as_uuid=True), ForeignKey("audit_sessions.id", ondelete="SET NULL"), nullable=True)
    reopen_count = Column(Integer, default=0, nullable=False)
    times_seen = Column(Integer, default=1, nullable=False)
    clean_runs_count = Column(Integer, default=0, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Human / management fields
    assignee_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    suppressed_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("project_id", "fingerprint", name="uq_project_defect_fingerprint"),
        UniqueConstraint("project_id", "defect_code", name="uq_project_defect_code"),
        Index("ix_defects_project_status", "project_id", "status"),
    )

    project = relationship("Project", back_populates="defects")
    success_criterion = relationship("SuccessCriterion")
    first_seen_run = relationship("AuditSession", foreign_keys=[first_seen_run_id])
    last_seen_run = relationship("AuditSession", foreign_keys=[last_seen_run_id])
    fixed_in_run = relationship("AuditSession", foreign_keys=[fixed_in_run_id])
    assignee = relationship("User", foreign_keys=[assignee_user_id])
    events = relationship("DefectEvent", back_populates="defect", cascade="all, delete-orphan", order_by="DefectEvent.created_at.asc()")
    testcases = relationship("TestCase", back_populates="defect")


class DefectEvent(Base):
    __tablename__ = "defect_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    defect_id = Column(UUID(as_uuid=True), ForeignKey("defects.id", ondelete="CASCADE"), nullable=False, index=True)
    audit_session_id = Column(UUID(as_uuid=True), ForeignKey("audit_sessions.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event = Column(String, nullable=False)  # detected, still_open, auto_fixed, reopened, closed, status_changed, commented, severity_changed, still_suppressed
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    defect = relationship("Defect", back_populates="events")
    session = relationship("AuditSession", back_populates="defect_events")
    user = relationship("User")


class TestCase(Base):
    __tablename__ = "testcases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_session_id = Column(UUID(as_uuid=True), ForeignKey("audit_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    audit_page_id = Column(UUID(as_uuid=True), ForeignKey("audit_pages.id", ondelete="SET NULL"), nullable=True)
    success_criterion_id = Column(UUID(as_uuid=True), ForeignKey("success_criteria.id", ondelete="SET NULL"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    defect_id = Column(UUID(as_uuid=True), ForeignKey("defects.id", ondelete="SET NULL"), nullable=True, index=True)

    testcase_code = Column(String, nullable=False)  # TC-0001
    display_name = Column(String, nullable=True)  # TC-HOME-0001
    rule_id = Column(String, nullable=False)
    testcase_name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # PASS, FAIL, NOT_APPLICABLE, MANUAL_REVIEW
    severity = Column(String, default="N/A", nullable=False)

    description = Column(Text, nullable=True)
    expected_result = Column(Text, nullable=True)
    actual_result = Column(Text, nullable=True)
    steps_to_reproduce = Column(Text, nullable=True)
    business_impact = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    html_snippet = Column(Text, nullable=True)
    selector = Column(Text, nullable=True)
    screenshot_path = Column(String, nullable=True)
    repeat_count = Column(Integer, default=1, nullable=False)
    remarks = Column(Text, nullable=True)
    help_url = Column(String, nullable=True)
    page_url = Column(String, nullable=True)
    page_title = Column(String, nullable=True)
    fingerprint = Column(String, nullable=True, index=True)

    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    refined_by = Column(String, nullable=True)

    # Authoritative WCAG facts captured at audit time
    wcag_criteria = Column(String, nullable=True)
    wcag_level = Column(String, nullable=True)
    wcag_principle = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_testcases_session_status", "audit_session_id", "status"),
        Index("ix_testcases_project_fingerprint", "project_id", "fingerprint"),
    )

    project = relationship("Project", back_populates="testcases")
    session = relationship("AuditSession", back_populates="testcases")
    page = relationship("AuditPage", back_populates="testcases")
    success_criterion = relationship("SuccessCriterion")
    defect = relationship("Defect", back_populates="testcases")


class LLMUsage(Base):
    """One row per LLM API call made during an audit (used for per-provider cost reporting)."""
    __tablename__ = "llm_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False)  # claude, gemini, groq
    model = Column(String, nullable=False)
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    cached = Column(Boolean, default=False, nullable=False)
    cost_usd = Column(Float, default=0.0, nullable=False)
    category = Column(String(50), default="other", nullable=False, index=True)  # defect, testcase, other
    created_at = Column(DateTime, default=datetime.utcnow)


class RunCriterionResult(Base):
    __tablename__ = "run_criterion_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_session_id = Column(UUID(as_uuid=True), ForeignKey("audit_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    success_criterion_id = Column(UUID(as_uuid=True), ForeignKey("success_criteria.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False)  # PASS, FAIL, NOT_APPLICABLE, MANUAL_REVIEW
    pass_count = Column(Integer, default=0, nullable=False)
    fail_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("audit_session_id", "success_criterion_id", name="uq_session_criterion"),
    )

    session = relationship("AuditSession", back_populates="run_criterion_results")
    success_criterion = relationship("SuccessCriterion")


class ReportArtifact(Base):
    __tablename__ = "report_artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_session_id = Column(UUID(as_uuid=True), ForeignKey("audit_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String, nullable=False)  # excel, pdf, json
    file_path = Column(String, nullable=False)
    report_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("AuditSession", back_populates="report_artifacts")


class ViolationRecord(Base):
    __tablename__ = "violations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    audit_session_id = Column(UUID(as_uuid=True), ForeignKey("audit_sessions.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(String, nullable=False)
    impact = Column(String, nullable=True)
    description = Column(String, nullable=False)
    help = Column(String, nullable=False)
    help_url = Column(String, nullable=True)
    nodes = Column(JSON, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("AuditSession", back_populates="violations")


class ErrorEventRecord(Base):
    __tablename__ = "error_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    correlation_id = Column(String, nullable=True)
    service_name = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    context_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditProgress(Base):
    __tablename__ = "audit_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String, unique=True, nullable=False, index=True)
    url = Column(String, nullable=False)
    status = Column(String, nullable=False, default="processing")
    pages_found = Column(Integer, default=0)
    pages_completed = Column(Integer, default=0)
    pages_total = Column(Integer, default=0)
    pages_scanned = Column(JSON, default=list)
    pages_discovered = Column(JSON, default=list)
    pages_depth_map = Column(JSON, nullable=True)
    depth = Column(Integer, default=1, nullable=True)
    report_url = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    token_usage = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrawlProgress(Base):
    __tablename__ = "crawl_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crawl_task_id = Column(String, unique=True, nullable=False, index=True)
    url = Column(String, nullable=False)
    scan_target = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    pages_discovered = Column(JSON, default=list)
    pages_depth_map = Column(JSON, nullable=True)
    url_to_menu_text = Column(JSON, nullable=True)
    sitemaps_found = Column(JSON, default=list)
    unauth_pages_discovered = Column(JSON, default=list)
    auth_pages_discovered = Column(JSON, default=list)
    storage_state = Column(JSON, nullable=True)
    auth_headers = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PageCredential(Base):
    __tablename__ = "page_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    label = Column(String, nullable=False)
    login_url = Column(String, nullable=False)
    url_pattern = Column(String, nullable=False)
    auth_type = Column(String, default="form")
    username_field = Column(String, default="[name=username]", nullable=True)
    password_field = Column(String, default="[name=password]", nullable=True)
    submit_selector = Column(String, default="button[type=submit]", nullable=True)
    username_encrypted = Column(Text, nullable=True)
    password_encrypted = Column(Text, nullable=True)
    extra_fields_encrypted = Column(Text, nullable=True)
    post_login_url_pattern = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="credentials")
    organization = relationship("Organization")


class EstimationRecord(Base):
    __tablename__ = "estimations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, default="Website Audit Estimation")
    base_url = Column(String, nullable=False)
    mode = Column(String, default="discover", nullable=False)
    status = Column(String, default="completed", nullable=False)
    hourly_rate = Column(Float, default=40.0, nullable=False)
    platform_fee = Column(Float, default=10.0, nullable=False)
    profit_margin_pct = Column(Float, default=30.0, nullable=False)
    total_pages = Column(Integer, default=0, nullable=False)
    simple_pages = Column(Integer, default=0, nullable=False)
    medium_pages = Column(Integer, default=0, nullable=False)
    complex_pages = Column(Integer, default=0, nullable=False)
    total_manual_hours = Column(Float, default=0.0, nullable=False)
    total_manual_cost = Column(Float, default=0.0, nullable=False)
    total_api_cost = Column(Float, default=0.0, nullable=False)
    total_platform_cost = Column(Float, default=0.0, nullable=False)
    total_base_cost = Column(Float, default=0.0, nullable=False)
    total_profit_margin = Column(Float, default=0.0, nullable=False)
    total_quote = Column(Float, default=0.0, nullable=False)
    pages = Column(JSON, nullable=False)
    summary = Column(JSON, nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship("Organization")
