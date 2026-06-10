import os
import asyncio
import sys
from dotenv import load_dotenv

# Fix for Playwright/Subprocess on Windows
# Set policy at module level to ensure it runs as soon as this config is imported
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def setup_logging():
    """
    Sets up dynamic backend logging to a text file with a 7-day retention policy
    using TimedRotatingFileHandler.
    """
    import logging
    from logging.handlers import TimedRotatingFileHandler
    
    # 1. Determine service name
    service_name = None
    env_app_name = os.getenv("APP_NAME")
    if env_app_name and env_app_name not in ["A11ySense AI", "A11ySense"]:
        service_name = env_app_name

    if not service_name:
        cwd = os.path.abspath(os.getcwd())
        parts = cwd.replace("\\", "/").split("/")
        for part in ["gateway", "agent", "reporting", "crawler", "analyzer", "llm"]:
            if part in parts:
                service_name = part
                break
    if not service_name:
        service_name = env_app_name or "backend"

    # 2. Setup logs directory under backend/storage/logs/
    base = os.getenv("STORAGE_BASE_PATH")
    if not base:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage"))
    logs_dir = os.path.join(base, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    log_file_path = os.path.join(logs_dir, f"{service_name}.txt")
    
    # 3. Create root logger handler
    root_logger = logging.getLogger()
    
    # Prevent duplicate handlers if setup is called multiple times
    if not any(isinstance(h, TimedRotatingFileHandler) for h in root_logger.handlers):
        # Timed rotating file handler: rotates daily (when='D'), every 1 day, keeps 7 backups (backupCount=7)
        file_handler = TimedRotatingFileHandler(
            log_file_path,
            when='D',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        
        # Plain text formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        
        # Ensure the root logger level is at least INFO to pass through messages
        if root_logger.level > logging.INFO:
            root_logger.setLevel(logging.INFO)


def setup_environment():
    """
    Loads environment variables from the appropriate .env file based on APP_ENV.

    Priority:
    1. .env.[APP_ENV] if APP_ENV is set
    2. .env (default)
    """
    app_env = os.getenv("APP_ENV", "dev")
    env_file = f".env.{app_env}"
    
    # Search for the env file in the root directory
    # Assuming the services are run from their own directories or project root
    root_env_path = os.path.join(os.path.dirname(__file__), "../../", env_file)
    default_env_path = os.path.join(os.path.dirname(__file__), "../../.env")

    if os.path.exists(root_env_path):
        load_dotenv(root_env_path)
    elif os.path.exists(default_env_path):
        load_dotenv(default_env_path)
    
    # Configure unified logging
    try:
        setup_logging()
    except Exception as e:
        print(f"Failed to setup backend logging: {e}")

    return app_env


def get_storage_path(sub_path: str = "") -> str:
    """
    Returns an absolute configured storage path, creating directories if missing.
    Resolves using the STORAGE_BASE_PATH env var, falling back to backend 'storage' directory.
    """
    base = os.getenv("STORAGE_BASE_PATH")
    if not base:
        # Fallback to backend/storage sibling relative to backend/common
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage"))
    full_path = os.path.join(base, sub_path)
    os.makedirs(full_path, exist_ok=True)
    return full_path


def get_audit_storage_path(task_id: str, org_id: str = None, proj_id: str = None, create: bool = True) -> str:
    """
    Returns the organization- and project-specific audit directory under backend/storage.
    Structure: backend/storage/org_<org_id>/proj_<proj_id>/audit_<task_id>/
    If org_id or proj_id are not supplied, they are resolved from the database for the given task_id.
    """
    # 1. Resolve org_id and proj_id if not provided
    if not org_id or not proj_id:
        try:
            from common.database.connection import get_session_local
            from common.database.models import AuditSession
            db = get_session_local()()
            try:
                session_rec = db.query(AuditSession).filter_by(task_id=task_id).first()
                if session_rec:
                    if not org_id and session_rec.organization_id:
                        org_id = str(session_rec.organization_id)
                    if not proj_id and session_rec.project_id:
                        proj_id = str(session_rec.project_id)
            finally:
                db.close()
        except Exception:
            # Database might not be initialized or module not importable in some context
            pass

    # 2. Fallbacks if still unresolved
    org_str = f"org_{org_id}" if org_id else "org_default"
    proj_str = f"proj_{proj_id}" if proj_id else "proj_default"
    audit_str = f"audit_{task_id}"

    # 3. Build full path under backend/storage
    base = os.getenv("STORAGE_BASE_PATH")
    if not base:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "../storage"))
    
    full_path = os.path.join(base, org_str, proj_str, audit_str)
    if create:
        os.makedirs(full_path, exist_ok=True)
    return full_path


def get_cors_origins() -> list[str]:
    """
    Returns a list of allowed CORS origins from the CORS_ORIGINS env var.
    Defaults to allowing standard local React development servers.
    """
    origins = os.getenv("CORS_ORIGINS") or os.getenv("BACKEND_CORS_ORIGINS")
    if not origins:
        return [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000"
        ]
    return [orig.strip() for orig in origins.split(",") if orig.strip()]


def get_service_url(env_name: str, docker_default: str, host_default: str) -> str:
    """
    Dynamically returns a service URL.
    Checks env variable first.
    If not set, checks if running inside Docker (Linux /.dockerenv)
    or if the host is resolvable. If not, falls back to host_default (localhost).
    """
    val = os.getenv(env_name)
    if val:
        return val
        
    # Check if /.dockerenv exists (Linux Docker containers)
    if os.path.exists("/.dockerenv"):
        return docker_default
        
    # Standard fallback for local development outside Docker
    return host_default
