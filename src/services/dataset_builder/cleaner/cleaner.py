import re

import re


def clean_question(question: str) -> str:

    question = question.strip()

    patterns = [
        r'^Q\s*\d+[\.\:\-\s]*',      # Q 46.
        r'^Q\d+[\.\:\-\s]*',         # Q46.
        r'^\d+[\.\:\-\s]*',          # 46.
        r'^Question\s*\d+[\.\:\-\s]*'
    ]

    for pattern in patterns:
        question = re.sub(
            pattern,
            '',
            question,
            flags=re.IGNORECASE
        )

    return question.strip()