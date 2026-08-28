from bs4 import BeautifulSoup
import re


def clean_text(text: str) -> str:

    if not text:
        return ""

    soup = BeautifulSoup(
        text,
        "html.parser"
    )

    text = soup.get_text(
        separator=" "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def clean_article(article):

    title = clean_text(
        article["title"]
    )

    summary = clean_text(
        article["summary"]
    )

    combined_text = f"{title}. {summary}"

    return {
        **article,
        "title": title,
        "summary": summary,
        "text": combined_text
    }