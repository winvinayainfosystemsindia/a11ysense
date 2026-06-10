import os
import sys
import logging

# Add parent directory to sys.path so we can import from backend root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.database.connection import get_session_local
from common.database.models import User, Organization, Project
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def make_super_admin():
    session = get_session_local()()
    try:
        # 1. Resolve or create default organization
        org = session.query(Organization).filter_by(name="A11ySense Enterprise").first()
        if not org:
            org = Organization(name="A11ySense Enterprise")
            session.add(org)
            session.flush()
            logger.info("Default Organization created.")

        # 2. Check if default project exists
        project = session.query(Project).filter_by(name="Default Project", organization_id=org.id).first()
        if not project:
            project = Project(name="Default Project", organization_id=org.id)
            session.add(project)
            logger.info("Default Project created.")

        # 3. Find or create admin@a11y.com user and make them Superadmin
        user = session.query(User).filter_by(email="admin@a11y.com").first()
        if user:
            user.role = "Superadmin"
            user.hashed_password = hash_password("password")
            logger.info("Updated existing user admin@a11y.com to Superadmin role and reset password.")
        else:
            user = User(
                email="admin@a11y.com",
                hashed_password=hash_password("password"),
                role="Superadmin",
                organization_id=org.id
            )
            session.add(user)
            logger.info("Created new user admin@a11y.com with Superadmin role and password 'password'.")

        session.commit()
        print("SUCCESS: admin@a11y.com is now a Superadmin with password 'password'.")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to create/update super admin: {str(e)}")
        print(f"ERROR: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    make_super_admin()
