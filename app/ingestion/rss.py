import feedparser


RSS_FEEDS = [
    # NASA
    "https://www.nasa.gov/rss/dyn/breaking_news.rss",

    # NASA Earthdata
    "https://www.earthdata.nasa.gov/rss.xml",

    # ScienceDaily - Top Science
    "https://www.sciencedaily.com/rss/top/science.xml",

    # Ars Technica - Science
    "https://feeds.arstechnica.com/arstechnica/science",

    # MIT News
    "https://news.mit.edu/rss/feed",
]


def fetch_rss_feed(feed_url: str):

    feed = feedparser.parse(feed_url)

    articles = []

    # Check if feed parsing failed
    if feed.bozo and not feed.entries:
        raise Exception(
            f"Could not parse RSS feed: {feed_url}"
        )

    # Get source name from RSS feed
    source = feed.feed.get(
        "title",
        feed_url
    )

    for entry in feed.entries:

        title = entry.get(
            "title",
            ""
        ).strip()

        summary = entry.get(
            "summary",
            entry.get(
                "description",
                ""
            )
        )

        url = entry.get(
            "link",
            ""
        ).strip()

        published = entry.get(
            "published",
            entry.get(
                "updated",
                ""
            )
        )

        # Skip incomplete entries
        if not title or not url:
            continue

        articles.append({

            "title": title,

            "summary": summary,

            "url": url,

            "published": published,

            "source": source
        })

    return articles


def fetch_all_feeds():

    all_articles = []

    for feed_url in RSS_FEEDS:

        try:

            articles = fetch_rss_feed(
                feed_url
            )

            print(
                f"Fetched {len(articles)} articles "
                f"from {feed_url}"
            )

            all_articles.extend(
                articles
            )

        except Exception as e:

            print(
                f"Failed to fetch {feed_url}: {e}"
            )

    print(
        f"Total articles fetched: "
        f"{len(all_articles)}"
    )

    return all_articles