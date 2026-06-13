from bs4 import BeautifulSoup
from models.Interview import Question
import re

from services.dataset_builder.constants import CATEGORY_MAPPING 

def parse_gfg(
    html: str,
    domain: str,
    url: str
):
    soup = BeautifulSoup(
        html,
        "lxml"
    )
    results = []

    headings = soup.find_all(
        ["h2", "h3"]
    )
    for heading in headings:

        text = heading.get_text(
            strip=True
        )

        if "?" not in text:
            continue

        answer_parts = []

        current = heading.next_sibling

        while current:

            if getattr(
                current,
                "name",
                None
            ) in ["h2", "h3"]:
                break

            if hasattr(
                current,
                "get_text"
            ):
                answer_parts.append(
                    current.get_text(
                        " ",
                        strip=True
                    )
                )

            current = current.next_sibling

        answer = "\n".join(
            answer_parts
        )
        text = re.sub(r'^\d+\.\s*', '', text)
        results.append(
            {
                "question_text": text,
                "expected_answer": answer,
                "source": "gfg",
                "difficulty":"unknown",
                "category": CATEGORY_MAPPING.get(domain.lower(), domain),
                "question_type":"Technical",
            }
        )
        # results.append(
        #     Question(
        #         question_text=text,
        #         expected_answer=answer,
        #         difficulty="unknown",
        #         # skills={},
        #         category=domain,
        #         question_type="Technical",
        #         source="gfg"
        #     )
        # )

    return results