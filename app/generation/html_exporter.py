from pathlib import Path
from datetime import datetime
import re


GENERATED_ARTICLES_DIR = Path("generated_articles")

def create_safe_filename(text: str) -> str:
    """
    Convert the query into a safe filename.
    """

    text = text.lower().strip()

    text = re.sub(
        r"[^a-z0-9]+",
        "_",
        text
    )

    text = text.strip("_")

    if not text:
        text = "article"

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return f"{text}_{timestamp}.html"


def save_article_html(
    query: str,
    html: str
) -> str:

    GENERATED_ARTICLES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = create_safe_filename(query)

    file_path = (
        GENERATED_ARTICLES_DIR / filename
    )

    file_path.write_text(
        html,
        encoding="utf-8"
    )

    return str(file_path)