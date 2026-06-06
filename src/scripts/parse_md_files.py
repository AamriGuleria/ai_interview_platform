import os
from logging import getLogger
import logging
from pathlib import Path
import re
from database.session_manager import db_manager
from models.Interview import Question
from scripts.general import clean_markdown, store_questions_in_bank

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = getLogger(__name__)

MD_FOLDER_PATH = (
    Path.home()
    / "Documents"
    / "interview_datasets"
    / "raw_interview_qa"
)

def read_md_files():
    try:
        all_files = []

        md_files = list(
            MD_FOLDER_PATH.glob("*.md")
        )

        logger.info(
            f"Found {len(md_files)} markdown files"
        )

        for file in md_files:
            try:
                with open(
                    file,
                    "r",
                    encoding="utf-8"
                ) as f:
                    content = f.read()

                all_files.append(
                    {
                        "file_name": file.name,
                        "content": content
                    }
                )

                logger.info(
                    f"Successfully read {file.name}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to read {file.name}: {e}"
                )

        return all_files

    except Exception as e:
        logger.error(
            f"Could not read markdown files due to: {e}"
        )
        raise

def parse_questions(content: str):
    questions = []

    pattern = re.compile(
        r"## .*?Q\d+:\s*(.*?)\n\n### .*?Answer\s*\n\n(.*?)(?=\n## |\Z)",
        re.DOTALL
    )

    matches = pattern.findall(content)

    for question, answer in matches:
        questions.append(
            {
                "question_text": question.strip(),
                "expected_answer": answer.strip(),
                "source": "github_rag_repo"
            }
        )

    return questions

def extract_all_questions():
    files = read_md_files()

    all_questions = []

    for file in files:
        extracted_questions = parse_questions(
            file["content"]
        )

        logger.info(
            f"{file['file_name']} -> "
            f"{len(extracted_questions)} questions"
        )

        all_questions.extend(
            extracted_questions
        )

    # Deduplicate by question text
    unique_questions = {}

    for question in all_questions:
        unique_questions[
            question["question_text"]
        ] = question

    return list(
        unique_questions.values()
    )

# def store_questions_in_bank(questions: list):
#     try:
#         db_question_entries = []
#         for question in questions:
#             logger.info(
#                 f"Storing question: "
#                 f"{question['question_text'][:50]}..."
#             )
#             question_entry = Question(
#                 question_text=clean_markdown(question["question_text"]),
#                 expected_answer=clean_markdown(question["expected_answer"]),
#                 source=question["source"],
#                 category="general",
#                 difficulty="unknown",
#                 question_type="technical",
#                 skills=[]
#             )
#             db_question_entries.append(question_entry)

#         with db_manager.sync_session_scope() as session:
#             session.add_all(db_question_entries)
#             session.commit()
#             logger.info(
#                 f"Successfully stored "
#                 f"{len(db_question_entries)} questions"
#             )
#     except Exception as e:
#         logger.error(
#             f"Failed to store questions in bank: {e}"
#         )
#         raise
if __name__ == "__main__":
    questions = extract_all_questions()
    store_questions_in_bank(questions)
    for question in questions[:5]:
        logger.info("\n" + "=" * 80)
        logger.info(
            f"Question: "
            f"{question['question_text']}"
        )
        logger.info(
            f"Answer Preview: "
            f"{question['expected_answer'][:200]}"
        )