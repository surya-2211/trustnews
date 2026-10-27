from typing import Any, Callable

from app.verification.llm import generate_structured_json


VERDICTS = {
    "SUPPORTED",
    "REFUTED",
    "CONFLICTING_EVIDENCE",
    "NOT_ENOUGH_EVIDENCE",
}

JUDGE_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "verdict": {
            "type": "STRING",
            "enum": sorted(VERDICTS),
        },
        "explanation": {"type": "STRING"},
        "supporting_evidence_indexes": {
            "type": "ARRAY",
            "items": {"type": "INTEGER"},
        },
        "contradicting_evidence_indexes": {
            "type": "ARRAY",
            "items": {"type": "INTEGER"},
        },
        "further_retrieval_recommended": {"type": "BOOLEAN"},
    },
    "required": [
        "verdict",
        "explanation",
        "supporting_evidence_indexes",
        "contradicting_evidence_indexes",
        "further_retrieval_recommended",
    ],
}


def judge_claim(
    claim: dict[str, Any],
    evidence: list[dict[str, Any]],
    generate_json: Callable[..., dict[str, Any]] = generate_structured_json,
) -> dict[str, Any]:
    indexed_evidence = [
        {
            "evidence_index": index,
            "title": item.get("title", ""),
            "source": item.get("source", ""),
            "url": item.get("url", ""),
            "published_at": item.get("published_at"),
            "content": item.get("content", ""),
        }
        for index, item in enumerate(evidence)
    ]

    prompt = f"""
Determine how the complete evidence set relates to this factual claim.

Use only the supplied passages and metadata. Semantic similarity is not proof.
Evaluate the full claim, including its dates, quantities, entities, and
qualifiers. Partial support is not sufficient to label the whole claim
SUPPORTED. Preserve relevant contradictory evidence. Do not use majority
voting alone; consider directness, source context, dates, and whether reports
may repeat the same original source.

For SUPPORTED, the cited passages must directly substantiate every material
part of the claim. Do not treat the article text, a source title, or retrieval
relevance as confirmation. When evidence is indirect, incomplete, or
ambiguous, choose NOT_ENOUGH_EVIDENCE. Do not infer support merely because
no contradiction was found.

Choose exactly one verdict:
- SUPPORTED: relevant evidence adequately supports the whole claim.
- REFUTED: relevant evidence adequately contradicts the whole claim.
- CONFLICTING_EVIDENCE: relevant evidence gives materially incompatible
  accounts that cannot be resolved from the available information.
- NOT_ENOUGH_EVIDENCE: evidence is missing, irrelevant, incomplete, or
  insufficient to establish support or contradiction.

Reference evidence only by its zero-based evidence_index. Include every
passage materially supporting or contradicting the claim. Do not invent
references. Recommend more retrieval for unresolved insufficiency or
conflict. Relevance scores are not truth or credibility scores.

CLAIM:
{claim.get("claim_text", "")!r}

EVIDENCE:
{indexed_evidence!r}
"""
    result = generate_json(prompt, JUDGE_RESPONSE_SCHEMA)
    verdict = result.get("verdict")
    explanation = result.get("explanation")
    if not isinstance(verdict, str) or verdict not in VERDICTS:
        raise RuntimeError("Gemini returned an invalid verification verdict.")
    if not isinstance(explanation, str) or not explanation.strip():
        raise RuntimeError("Gemini returned no verification explanation.")

    supporting = _validate_indexes(
        result.get("supporting_evidence_indexes"),
        len(evidence),
        "supporting_evidence_indexes",
    )
    contradicting = _validate_indexes(
        result.get("contradicting_evidence_indexes"),
        len(evidence),
        "contradicting_evidence_indexes",
    )
    further = result.get("further_retrieval_recommended")
    if not isinstance(further, bool):
        raise RuntimeError(
            "Gemini returned an invalid further-retrieval flag."
        )

    return {
        "verdict": verdict,
        "explanation": explanation.strip(),
        "supporting_evidence_indexes": supporting,
        "contradicting_evidence_indexes": contradicting,
        "further_retrieval_recommended": further,
    }


def _validate_indexes(
    value: Any,
    evidence_count: int,
    field_name: str,
) -> list[int]:
    if not isinstance(value, list):
        raise RuntimeError(f"Gemini returned malformed {field_name}.")

    indexes = []
    for index in value:
        if type(index) is not int or not 0 <= index < evidence_count:
            raise RuntimeError(
                f"Gemini returned an invalid index in {field_name}."
            )
        if index not in indexes:
            indexes.append(index)
    return indexes
