from html import escape
from typing import Dict, List


# =========================================================
# TRUSTNEWS ARTICLE TEMPLATE
# Black & White Editorial UI
# =========================================================


def safe_text(value) -> str:
    """
    Safely convert a value to escaped HTML text.
    """
    if value is None:
        return ""

    return escape(str(value))


def safe_url(value) -> str:
    """
    Safely prepare a URL for use inside an href.
    """
    if not value:
        return "#"

    value = str(value).strip()

    if not (
        value.startswith("http://")
        or value.startswith("https://")
    ):
        return "#"

    return escape(value, quote=True)


def format_score(value) -> str:
    """
    Format relevance/reranking scores for display.
    """
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return "—"


def truncate_text(
    text: str,
    max_length: int = 260
) -> str:
    """
    Create a compact source preview.
    """
    if not text:
        return ""

    text = " ".join(str(text).split())

    if len(text) <= max_length:
        return text

    return text[:max_length].rstrip() + "…"


def build_source_card(
    source: Dict,
    index: int
) -> str:
    """
    Build a source card for the article sidebar.
    """

    title = safe_text(
        source.get(
            "title",
            "Untitled source"
        )
    )

    publisher = safe_text(
        source.get(
            "source",
            "Unknown source"
        )
    )

    url = safe_url(
        source.get(
            "url",
            ""
        )
    )

    preview = safe_text(
        truncate_text(
            source.get(
                "content",
                ""
            )
        )
    )

    rerank_score = format_score(
        source.get(
            "rerank_score"
        )
    )

    retrieval_score = format_score(
        source.get(
            "retrieval_score"
        )
    )

    return f"""
    <article class="source-card">

        <div class="source-card-top">

            <span class="source-number">
                {index:02d}
            </span>

            <span class="source-label">
                SOURCE
            </span>

        </div>

        <h3 class="source-title">
            {title}
        </h3>

        <div class="source-publisher">
            {publisher}
        </div>

        <p class="source-preview">
            {preview}
        </p>

        <div class="source-metrics">

            <div class="source-metric">

                <span class="metric-label">
                    RELEVANCE
                </span>

                <strong>
                    {rerank_score}
                </strong>

            </div>

            <div class="source-metric">

                <span class="metric-label">
                    RETRIEVAL
                </span>

                <strong>
                    {retrieval_score}
                </strong>

            </div>

        </div>

        <a
            class="source-link"
            href="{url}"
            target="_blank"
            rel="noopener noreferrer"
        >
            Read source
            <span aria-hidden="true">↗</span>
        </a>

    </article>
    """


def build_key_points(
    key_points: List[str]
) -> str:
    """
    Build the key-points block.
    """

    if not key_points:
        return ""

    items = []

    for point in key_points:

        if not point:
            continue

        items.append(
            f"""
            <li class="key-point">
                <span class="key-point-mark"></span>
                <span>
                    {safe_text(point)}
                </span>
            </li>
            """
        )

    if not items:
        return ""

    return f"""
    <section class="key-points">

        <div class="section-eyebrow">
            KEY POINTS
        </div>

        <h2>
            What matters
        </h2>

        <ul>
            {''.join(items)}
        </ul>

    </section>
    """


def build_article_sections(
    sections: List[Dict]
) -> str:
    """
    Build numbered article sections.
    """

    if not sections:
        return ""

    output = []

    section_number = 0

    for section in sections:

        if not isinstance(
            section,
            dict
        ):
            continue

        heading = section.get(
            "heading",
            ""
        )

        content = section.get(
            "content",
            ""
        )

        if not heading and not content:
            continue

        section_number += 1

        heading_html = safe_text(
            heading
        )

        content_html = safe_text(
            content
        )

        output.append(
            f"""
            <section
                class="article-section"
                id="section-{section_number}"
            >

                <div class="section-number">
                    {section_number:02d}
                </div>

                <div class="section-body">

                    <div class="section-eyebrow">
                        SECTION {section_number:02d}
                    </div>

                    <h2>
                        {heading_html}
                    </h2>

                    <div class="section-content">
                        {content_html}
                    </div>

                </div>

            </section>
            """
        )

    return "\n".join(output)


