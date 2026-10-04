import os
import time

from google import genai


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# Use a model available to your Gemini API account.
# Keep this configurable through .env.
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
)


def expand_query(query: str) -> list[str]:
    """
    Expand the user's query into semantically related
    search queries.

    If Gemini is unavailable, the system falls back
    to the original query so retrieval can continue.
    """

    query = query.strip()

    if not query:
        return []

    # Always preserve original query.
    queries = [query]

    # -----------------------------------------
    # Gemini unavailable
    # -----------------------------------------

    if client is None:
        print(
            "WARNING: GEMINI_API_KEY is not configured. "
            "Using original query only."
        )

        return queries

    prompt = f"""
You are a query expansion component for a news retrieval system.

Original query:
{query}

Generate exactly 3 alternative search queries.

Rules:
- Preserve the original meaning.
- Keep the same entities.
- Do not introduce unrelated topics.
- Do not invent facts or entities.
- Do not answer the query.
- Make each query useful for retrieving relevant news.
- Return ONLY the 3 queries.
- One query per line.
"""

    # -----------------------------------------
    # Retry Gemini temporarily
    # -----------------------------------------

    for attempt in range(3):

        try:

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt
            )

            text = (
                response.text
                if response and response.text
                else ""
            ).strip()

            if not text:
                return queries

            expanded = []

            for line in text.splitlines():

                line = line.strip()

                # Remove common numbering/bullets
                line = line.lstrip("-•")

                if line[:2].isdigit() and line[2:3] in [".", ")"]:
                    line = line[3:].strip()

                line = line.strip()

                if not line:
                    continue

                if line not in queries and line not in expanded:
                    expanded.append(line)

            queries.extend(expanded[:3])

            return queries[:4]

        except Exception as exc:

            print(
                f"Query expansion attempt "
                f"{attempt + 1}/3 failed: {exc}"
            )

            # Small delay before retry
            if attempt < 2:
                time.sleep(2)

    # -----------------------------------------
    # Final fallback
    # -----------------------------------------

    print(
        "WARNING: Gemini query expansion failed. "
        "Continuing with original query."
    )

    return queries