from typing import Any


def generate_inquiries(claim_text: str) -> dict[str, Any]:
    normalized_claim = " ".join(claim_text.split())
    if not normalized_claim:
        raise ValueError("Claim text cannot be empty.")

    return {
        "verification_question": (
            "Does the available evidence support or contradict this claim: "
            f"{normalized_claim}"
        ),
        "search_queries": [normalized_claim],
    }
