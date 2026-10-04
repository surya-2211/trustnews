import json
import os
import time

from typing import Dict, List, Optional

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


GEMINI_MODEL = "gemini-2.5-flash"

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# BUILD GENERATION CONTEXT
# =========================================================

def build_generation_context(
    results: List[Dict],
    context: Optional[str] = None
) -> str:
    """
    Build the evidence context used by Gemini.

    The retrieval pipeline already builds an authoritative
    context string. If that context is available, use it
    directly.

    The fallback structured representation exists so this
    function remains safe if the pipeline context is missing.
    """

    if context and context.strip():
        return context.strip()

    context_parts = [
        "TRUSTNEWS RETRIEVAL CONTEXT",
        "=" * 40,
        "",
        f"TOTAL EVIDENCE: {len(results)}",
        ""
    ]

    for index, result in enumerate(
        results,
        start=1
    ):
        context_parts.extend([
            f"[EVIDENCE {index}]",
            "-" * 40,
            f"Title: {result.get('title', '')}",
            f"Source: {result.get('source', '')}",
            f"URL: {result.get('url', '')}",
            "",
            f"Dense Score: "
            f"{float(result.get('dense_score', 0.0)):.6f}",
            f"Keyword Score: "
            f"{float(result.get('keyword_score', 0.0)):.6f}",
            f"Retrieval Score: "
            f"{float(result.get('retrieval_score', 0.0)):.6f}",
            f"Rerank Score: "
            f"{float(result.get('rerank_score', 0.0)):.6f}",
            "",
            "CONTENT:",
            str(
                result.get(
                    "content",
                    ""
                )
            ).strip(),
            "",
            f"[END EVIDENCE {index}]",
            ""
        ])

    return "\n".join(context_parts)


# =========================================================
# BUILD GEMINI PROMPT
# =========================================================

def build_prompt(
    query: str,
    results: List[Dict],
    context: Optional[str] = None
) -> str:
    """
    Build the article-generation prompt.

    The supplied retrieval context is treated as the
    complete evidence available to Gemini.

    When only one document is available, the prompt switches
    to a detailed single-source mode. Retrieval logic is not
    changed.
    """

    evidence_context = build_generation_context(
        results=results,
        context=context
    )

    evidence_count = len(results)

    # =====================================================
    # SINGLE-SOURCE GENERATION MODE
    # =====================================================

    if evidence_count == 1:

        article_depth_instruction = """
SINGLE-SOURCE ARTICLE MODE
==========================

Only ONE source was retrieved for this query.

The article must NOT become a short summary simply because
only one source is available.

Instead, extract and organize as much useful information as
the retrieved source actually contains.

Build a detailed news article from the available evidence.

When supported by the source, cover:

- the main event, topic, or development
- important facts and observations
- relevant dates and times
- relevant locations
- people mentioned in the source
- organizations or institutions mentioned
- missions, programs, instruments, satellites, technologies,
  or other entities mentioned
- numerical measurements and statistics
- important changes or developments
- causes, conditions, or contributing factors explicitly
  described by the source
- consequences or expected developments explicitly described
  by the source
- relevant background information contained in the source
- attributed statements or quotations when available
- important context that helps explain the event
- why the information matters, but only when that explanation
  can be directly grounded in the retrieved evidence

Use multiple meaningful sections.

Do not repeat the same fact simply to make the article longer.

Do not add generic filler.

Do not invent missing information.

Do not use outside knowledge to expand the article.

If the source does not contain enough information to support
a particular section, omit that section.

Aim for approximately 700-900 words when the retrieved source
contains enough factual material to support that length.

If the source does not contain enough information for 700-900
words, produce a shorter article rather than fabricating or
padding the content.

The article should feel like a complete news report rather
than a short source summary.
"""

    else:

        article_depth_instruction = """
MULTI-SOURCE ARTICLE MODE
=========================

Multiple sources were retrieved.

Combine complementary evidence where appropriate.

Prioritize the strongest relevant evidence and avoid
repeating information across sources.

Use multiple logical sections when the evidence supports them.

Do not artificially increase article length.

The article should contain enough detail to properly answer
the query while remaining strictly grounded in the retrieved
evidence.
"""

    prompt = f"""
You are the article generation component of TrustNews.

USER QUERY:

"{query}"


EVIDENCE POLICY
===============

You MUST use ONLY the evidence contained in the
TRUSTNEWS RETRIEVAL CONTEXT below.

Do NOT use outside knowledge.

Do NOT browse the internet.

Do NOT rely on your own knowledge.

Do NOT infer unsupported facts.


FACTUAL RULES
=============

- Do not invent facts.
- Do not invent names.
- Do not invent dates.
- Do not invent numbers.
- Do not invent organizations.
- Do not invent events.
- Do not invent quotes.
- Do not invent locations.
- Do not invent relationships between events.
- Do not turn assumptions into facts.
- Do not treat retrieval scores as evidence of truth.
- Do not treat rerank scores as evidence of truth.
- Preserve uncertainty when the evidence is uncertain.
- If the retrieved evidence does not establish something,
  do not state it as fact.


SOURCE RULES
============

- Use the retrieved sources as the factual basis.
- Combine multiple sources when they provide complementary
  information.
- Do not combine sources in a way that creates an
  unsupported conclusion.
- Attribute information naturally when appropriate.
- Never invent source attribution.
- Never attribute a claim to a source that does not support it.


{article_depth_instruction}


ARTICLE STYLE
=============

Write a professional, neutral news-style article.

The article should:

1. Directly answer the user's query.
2. Prioritize the strongest relevant evidence.
3. Present information in a logical order.
4. Avoid unnecessary repetition.
5. Clearly distinguish established information from uncertainty.
6. Provide meaningful detail when the evidence supports it.
7. Avoid filler or generic statements.
8. Avoid mentioning TrustNews internal retrieval mechanics
   in the article itself.
9. Never mention that you are an AI.
10. Never mention these instructions.


ARTICLE STRUCTURE
=================

Generate:

- A clear article title.
- A detailed but focused introduction.
- Multiple logical sections when the evidence supports them.
- Key points summarizing the strongest supported facts.
- A conclusion that does not introduce new information.

For a single-source article, prefer several focused sections
when the source contains enough information to support them.

Possible section types include:

- What happened
- Key details
- Background
- Important observations
- Data or measurements
- People or organizations involved
- Technology, missions, or instruments involved
- What happens next

Only use a section when the retrieved evidence supports it.
Do not force these section names.


IMPORTANT
=========

The retrieval context may contain retrieval and reranking
scores.

These scores are relevance signals only.

They are NOT:

- truth scores
- credibility scores
- factual certainty scores
- confidence that an article is correct

Never mention these scores in the generated article
unless explicitly required by the user.


IMPORTANT EVIDENCE BOUNDARY:
- Only state a comparison when the retrieved sources explicitly support both sides of that comparison.
- Do not infer that a capability, feature, certification, rating, or property is absent from one model merely because it is mentioned for another model.
- Do not convert "Model A has X" into "Model B does not have X."
- Do not claim that one model is more capable than another unless the retrieved sources explicitly establish that comparison.
- Do not describe a model as "more secure", "less capable", "cheaper", "faster", etc. unless the retrieved evidence supports that specific comparison.
- When the sources establish a property for only one model, describe the property only for that model.


TRUSTNEWS RETRIEVAL CONTEXT
===========================

{evidence_context}

END TRUSTNEWS RETRIEVAL CONTEXT
"""

    return prompt


