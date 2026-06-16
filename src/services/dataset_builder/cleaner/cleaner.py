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

def clean_answer(answer: str) -> str:
    if not answer:
        return ""

    answer = answer.strip()
    answer = re.sub(
        r"^(Answer\s*:\s*)",
        "",
        answer,
        flags=re.IGNORECASE
    )

    answer = re.sub(
        r"^(Explanation\s*:\s*)",
        "",
        answer,
        flags=re.IGNORECASE
    )

    answer = re.sub(
        r"^(Ans\s*:\s*)",
        "",
        answer,
        flags=re.IGNORECASE
    )

    # Remove excessive spaces
    answer = re.sub(r"\s+", " ", answer)

    return answer.strip()