from scripts.general import store_questions_in_bank
from services.dataset_builder.constants import DOMAIN_CONFIGURATION
from logging import getLogger
from services.dataset_builder.crawler.scrape_page import fetch_page
from services.dataset_builder.parser.gfg_parser import parse_gfg

logger = getLogger(__name__)


def run_scraper():
    try:
        all_questions = []
        for domain, urls in DOMAIN_CONFIGURATION.items():
            for url in urls:
                try:
                    html = fetch_page(url)
                    questions = parse_gfg(html, domain, url)
                    all_questions.extend(
                        questions
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to process {url} for domain {domain}: {e}"
                    )

        unique_questions = {}
        for question in all_questions:
            key = (
                question["question_text"]
                .strip()
                .lower()
            )
            unique_questions[key] = question

        store_questions_in_bank(
            list(unique_questions.values()),
            enrichement=False
        )
    except Exception as e:
        logger.error(
            f"Failed to run scraper: {e}"
        )
        raise

if __name__ == "__main__":
    run_scraper()