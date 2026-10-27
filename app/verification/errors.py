import re
from typing import Any

from fastapi import HTTPException
from google.genai.errors import APIError


def is_per_minute_quota_error(exc: APIError) -> bool:
    return any(
        "minute" in value.casefold()
        for value in _quota_descriptions(exc.details)
    )


def get_gemini_retry_delay(exc: APIError) -> float | None:
    for item in _detail_items(exc.details):
        if not isinstance(item, dict):
            continue
        retry_delay = item.get("retryDelay")
        if not isinstance(retry_delay, str):
            continue

        match = re.fullmatch(
            r"(?:(\d+(?:\.\d+)?)h)?"
            r"(?:(\d+(?:\.\d+)?)m)?"
            r"(?:(\d+(?:\.\d+)?)s)?",
            retry_delay.strip(),
        )
        if match and any(match.groups()):
            hours, minutes, seconds = (
                float(part or 0)
                for part in match.groups()
            )
            return hours * 3600 + minutes * 60 + seconds
    return None


def _detail_items(value: Any) -> list[Any]:
    if isinstance(value, dict):
        items = [value]
        for nested in value.values():
            items.extend(_detail_items(nested))
        return items
    if isinstance(value, list):
        return [
            item
            for nested in value
            for item in _detail_items(nested)
        ]
    return []


def _quota_descriptions(value: Any) -> list[str]:
    descriptions = []
    for item in _detail_items(value):
        if not isinstance(item, dict):
            continue
        for key in ("quotaId", "description", "quotaMetric"):
            text = item.get(key)
            if isinstance(text, str):
                descriptions.append(text)
    return descriptions


def map_gemini_error(
    exc: APIError,
    model_name: str,
) -> HTTPException:
    message = str(
        getattr(exc, "message", "") or "No additional details returned."
    )[:800]

    if exc.code == 429:
        if is_per_minute_quota_error(exc):
            retry_delay = get_gemini_retry_delay(exc)
            retry_hint = (
                f" Gemini recommends retrying in about {retry_delay:g} "
                "seconds."
                if retry_delay is not None
                else ""
            )
            return HTTPException(
                status_code=429,
                detail=(
                    f"Gemini's per-minute request limit was reached for "
                    f"model '{model_name}'. Claim verification makes "
                    "multiple model requests; wait for the limit to "
                    "reset before trying again."
                    f"{retry_hint} Gemini says: {message}"
                ),
            )

        return HTTPException(
            status_code=429,
            detail=(
                "Gemini API quota or rate limit has been reached. Quotas "
                "are associated with the project and model, not an "
                "individual API key; creating another key in the same "
                "project will not reset them. Check project usage and "
                f"billing, or retry when the quota resets. Gemini says: {message}"
            ),
        )

    if exc.code == 404:
        return HTTPException(
            status_code=502,
            detail=(
                f"Gemini could not find or access model '{model_name}'. "
                "Check GEMINI_MODEL against the models available to this "
                f"API key. Gemini says: {message}"
            ),
        )

    if exc.code in (401, 403):
        return HTTPException(
            status_code=502,
            detail=(
                "Gemini rejected the API key or project permissions. "
                f"Gemini says: {message}"
            ),
        )

    if exc.code == 503:
        return HTTPException(
            status_code=503,
            detail=(
                "Gemini is temporarily unavailable or under high demand. "
                "Wait briefly and retry, or configure GEMINI_MODEL to "
                f"another model available to your API key. Gemini says: {message}"
            ),
        )

    return HTTPException(
        status_code=502,
        detail=(
            "Gemini rejected the claim-verification request "
            f"(HTTP {exc.code}). Gemini says: {message}"
        ),
    )