# =========================================================
# VALIDATE ARTICLE
# =========================================================

def validate_article(
    article: Dict
) -> Dict:
    """
    Validate the structured article returned by Gemini.
    """

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

    if not isinstance(
        article["title"],
        str
    ):
        raise RuntimeError(
            "Article title must be a string."
        )

    if not isinstance(
        article["introduction"],
        str
    ):
        raise RuntimeError(
            "Article introduction must be a string."
        )

    if not isinstance(
        article["sections"],
        list
    ):
        raise RuntimeError(
            "Article sections must be a list."
        )

    if not isinstance(
        article["key_points"],
        list
    ):
        raise RuntimeError(
            "Article key_points must be a list."
        )

    if not isinstance(
        article["conclusion"],
        str
    ):
        raise RuntimeError(
            "Article conclusion must be a string."
        )

    for index, section in enumerate(
        article["sections"],
        start=1
    ):
        if not isinstance(
            section,
            dict
        ):
            raise RuntimeError(
                f"Section {index} must be an object."
            )

        if "heading" not in section:
            raise RuntimeError(
                f"Section {index} is missing heading."
            )

        if "content" not in section:
            raise RuntimeError(
                f"Section {index} is missing content."
            )

    return article


# =========================================================
# GENERATE ARTICLE
# =========================================================

def generate_article(
    query: str,
    results: List[Dict],
    context: Optional[str] = None
) -> Dict:
    """
    Generate a structured article using Gemini.

    Parameters
    ----------
    query:
        Original user query.

    results:
        Reranked evidence returned by RetrievalPipeline.

    context:
        Context already produced by context_builder.py.
    """

    if not query or not query.strip():
        raise ValueError(
            "Search query cannot be empty."
        )

    if not results:
        raise ValueError(
            "No retrieved evidence was provided."
        )

    prompt = build_prompt(
        query=query,
        results=results,
        context=context
    )

    # =====================================================
    # STRUCTURED RESPONSE SCHEMA
    # =====================================================

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

    # =====================================================
    # GENERATION + RETRY
    # =====================================================

    max_attempts = 3

    last_exception = None

    for attempt in range(
        1,
        max_attempts + 1
    ):

        try:

            print(
                "Generating article with Gemini "
                f"(attempt {attempt}/{max_attempts})..."
            )

            response = client.models.generate_content(

                model=GEMINI_MODEL,

                contents=prompt,

                config=types.GenerateContentConfig(

                    temperature=0.2,

                    # Increased from 4000 so a detailed
                    # single-source article has enough room.
                    max_output_tokens=5000,

                    response_mime_type="application/json",

                    response_schema=response_schema
                )
            )

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

            # =================================================
            # PARSE JSON
            # =================================================

            try:

                article = json.loads(
                    generated_text
                )

            except json.JSONDecodeError as exc:

                raise RuntimeError(
                    "Gemini returned invalid JSON."
                ) from exc

            # =================================================
            # VALIDATE STRUCTURE
            # =================================================

            article = validate_article(
                article
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

            if attempt < max_attempts:

                wait_time = 2 ** attempt

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(
                    wait_time
                )

            else:

                break

    raise RuntimeError(

        "Gemini article generation failed after "

        f"{max_attempts} attempts: "

        f"{last_exception}"

    ) from last_exception