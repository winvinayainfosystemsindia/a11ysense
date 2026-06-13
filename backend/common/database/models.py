import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Float, Integer, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    plan_tier = Column(String, default="free")  # free, pro, enterprise
    credit_balance = Column(Integer, default=500)  # Seed new orgs with 500 demo credits!
    billing_status = Column(String, default="active")  # active, past_due, canceled
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    pay_as_you_go_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="Viewer")  # Admin, Auditor, Viewer
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="users")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="projects")
    audit_sessions = relationship("AuditSession", back_populates="project", cascade="all, delete-orphan")
    credentials = relationship("PageCredential", back_populates="project", cascade="all, delete-orphan")

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_hash = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="api_keys")
    organization = relationship("Organization")

class AuditSession(Base):
    __tablename__ = "audit_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String, unique=True, nullable=False, index=True)
    url = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, nullable=False)  # processing, crawling, auditing, completed, failed
    summary = Column(JSON, nullable=True)  # accessibility_score, passes, total violations breakdown
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    depth = Column(Integer, default=1, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization")
    project = relationship("Project", back_populates="audit_sessions")
    violations = relationship("ViolationRecord", back_populates="session", cascade="all, delete-orphan")

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
    """
    Single source of truth for live audit progress.
    Replaces the in-memory ACTIVE_TASKS dict — survives service restarts
    and works correctly under multiple agent instances.
    """
    __tablename__ = "audit_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String, unique=True, nullable=False, index=True)
    url = Column(String, nullable=False)
    status = Column(String, nullable=False, default="processing")
    # Live page progress counters
    pages_found = Column(Integer, default=0)
    pages_completed = Column(Integer, default=0)
    pages_total = Column(Integer, default=0)
    # JSON arrays of URL strings
    pages_scanned = Column(JSON, default=list)
    pages_discovered = Column(JSON, default=list)
    pages_depth_map = Column(JSON, nullable=True)  # {url: depth} mapping from crawler
    depth = Column(Integer, default=1, nullable=True)
    # Completion payload
    report_url = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    token_usage = Column(JSON, nullable=True)
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Integer, nullable=False)  # positive = load, negative = consumption
    transaction_type = Column(String, nullable=False)  # "purchase", "usage", "grant", "refund"
    description = Column(String, nullable=True)
    reference_id = Column(String, nullable=True)  # task_id of audit
    timestamp = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization")


class PageCredential(Base):
    __tablename__ = "page_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    label = Column(String, nullable=False)
    login_url = Column(String, nullable=False)
    url_pattern = Column(String, nullable=False)
    auth_type = Column(String, default="form")  # form, cookie, bearer_token
    username_field = Column(String, default="[name=username]", nullable=True)
    password_field = Column(String, default="[name=password]", nullable=True)
    submit_selector = Column(String, default="button[type=submit]", nullable=True)
    username_encrypted = Column(Text, nullable=True)
    password_encrypted = Column(Text, nullable=True)
    extra_fields_encrypted = Column(Text, nullable=True)  # Fernet encrypted JSON
    post_login_url_pattern = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="credentials")
    organization = relationship("Organization")


