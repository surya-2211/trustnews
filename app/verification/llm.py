import json
import time
from typing import Any, Callable

from app.verification.errors import (
    get_gemini_retry_delay,
    is_per_minute_quota_error,
)


MAX_RATE_LIMIT_RETRY_DELAY_SECONDS = 60
MAX_SERVICE_UNAVAILABLE_RETRIES = 2
MAX_SERVICE_UNAVAILABLE_RETRY_DELAY_SECONDS = 10


def generate_structured_json(
    prompt: str,
    response_schema: dict[str, Any],
    *,
    client: Any = None,
    model_name: str | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    from google.genai.errors import APIError
    from google.genai import types

    from app.generation import article_generator

    gemini_client = client or article_generator.client
    selected_model = model_name or article_generator.GEMINI_MODEL
    config = types.GenerateContentConfig(
        temperature=0,
        response_mime_type="application/json",
        response_schema=response_schema,
    )
    service_unavailable_retries = 0
    rate_limit_retried = False
    while True:
        try:
            response = gemini_client.models.generate_content(
                model=selected_model,
                contents=prompt,
                config=config,
            )
            break
        except APIError as exc:
            if (
                exc.code == 503
                and service_unavailable_retries
                < MAX_SERVICE_UNAVAILABLE_RETRIES
            ):
                retry_delay = get_gemini_retry_delay(exc)
                if retry_delay is None:
                    retry_delay = 2 ** service_unavailable_retries
                if retry_delay <= MAX_SERVICE_UNAVAILABLE_RETRY_DELAY_SECONDS:
                    sleep(retry_delay)
                    service_unavailable_retries += 1
                    continue

            retry_delay = get_gemini_retry_delay(exc)
            if (
                exc.code == 429
                and not rate_limit_retried
                and is_per_minute_quota_error(exc)
                and retry_delay is not None
                and retry_delay <= MAX_RATE_LIMIT_RETRY_DELAY_SECONDS
            ):
                sleep(retry_delay)
                rate_limit_retried = True
                continue

            raise

    if not response or not response.text:
        raise RuntimeError("Gemini returned an empty verification response.")

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini returned invalid JSON during claim verification."
        ) from exc

    if not isinstance(result, dict):
        raise RuntimeError(
            "Gemini verification response must be a JSON object."
        )

    return result
