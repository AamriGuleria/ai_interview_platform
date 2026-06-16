from apscheduler.schedulers.background import BackgroundScheduler
from logging import getLogger
from services.question_enrichment_service import QuestionEnrichmentService
from database.session_manager import db_manager
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = getLogger(__name__)

scheduler = BackgroundScheduler()

def trigger_enrichment_job():
    try:
        with db_manager.sync_session_scope() as db:
            enrichment_service = QuestionEnrichmentService(db)
            enrichment_service.enrich_question_bank()
    except Exception as e:
        logger.error(f"Error during enrichment job: {e}")

scheduler.add_job(
    trigger_enrichment_job,
    trigger="interval",
    minutes=10
)

if __name__ == "__main__":
    logger.info("Starting enrichment scheduler manually...")
    trigger_enrichment_job()
    logger.info("Initial enrichment run complete. Scheduler will re-run every 10 minutes. Press CTRL+C to stop.")
    scheduler.start()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()
        logger.info("Scheduler stopped.")