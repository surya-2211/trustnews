import feedparser


RSS_FEEDS = [
    "https://www.nasa.gov/rss/dyn/breaking_news.rss",
]


def fetch_rss_feed(feed_url: str):

    feed = feedparser.parse(feed_url)

    articles = []

    for entry in feed.entries:

        title = entry.get("title", "").strip()

        summary = entry.get(
            "summary",
            entry.get("description", "")
        )

        url = entry.get("link", "").strip()

        published = entry.get(
            "published",
            ""
        )

        if not title or not url:
            continue

        articles.append({
            "title": title,
            "summary": summary,
            "url": url,
            "published": published,
            "source": feed.feed.get(
                "title",
                feed_url
            )
        })

    return articles


def fetch_all_feeds():

    all_articles = []

    for feed_url in RSS_FEEDS:

        try:

            articles = fetch_rss_feed(feed_url)

            all_articles.extend(articles)

        except Exception as e:

            print(
                f"Failed to fetch {feed_url}: {e}"
            )

    return all_articles