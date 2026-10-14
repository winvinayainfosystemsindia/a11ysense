import logging
from sqlalchemy import select, text
from common.database.connection import get_engine, get_session_local
from common.database.models import Base, Organization, User, Project, SuccessCriterion
from common.constants import A11YSENSE_AUDIT_SCOPE, A11YSENSE_MANUAL_REVIEW_CRITERIA
from common.constants.sc_catalog import SC_CATALOG
from common.constants.rule_catalog import principle_for
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def seed_success_criteria(session):
    """
    Seeds all 50 WCAG success criteria into the success_criteria table idempotently.
    """
    all_criteria = list(A11YSENSE_AUDIT_SCOPE) + list(A11YSENSE_MANUAL_REVIEW_CRITERIA)
    seen_codes = set()

    for item in all_criteria:
        code = item["code"]
        if code in seen_codes:
            continue
        seen_codes.add(code)

        existing = session.query(SuccessCriterion).filter_by(sc_code=code).first()
        sc_info = SC_CATALOG.get(code, {})
        principle = principle_for(code)

        if not existing:
            sc = SuccessCriterion(
                sc_code=code,
                name=item["name"],
                level=item.get("level", "A"),
                principle=principle,
                wcag_version="2.2",
                what_we_check=sc_info.get("what_we_check", ""),
                expected=sc_info.get("expected", ""),
                manual_steps=sc_info.get("manual_steps", [])
            )
            session.add(sc)
        else:
            # Update fields if needed
            existing.name = item["name"]
            existing.level = item.get("level", existing.level)
            existing.principle = principle
            existing.what_we_check = sc_info.get("what_we_check", existing.what_we_check)
            existing.expected = sc_info.get("expected", existing.expected)
            existing.manual_steps = sc_info.get("manual_steps", existing.manual_steps)

    logger.info(f"Seeded/verified {len(seen_codes)} WCAG success criteria.")


def init_db():
    """
    Creates all database tables in PostgreSQL, applies auto-schema column additions,
    and seeds initial organization/user/project/success_criteria records.
    """
    logger.info("Initializing database schema...")
    engine = get_engine()
    
    # 1. Create tables
    try:
        Base.metadata.create_all(bind=engine)
        
        # Ensure project_type and base_url columns exist on pre-existing projects table
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_type VARCHAR DEFAULT 'web_page';"))
            conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS base_url VARCHAR;"))
            conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS description TEXT;"))
            conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'active';"))
            conn.commit()
            
        logger.info("Database tables created/verified successfully.")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise e

    # 2. Seed initial data
    session = get_session_local()()
    try:
        # Check if default organization exists
        org = session.query(Organization).filter_by(name="A11ySense Enterprise").first()
        if not org:
            org = Organization(name="A11ySense Enterprise")
            session.add(org)
            session.flush()
            logger.info("Default Organization created.")

        # Check if default project exists
        project = session.query(Project).filter_by(name="Default Project", organization_id=org.id).first()
        if not project:
            project = Project(
                name="Default Project",
                project_type="web_page",
                status="active",
                organization_id=org.id
            )
            session.add(project)
            logger.info("Default Project created.")

        # Check if admin user exists
        admin = session.query(User).filter_by(email="admin@a11y.com").first()
        if not admin:
            admin = User(
                email="admin@a11y.com",
                hashed_password=hash_password("password"),
                role="Admin",
                organization_id=org.id
            )
            session.add(admin)
            logger.info("Default Admin User created (admin@a11y.com / password).")

        # Check if auditor user exists
        auditor = session.query(User).filter_by(email="auditor@a11y.com").first()
        if not auditor:
            auditor = User(
                email="auditor@a11y.com",
                hashed_password=hash_password("password"),
                role="Auditor",
                organization_id=org.id
            )
            session.add(auditor)
            logger.info("Default Auditor User created (auditor@a11y.com / password).")

        # Check if viewer user exists
        viewer = session.query(User).filter_by(email="viewer@a11y.com").first()
        if not viewer:
            viewer = User(
                email="viewer@a11y.com",
                hashed_password=hash_password("password"),
                role="Viewer",
                organization_id=org.id
            )
            session.add(viewer)
            logger.info("Default Viewer User created (viewer@a11y.com / password).")

        # Seed success criteria
        seed_success_criteria(session)

        session.commit()
        logger.info("Database seeding completed.")
    except Exception as seed_err:
        session.rollback()
        logger.error(f"Failed to seed initial database records: {str(seed_err)}")
    finally:
        session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
