import os
import shutil
import time
import logging
import threading

logger = logging.getLogger(__name__)

def clean_old_audits(storage_base: str, max_age_days: int = 7) -> int:
    """
    Scans the storage directory and deletes audit folders older than max_age_days.
    Path structure: backend/storage/org_<org_id>/proj_<proj_id>/audit_<task_id>/
    """
    if not os.path.exists(storage_base):
        return 0

    now = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    deleted_count = 0

    try:
        # Loop through organization folders
        for org_dir in os.listdir(storage_base):
            org_path = os.path.join(storage_base, org_dir)
            if not os.path.isdir(org_path) or not org_dir.startswith("org_"):
                continue
            
            # Loop through project folders
            for proj_dir in os.listdir(org_path):
                proj_path = os.path.join(org_path, proj_dir)
                if not os.path.isdir(proj_path) or not proj_dir.startswith("proj_"):
                    continue
                
                # Loop through audit folders
                for audit_dir in os.listdir(proj_path):
                    audit_path = os.path.join(proj_path, audit_dir)
                    if not os.path.isdir(audit_path) or not audit_dir.startswith("audit_"):
                        continue
                    
                    # Check folder age
                    try:
                        mtime = os.path.getmtime(audit_path)
                        age = now - mtime
                        if age > max_age_seconds:
                            logger.info(f"Purging old audit directory: {audit_path} (age: {age / (24*3600):.1f} days)")
                            shutil.rmtree(audit_path)
                            deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error checking/deleting directory {audit_path}: {e}")
                        
        if deleted_count > 0:
            logger.info(f"Retention policy cleanup complete. Purged {deleted_count} audit directories.")
    except Exception as e:
        logger.error(f"Error walking storage base for cleanup: {e}")

    return deleted_count

def start_storage_cleanup_worker():
    """
    Spawns a background thread to run the retention policy cleanup daily.
    """
    def _run_cleanup_loop():
        # Lazy import get_storage_path to avoid circular imports at module level
        from common.config import get_storage_path
        
        logger.info("Storage Cleanup Worker: Starting background loop.")
        while True:
            try:
                base_storage = get_storage_path()
                logger.info("Storage Cleanup Worker: Running daily retention scan...")
                clean_old_audits(base_storage, max_age_days=7)
            except Exception as e:
                logger.error(f"Storage Cleanup Worker encountered error: {e}")
            
            # Sleep for 24 hours (86400 seconds) in 1-minute chunks to remain responsive
            # 24 hours * 60 minutes = 1440 cycles of 60 seconds
            for _ in range(1440):
                time.sleep(60)
                
    thread = threading.Thread(target=_run_cleanup_loop, name="storage_cleanup_worker", daemon=True)
    thread.start()
