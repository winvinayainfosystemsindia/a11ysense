import os
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD", "12345")
server = os.getenv("POSTGRES_SERVER", "localhost")
port = os.getenv("POSTGRES_PORT", "5432")
db = os.getenv("POSTGRES_DB", "a11ysense")

# Fetch DATABASE_URL from env or build from POSTGRES_* vars
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql://{user}:{password}@{server}:{port}/{db}"
)

# Connect engine with pool configuration
engine = None
SessionLocal = None

def get_engine():
    global engine
    if engine is None:
        # Retry connection to PostgreSQL (in case of startup delay)
        retries = 5
        while retries > 0:
            try:
                engine = create_engine(
                    DATABASE_URL,
                    pool_pre_ping=True,
                    pool_size=10,
                    max_overflow=20
                )
                # Test connection
                with engine.connect() as conn:
                    logger.info("Successfully connected to PostgreSQL database.")
                break
            except Exception as e:
                retries -= 1
                logger.warning(f"Failed to connect to PostgreSQL (DATABASE_URL={DATABASE_URL}). Retrying in 3 seconds... Error: {str(e)}")
                if retries == 0:
                    logger.error("Could not establish database connection after multiple retries.")
                    raise e
                time.sleep(3)
    return engine

def get_session_local():
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return SessionLocal

def get_db():
    """
    FastAPI dependency that yields a database session and guarantees closure.
    """
    db_session = get_session_local()()
    try:
        yield db_session
    finally:
        db_session.close()
