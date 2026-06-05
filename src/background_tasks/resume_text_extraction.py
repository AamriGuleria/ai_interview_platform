import logging
from sqlalchemy import select
from models.Interview import Interview
from services.minio_client import MinioClient
from core.config import config
from database.session_manager import db_manager
import tempfile
import fitz
import os
import re

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]",
        "",
        text
    )
    # text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
    return text.strip()

def extract_text(file_path: str):
    text = ""
    pdf = fitz.open(file_path)
    pages = [page.get_text() for page in pdf]
    pdf.close()
    return "\n".join(pages)

def extract_resume_context(interview_id: int):
    file_name = None
    try:
        with db_manager.sync_session_scope() as db:
            interview = db.execute(
                select(Interview).where(Interview.id == interview_id)
            ).scalars().one_or_none()
            if not interview:
                raise Exception("Interview not found")
            resume_url = interview.resume_url
            file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            file_name = file.name
            file.close()
            minio_service = MinioClient()
            minio_service.download_file(
                config.bucket_name,
                resume_url,
                file_name
            )
            text = extract_text(file_name)
            cleaned_text = clean_text(text)
            interview.resume_text = cleaned_text
            db.add(interview)
    except Exception as e:
        logger.error(f"Failed to extract resume context due to: {e}")
        raise
    finally:
        if file_name is not None and os.path.exists(file_name):
            os.remove(file_name)