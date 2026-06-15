import requests
from logging import getLogger

logger = getLogger(__name__)

def fetch_page(url: str) -> str:

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()
    logger.info(f"The content that we get {url} is {response.text[:100]}")
    return response.text