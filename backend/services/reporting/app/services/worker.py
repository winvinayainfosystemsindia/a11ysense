import asyncio
import time
import logging
import threading

from app.schemas.audit import AuditResult
from app.services.report_service import report_service
from app.repository.report_repo import report_repo

logger = logging.getLogger(__name__)

class ReportingWorker:
    def start(self) -> None:
        """
        Spawns the background ReportingWorker thread.
        """
        thread = threading.Thread(target=self._run_loop, daemon=True)
        thread.start()
        logger.info("Reporting Worker: Background thread spawned successfully.")

    def _run_loop(self) -> None:
        """
        Blocking thread loop that polls the 'audit:analyzed' Redis stream.
        """
        time.sleep(2.0)
        logger.info("Reporting Worker: Loop started. Listening to stream 'audit:analyzed'...")
        
        # Listen to new events created after startup
        last_id = "$"
        
        while True:
            try:
                events = report_repo.read_analyzed_events(last_id=last_id, block_ms=2000)
                if not events:
                    time.sleep(1.0)
                    continue
                for msg_id, payload in events:
                    last_id = msg_id
                    
                    task_id = payload.get("task_id")
                    result_dict = payload.get("result")
                    if not task_id or not result_dict:
                        continue
                    
                    logger.info(f"Reporting Worker: Received finished audit data for task {task_id}")
                    
                    # Compile report asynchronously in a dedicated loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = AuditResult(**result_dict)
                        loop.run_until_complete(report_service.create_audit_report(result, task_id))
                        logger.info(f"Reporting Worker: Successfully generated Allure report for task {task_id}")
                    except Exception as report_err:
                        logger.error(f"Reporting Worker: Report generation failed for task {task_id}: {str(report_err)}")
                    finally:
                        loop.close()
                        
            except Exception as e:
                logger.error(f"Reporting Worker: Loop error: {str(e)}")
                time.sleep(5.0)

reporting_worker = ReportingWorker()
