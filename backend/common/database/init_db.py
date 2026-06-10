import logging
from sqlalchemy import select
from common.database.connection import get_engine, get_session_local
from common.database.models import Base, Organization, User, Project
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def init_db():
    """
    Creates all database tables in PostgreSQL and seeds initial organization/user records.
    """
    logger.info("Initializing database schema...")
    engine = get_engine()
    
    # 1. Create tables
    try:
        Base.metadata.create_all(bind=engine)
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
            project = Project(name="Default Project", organization_id=org.id)
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
