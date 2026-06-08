import pandas as pd
from pathlib import Path

from database import session_manager
from models.Interview import Question


CSV_PATH = (
    Path.home()
    / "Documents"
    / "interview_datasets"
    / "Software Questions.csv"
)
df = pd.read_csv(CSV_PATH)

required_columns = [
    "Question",
    "Answer",
    "Category",
    "Difficulty"
]
for col in required_columns:
    if col not in df.columns:
        raise ValueError(
            f"Missing column: {col}"
        )
    
questions = []

for _, row in df.iterrows():
    question_text = str(row["Question"]).strip()

    if not question_text:
        continue
    questions.append(
        {
            "question_text": row["Question"],
            "expected_answer": row["Answer"],
            "category": row["Category"],
            "difficulty": row["Difficulty"],
            "source": "csv_dataset"
        }
    )
unique_questions = {}

for q in questions:

    key = (
        q["question_text"]
        .strip()
        .lower()
    )
    unique_questions[key] = q

questions = list(
    unique_questions.values()
)
db_entries = []

for q in questions:

    db_entries.append(
        Question(
            question_text=q["question_text"],
            expected_answer=q["expected_answer"],
            category=q["category"],
            difficulty=q["difficulty"],
            source=q["source"]
        )
    )

with session_manager.sync_session_scope() as session:

    session.bulk_save_objects(
        db_entries
    )

    session.commit()