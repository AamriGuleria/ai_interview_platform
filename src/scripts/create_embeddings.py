import logging
from database.session_manager import db_manager
from services.embeddings import create_question_embeddings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

if __name__ == "__main__":
    with db_manager.sync_session_scope() as db:
        create_question_embeddings(db)