def build_source_list(
    sources: List[Dict]
) -> str:
    """
    Build the complete source list.
    """

    if not sources:
        return """
        <div class="empty-sources">
            No source information available.
        </div>
        """

    cards = []

    for index, source in enumerate(
        sources,
        start=1
    ):

        cards.append(
            build_source_card(
                source=source,
                index=index
            )
        )

    return "\n".join(cards)


def build_article_html(
    query: str,
    article: Dict,
    sources: List[Dict]
) -> str:
    """
    Build the complete TrustNews article HTML page.

    Parameters
    ----------
    query:
        Original user search query.

    article:
        Structured article returned by Gemini.

    sources:
        Retrieved evidence sources.
    """

    # =====================================================
    # ARTICLE DATA
    # =====================================================

    title = safe_text(
        article.get(
            "title",
            "TrustNews Article"
        )
    )

    introduction = safe_text(
        article.get(
            "introduction",
            ""
        )
    )

    conclusion = safe_text(
        article.get(
            "conclusion",
            ""
        )
    )

    clean_query = safe_text(
        query
    )

    sections = article.get(
        "sections",
        []
    )

    key_points = article.get(
        "key_points",
        []
    )

    source_count = len(
        sources
    )

    section_html = build_article_sections(
        sections
    )

    key_points_html = build_key_points(
        key_points
    )

    sources_html = build_source_list(
        sources
    )

    # =====================================================
    # COMPLETE HTML
    # =====================================================

    return f"""<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<meta
    name="description"
    content="{safe_text(query)} — TrustNews evidence-grounded news article."
>

<title>
    {title} — TrustNews
</title>


<style>

/* ========================================================
   RESET
   ======================================================== */

*,
*::before,
*::after {{
    box-sizing: border-box;
}}

html {{
    scroll-behavior: smooth;
}}

body {{
    margin: 0;
    padding: 0;

    background: #f5f5f5;

    color: #111111;

    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Helvetica,
        Arial,
        sans-serif;

    line-height: 1.7;

    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
}}

a {{
    color: inherit;
}}

button,
a {{
    -webkit-tap-highlight-color: transparent;
}}


/* ========================================================
   PAGE
   ======================================================== */

.page {{
    min-height: 100vh;
    background: #f5f5f5;
}}


/* ========================================================
   TOP NAVIGATION
   ======================================================== */

.topbar {{
    position: sticky;
    top: 0;
    z-index: 100;

    height: 68px;

    background: rgba(255, 255, 255, 0.96);

    border-bottom: 1px solid #d9d9d9;

    backdrop-filter: blur(12px);
}}

.topbar-inner {{
    width: min(
        1440px,
        calc(100% - 48px)
    );

    height: 100%;

    margin: 0 auto;

    display: flex;

    align-items: center;

    justify-content: space-between;
}}

.brand {{
    display: inline-flex;

    align-items: center;

    gap: 12px;

    text-decoration: none;
}}

.brand-mark {{
    width: 34px;
    height: 34px;

    background: #111111;

    color: #ffffff;

    display: grid;

    place-items: center;

    font-size: 15px;

    font-weight: 900;

    letter-spacing: -0.04em;
}}

.brand-name {{
    font-size: 19px;

    font-weight: 850;

    letter-spacing: -0.04em;
}}

.brand-subtitle {{
    color: #777777;

    font-size: 11px;

    font-weight: 650;

    letter-spacing: 0.08em;

    text-transform: uppercase;

    border-left: 1px solid #cccccc;

    padding-left: 12px;

    margin-left: 2px;
}}

.topbar-right {{
    display: flex;

    align-items: center;

    gap: 18px;
}}

.evidence-badge {{
    display: inline-flex;

    align-items: center;

    gap: 8px;

    padding: 8px 12px;

    border: 1px solid #d3d3d3;

    background: #fafafa;

    color: #333333;

    font-size: 11px;

    font-weight: 750;

    letter-spacing: 0.07em;

    text-transform: uppercase;
}}

.evidence-dot {{
    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: #111111;
}}


/* ========================================================
   HERO
   ======================================================== */

.hero {{
    background: #ffffff;

    border-bottom: 1px solid #d7d7d7;
}}

.hero-inner {{
    width: min(
        1440px,
        calc(100% - 48px)
    );

    margin: 0 auto;

    padding:
        78px
        0
        72px;
}}

.hero-meta {{
    display: flex;

    align-items: center;

    gap: 12px;

    margin-bottom: 28px;

    color: #666666;

    font-size: 11px;

    font-weight: 750;

    letter-spacing: 0.12em;

    text-transform: uppercase;
}}

.hero-meta-line {{
    width: 38px;
    height: 1px;

    background: #111111;
}}

.hero-title {{
    max-width: 1120px;

    margin: 0;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size:
        clamp(
            48px,
            6vw,
            88px
        );

    line-height: 0.98;

    letter-spacing: -0.055em;

    font-weight: 700;

    color: #0c0c0c;
}}

.hero-introduction {{
    max-width: 900px;

    margin:
        34px
        0
        0;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size:
        clamp(
            20px,
            2vw,
            27px
        );

    line-height: 1.55;

    color: #454545;
}}

.hero-query {{
    display: inline-flex;

    align-items: center;

    max-width: 100%;

    margin-top: 38px;

    padding: 11px 14px;

    border: 1px solid #d4d4d4;

    background: #fafafa;

    color: #555555;

    font-size: 12px;

    font-weight: 650;

    overflow-wrap: anywhere;
}}

.hero-query-label {{
    margin-right: 8px;

    color: #111111;

    font-weight: 800;

    text-transform: uppercase;

    letter-spacing: 0.08em;
}}


/* ========================================================
   MAIN LAYOUT
   ======================================================== */

.main {{
    width: min(
        1440px,
        calc(100% - 48px)
    );

    margin: 0 auto;

    display: grid;

    grid-template-columns:
        minmax(0, 1fr)
        360px;

    gap: 72px;

    align-items: start;

    padding:
        72px
        0
        100px;
}}


/* ========================================================
   ARTICLE
   ======================================================== */

.article-column {{
    min-width: 0;

    max-width: 850px;
}}

.article-intro {{
    padding-bottom: 44px;

    margin-bottom: 12px;

    border-bottom: 1px solid #d5d5d5;
}}

.article-intro-label {{
    margin-bottom: 14px;

    color: #777777;

    font-size: 10px;

    font-weight: 800;

    letter-spacing: 0.14em;

    text-transform: uppercase;
}}

.article-intro-text {{
    margin: 0;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 23px;

    line-height: 1.7;

    color: #222222;
}}


/* ========================================================
   ARTICLE SECTION
   ======================================================== */

.article-section {{
    position: relative;

    display: grid;

    grid-template-columns: 70px minmax(0, 1fr);

    gap: 28px;

    padding:
        58px
        0;

    border-bottom: 1px solid #dedede;
}}

.section-number {{
    padding-top: 5px;

    color: #a0a0a0;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 18px;

    font-weight: 700;
}}

.section-body {{
    min-width: 0;
}}

.section-eyebrow {{
    margin-bottom: 11px;

    color: #777777;

    font-size: 10px;

    font-weight: 800;

    letter-spacing: 0.14em;

    text-transform: uppercase;
}}

.section-body h2 {{
    margin:
        0
        0
        20px;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size:
        clamp(
            28px,
            3vw,
            40px
        );

    line-height: 1.12;

    letter-spacing: -0.035em;

    color: #111111;
}}

.section-content {{
    white-space: pre-line;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 18px;

    line-height: 1.9;

    color: #303030;
}}

.section-content::first-letter {{
    font-size: 1.2em;
}}


/* ========================================================
   KEY POINTS
   ======================================================== */

.key-points {{
    margin-top: 58px;

    padding:
        34px
        36px
        38px;

    background: #111111;

    color: #ffffff;
}}

.key-points .section-eyebrow {{
    color: #999999;
}}

.key-points h2 {{
    margin:
        0
        0
        24px;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 34px;

    line-height: 1.15;

    letter-spacing: -0.03em;

    font-weight: 700;
}}

.key-points ul {{
    list-style: none;

    margin: 0;

    padding: 0;
}}

.key-point {{
    display: grid;

    grid-template-columns: 12px minmax(0, 1fr);

    gap: 14px;

    padding: 17px 0;

    border-top: 1px solid #333333;

    color: #eeeeee;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 16px;

    line-height: 1.65;
}}

.key-point:last-child {{
    border-bottom: 1px solid #333333;
}}

.key-point-mark {{
    width: 7px;
    height: 7px;

    margin-top: 9px;

    background: #ffffff;
}}


/* ========================================================
   CONCLUSION
   ======================================================== */

.conclusion {{
    margin-top: 58px;

    padding:
        42px
        44px;

    background: #ffffff;

    border:
        1px
        solid
        #cfcfcf;

    border-left:
        5px
        solid
        #111111;
}}

.conclusion-label {{
    margin-bottom: 14px;

    color: #777777;

    font-size: 10px;

    font-weight: 800;

    letter-spacing: 0.14em;

    text-transform: uppercase;
}}

.conclusion h2 {{
    margin:
        0
        0
        18px;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 34px;

    line-height: 1.1;

    letter-spacing: -0.035em;
}}

.conclusion p {{
    margin: 0;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 18px;

    line-height: 1.85;

    color: #333333;
}}


/* ========================================================
   SIDEBAR
   ======================================================== */

.sidebar {{
    position: sticky;

    top: 92px;

    min-width: 0;
}}

.sidebar-heading {{
    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 15px;

    padding-bottom: 16px;

    border-bottom: 2px solid #111111;
}}

.sidebar-heading h2 {{
    margin: 0;

    font-size: 13px;

    font-weight: 850;

    letter-spacing: 0.09em;

    text-transform: uppercase;
}}

.sidebar-count {{
    display: inline-flex;

    min-width: 27px;
    height: 27px;

    padding: 0 8px;

    align-items: center;

    justify-content: center;

    background: #111111;

    color: #ffffff;

    font-size: 11px;

    font-weight: 800;
}}

.sources-list {{
    display: flex;

    flex-direction: column;

    gap: 0;
}}


/* ========================================================
   SOURCE CARD
   ======================================================== */

.source-card {{
    position: relative;

    padding:
        26px
        0
        28px;

    border-bottom: 1px solid #d6d6d6;
}}

.source-card-top {{
    display: flex;

    align-items: center;

    justify-content: space-between;

    margin-bottom: 17px;
}}

.source-number {{
    color: #999999;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 15px;

    font-weight: 700;
}}

.source-label {{
    color: #777777;

    font-size: 9px;

    font-weight: 850;

    letter-spacing: 0.13em;
}}

.source-title {{
    margin:
        0
        0
        8px;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 21px;

    line-height: 1.25;

    letter-spacing: -0.025em;

    color: #111111;
}}

.source-publisher {{
    margin-bottom: 13px;

    color: #555555;

    font-size: 11px;

    font-weight: 750;

    text-transform: uppercase;

    letter-spacing: 0.07em;
}}

.source-preview {{
    margin:
        0
        0
        18px;

    color: #666666;

    font-size: 13px;

    line-height: 1.7;
}}

.source-metrics {{
    display: grid;

    grid-template-columns: 1fr 1fr;

    border-top: 1px solid #dddddd;

    border-bottom: 1px solid #dddddd;

    margin-bottom: 18px;
}}

.source-metric {{
    padding:
        11px
        0;

    display: flex;

    flex-direction: column;

    gap: 3px;
}}

.source-metric + .source-metric {{
    border-left: 1px solid #dddddd;

    padding-left: 14px;
}}

.metric-label {{
    color: #999999;

    font-size: 8px;

    font-weight: 850;

    letter-spacing: 0.12em;
}}

.source-metric strong {{
    color: #111111;

    font-size: 14px;

    font-weight: 850;
}}

.source-link {{
    display: inline-flex;

    align-items: center;

    gap: 6px;

    color: #111111;

    font-size: 11px;

    font-weight: 800;

    text-decoration: none;

    border-bottom: 1px solid #111111;

    padding-bottom: 2px;

    transition:
        opacity 0.2s ease,
        transform 0.2s ease;
}}

.source-link:hover {{
    opacity: 0.55;

    transform: translateX(2px);
}}

.empty-sources {{
    padding:
        25px
        0;

    color: #777777;

    font-size: 13px;
}}


/* ========================================================
   EVIDENCE NOTICE
   ======================================================== */

.evidence-notice {{
    margin-top: 28px;

    padding:
        20px
        20px;

    background: #eeeeee;

    border: 1px solid #d6d6d6;
}}

.evidence-notice-title {{
    margin-bottom: 7px;

    color: #111111;

    font-size: 10px;

    font-weight: 850;

    letter-spacing: 0.11em;

    text-transform: uppercase;
}}

.evidence-notice-text {{
    margin: 0;

    color: #666666;

    font-size: 12px;

    line-height: 1.65;
}}


/* ========================================================
   FOOTER
   ======================================================== */

.footer {{
    border-top: 1px solid #cfcfcf;

    background: #111111;

    color: #ffffff;
}}

.footer-inner {{
    width: min(
        1440px,
        calc(100% - 48px)
    );

    margin: 0 auto;

    padding:
        44px
        0;

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 30px;
}}

.footer-brand {{
    display: flex;

    align-items: center;

    gap: 11px;
}}

.footer-mark {{
    width: 29px;
    height: 29px;

    background: #ffffff;

    color: #111111;

    display: grid;

    place-items: center;

    font-size: 12px;

    font-weight: 900;
}}

.footer-name {{
    font-size: 14px;

    font-weight: 800;

    letter-spacing: -0.02em;
}}

.footer-text {{
    color: #888888;

    font-size: 11px;

    line-height: 1.6;

    text-align: right;
}}


/* ========================================================
   SELECTION
   ======================================================== */

::selection {{
    background: #111111;

    color: #ffffff;
}}


/* ========================================================
   SCROLLBAR
   ======================================================== */

::-webkit-scrollbar {{
    width: 9px;
}}

::-webkit-scrollbar-track {{
    background: #eeeeee;
}}

::-webkit-scrollbar-thumb {{
    background: #999999;
}}

::-webkit-scrollbar-thumb:hover {{
    background: #555555;
}}


/* ========================================================
   RESPONSIVE — TABLET
   ======================================================== */

@media (
    max-width: 1100px
) {{

    .main {{
        grid-template-columns:
            minmax(0, 1fr)
            300px;

        gap: 45px;
    }}

    .hero-title {{
        font-size:
            clamp(
                46px,
                7vw,
                72px
            );
    }}

    .hero-inner {{
        padding-top: 62px;
        padding-bottom: 58px;
    }}

    .article-section {{
        grid-template-columns:
            52px
            minmax(0, 1fr);

        gap: 20px;
    }}

}}


/* ========================================================
   RESPONSIVE — MOBILE
   ======================================================== */

@media (
    max-width: 820px
) {{

    .topbar {{
        height: 60px;
    }}

    .topbar-inner {{
        width: min(
            100% - 28px,
            1440px
        );
    }}

    .brand-subtitle {{
        display: none;
    }}

    .evidence-badge {{
        padding:
            7px
            9px;

        font-size: 9px;
    }}

    .hero-inner {{
        width: min(
            100% - 28px,
            1440px
        );

        padding:
            52px
            0
            48px;
    }}

    .hero-title {{
        font-size:
            clamp(
                42px,
                12vw,
                62px
            );

        line-height: 1;
    }}

    .hero-introduction {{
        margin-top: 25px;

        font-size: 19px;
    }}

    .main {{
        width: min(
            100% - 28px,
            850px
        );

        display: block;

        padding:
            48px
            0
            70px;
    }}

    .article-column {{
        max-width: none;
    }}

    .sidebar {{
        position: static;

        margin-top: 65px;
    }}

    .article-section {{
        grid-template-columns:
            1fr;

        gap: 5px;

        padding:
            43px
            0;
    }}

    .section-number {{
        padding-top: 0;

        margin-bottom: 5px;
    }}

    .section-content {{
        font-size: 17px;

        line-height: 1.8;
    }}

    .key-points {{
        padding:
            29px
            26px;
    }}

    .conclusion {{
        padding:
            30px
            26px;
    }}

    .footer-inner {{
        width: min(
            100% - 28px,
            1440px
        );

        flex-direction: column;

        align-items: flex-start;
    }}

    .footer-text {{
        text-align: left;
    }}

}}


/* ========================================================
   RESPONSIVE — SMALL MOBILE
   ======================================================== */

@media (
    max-width: 480px
) {{

    .brand-name {{
        font-size: 17px;
    }}

    .hero-meta {{
        font-size: 9px;
    }}

    .hero-title {{
        font-size: 39px;
    }}

    .hero-query {{
        display: block;

        line-height: 1.6;
    }}

    .hero-query-label {{
        display: block;

        margin:
            0
            0
            4px;
    }}

    .article-intro-text {{
        font-size: 20px;
    }}

    .section-body h2 {{
        font-size: 29px;
    }}

    .key-points h2 {{
        font-size: 29px;
    }}

    .source-title {{
        font-size: 19px;
    }}

}}


/* ========================================================
   PRINT
   ======================================================== */

@media print {{

    body {{
        background: #ffffff;
    }}

    .topbar {{
        position: static;

        background: #ffffff;

        box-shadow: none;
    }}

    .hero,
    .page {{
        background: #ffffff;
    }}

    .hero-inner,
    .main,
    .footer-inner {{
        width: 100%;

        max-width: none;
    }}

    .main {{
        display: block;

        padding:
            30px
            0;
    }}

    .sidebar {{
        position: static;

        margin-top: 50px;
    }}

    .source-link {{
        text-decoration: underline;
    }}

    .footer {{
        background: #ffffff;

        color: #111111;
    }}

    .footer-text {{
        color: #555555;
    }}

    .footer-mark {{
        background: #111111;

        color: #ffffff;
    }}

    .key-points {{
        color: #111111;

        background: #ffffff;

        border: 1px solid #111111;
    }}

    .key-points .section-eyebrow {{
        color: #555555;
    }}

    .key-point {{
        color: #222222;

        border-color: #cccccc;
    }}

    .key-point-mark {{
        background: #111111;
    }}

    .evidence-badge {{
        background: #ffffff;
    }}

}}


</style>

</head>


<body>

<div class="page">


    <!-- ==================================================
         TOP BAR
         ================================================== -->

    <header class="topbar">

        <div class="topbar-inner">

            <a
                href="#"
                class="brand"
                aria-label="TrustNews"
            >

                <span class="brand-mark">
                    TN
                </span>

                <span class="brand-name">
                    TrustNews
                </span>

                <span class="brand-subtitle">
                    Evidence Desk
                </span>

            </a>


            <div class="topbar-right">

                <div class="evidence-badge">

                    <span class="evidence-dot"></span>

                    Source grounded

                </div>

            </div>

        </div>

    </header>



    <!-- ==================================================
         HERO
         ================================================== -->

    <section class="hero">

        <div class="hero-inner">

            <div class="hero-meta">

                <span>
                    TRUSTNEWS REPORT
                </span>

                <span class="hero-meta-line"></span>

                <span>
                    Evidence-based
                </span>

            </div>


            <h1 class="hero-title">
                {title}
            </h1>


            <p class="hero-introduction">
                {introduction}
            </p>


            <div class="hero-query">

                <span class="hero-query-label">
                    Query
                </span>

                <span>
                    {clean_query}
                </span>

            </div>

        </div>

    </section>



    <!-- ==================================================
         MAIN CONTENT
         ================================================== -->

    <main class="main">


        <!-- =================================================
             ARTICLE COLUMN
             ================================================= -->

        <article class="article-column">


            <section class="article-intro">

                <div class="article-intro-label">
                    Article
                </div>

                <p class="article-intro-text">
                    {introduction}
                </p>

            </section>


            {section_html}


            {key_points_html}


            <!-- =============================================
                 CONCLUSION
                 ============================================= -->

            <section class="conclusion">

                <div class="conclusion-label">
                    Conclusion
                </div>

                <h2>
                    The takeaway
                </h2>

                <p>
                    {conclusion}
                </p>

            </section>


        </article>



        <!-- =================================================
             SIDEBAR
             ================================================= -->

        <aside class="sidebar">


            <div class="sidebar-heading">

                <h2>
                    Sources
                </h2>

                <span class="sidebar-count">
                    {source_count}
                </span>

            </div>


            <div class="sources-list">

                {sources_html}

            </div>


            <div class="evidence-notice">

                <div class="evidence-notice-title">
                    Evidence note
                </div>

                <p class="evidence-notice-text">
                    This article is generated from the retrieved
                    sources shown here. Relevance scores indicate
                    retrieval relevance and should not be interpreted
                    as factual certainty or source credibility.
                </p>

            </div>


        </aside>


    </main>



    <!-- ==================================================
         FOOTER
         ================================================== -->

    <footer class="footer">

        <div class="footer-inner">


            <div class="footer-brand">

                <span class="footer-mark">
                    TN
                </span>

                <span class="footer-name">
                    TrustNews
                </span>

            </div>


            <div class="footer-text">

                Evidence-grounded news article<br>

                Generated from retrieved sources

            </div>


        </div>

    </footer>


</div>


</body>

</html>
"""