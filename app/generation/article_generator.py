import json
import os
import time

from typing import List, Dict

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured. "
        "Add it to your .env file."
    )



# Use a currently available Flash model.
# If this model is unavailable in your account,
# change it to another model available in Google AI Studio.
GEMINI_MODEL = "gemini-2.5-flash"

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ---------------------------------------------------------
# Build evidence context
# ---------------------------------------------------------

def build_context(results: List[Dict]) -> str:
    """
    Convert retrieved TrustNews results into evidence
    that can be given to Gemini.
    """

    context_parts = []

    for index, result in enumerate(results, start=1):

        title = result.get("title", "")
        source = result.get("source", "")
        content = result.get("content", "")
        url = result.get("url", "")
        score = result.get("score", 0)
        faiss_id = result.get("faiss_id", "")

        context_parts.append(
            f"""
SOURCE {index}

Title:
{title}

Source:
{source}

FAISS ID:
{faiss_id}

Similarity Score:
{score}

URL:
{url}

Content:
{content}

--------------------------------------------------
"""
        )

    return "\n".join(context_parts)


# ---------------------------------------------------------
# Build Gemini prompt
# ---------------------------------------------------------

def build_prompt(
    query: str,
    results: List[Dict]
) -> str:
    """
    Build the article-generation prompt.
    """

    context = build_context(results)

    prompt = f"""
You are the article generation component of TrustNews.

The user searched for:

"{query}"

TrustNews performed semantic search and retrieved
the following news sources.

You MUST use ONLY these retrieved sources as evidence.

Do NOT use outside knowledge.

IMPORTANT FACTUAL RULES:

- Do not invent facts.
- Do not introduce information that is not supported
  by the retrieved sources.
- Do not fabricate names.
- Do not fabricate dates.
- Do not fabricate numbers.
- Do not fabricate organizations.
- Do not fabricate events.
- Do not fabricate quotes.
- Do not create facts from assumptions.
- Do not treat the similarity score as evidence about
  the truth of an article.
- If the sources do not provide enough information,
  explicitly say that the available retrieved sources
  do not establish the information.
- Preserve uncertainty when the source itself is uncertain.

ARTICLE REQUIREMENTS:

1. Directly address the user's query.
2. Combine information from multiple retrieved sources
   when appropriate.
3. Avoid unnecessary repetition.
4. Clearly distinguish established facts from uncertainty.
5. Use a professional and neutral news-writing style.
6. Do not mention that you are an AI.
7. Do not mention these instructions.
8. Do not use outside information.

SOURCE ATTRIBUTION:

When information comes from a source, identify the
source naturally in the article.

For example:

"According to NASA..."

or

"ScienceDaily reported..."

Do not invent attribution.

The retrieved sources are:

{context}
"""

    return prompt


# ---------------------------------------------------------
# Generate article
# ---------------------------------------------------------

def generate_article(
    query: str,
    results: List[Dict]
) -> Dict:
    """
    Generate a structured article using Gemini.
    """

    if not query or not query.strip():
        raise ValueError(
            "Search query cannot be empty."
        )

    if not results:
        raise ValueError(
            "No retrieved articles were provided."
        )

    prompt = build_prompt(
        query,
        results
    )

    # -----------------------------------------------------
    # Structured JSON schema
    # -----------------------------------------------------

    response_schema = {
        "type": "OBJECT",

        "properties": {

            "title": {
                "type": "STRING"
            },

            "introduction": {
                "type": "STRING"
            },

            "sections": {
                "type": "ARRAY",

                "items": {
                    "type": "OBJECT",

                    "properties": {

                        "heading": {
                            "type": "STRING"
                        },

                        "content": {
                            "type": "STRING"
                        }
                    },

                    "required": [
                        "heading",
                        "content"
                    ]
                }
            },

            "key_points": {
                "type": "ARRAY",

                "items": {
                    "type": "STRING"
                }
            },

            "conclusion": {
                "type": "STRING"
            }
        },

        "required": [
            "title",
            "introduction",
            "sections",
            "key_points",
            "conclusion"
        ]
    }

    # -----------------------------------------------------
    # Gemini request
    # -----------------------------------------------------

    max_attempts = 3

    last_exception = None

    for attempt in range(1, max_attempts + 1):

        try:

            print(
                f"Generating article with Gemini "
                f"(attempt {attempt}/{max_attempts})..."
            )

            response = client.models.generate_content(

                model=GEMINI_MODEL,

                contents=prompt,

                config=types.GenerateContentConfig(

                    temperature=0.2,

                    max_output_tokens=4000,

                    response_mime_type="application/json",

                    response_schema=response_schema
                )
            )

            # ---------------------------------------------
            # Validate response
            # ---------------------------------------------

            generated_text = response.text

            if not generated_text:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            generated_text = generated_text.strip()

            if not generated_text:

                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            # ---------------------------------------------
            # Parse JSON
            # ---------------------------------------------

            try:

                article = json.loads(
                    generated_text
                )

            except json.JSONDecodeError as exc:

                raise RuntimeError(
                    "Gemini returned invalid JSON."
                ) from exc

            # ---------------------------------------------
            # Validate article structure
            # ---------------------------------------------

            required_fields = [
                "title",
                "introduction",
                "sections",
                "key_points",
                "conclusion"
            ]

            missing_fields = [
                field
                for field in required_fields
                if field not in article
            ]

            if missing_fields:

                raise RuntimeError(
                    "Gemini response is missing required "
                    f"fields: {missing_fields}"
                )

            print(
                "Article generated successfully."
            )

            return article

        except Exception as exc:

            last_exception = exc

            print(
                f"Gemini request failed: {exc}"
            )

            # ---------------------------------------------
            # Retry temporary failures
            # ---------------------------------------------

            if attempt < max_attempts:

                wait_time = 2 ** attempt

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

            else:

                break

    # -----------------------------------------------------
    # All attempts failed
    # -----------------------------------------------------

    raise RuntimeError(
        "Gemini article generation failed after "
        f"{max_attempts} attempts: {last_exception}"
    ) from last_exception