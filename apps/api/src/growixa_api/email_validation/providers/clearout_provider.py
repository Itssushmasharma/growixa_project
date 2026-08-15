from dataclasses import dataclass
from typing import Any

import httpx

from growixa_api.email_validation.providers.base import (
    STATUS_FALLBACK_REASON,
    TIMEOUT_SECONDS,
    EmailValidationProviderError,
    ProviderVerificationResult,
)

_VERIFY_URL = "https://api.clearout.io/v2/email_verify/instant"

# Clearout's own documented result categories -> this module's status vocabulary.
# `data.status` == "invalid" (with `data.sub_status` as an object, e.g.
# `{"code": 406, "desc": "Mailbox not found"}`, not a plain string) is confirmed against
# a real API key/response (GRX-SAAS-017); the other statuses (valid/disposable/
# role_based/catch_all/unknown) are still per Clearout's public docs only, not yet
# individually observed. If Clearout's actual field names/values differ from what's
# mapped here, `_parse_response`'s fallback raises a clear error with the raw response
# body rather than silently misclassifying, so the first real call hitting one surfaces
# the mismatch immediately rather than shipping a wrong classification.
_STATUS_MAP: dict[str, str] = {
    "valid": "VALID",
    "invalid": "INVALID",
    "disposable": "DISPOSABLE",
    "role_based": "ROLE",
    "role": "ROLE",
    "catch_all": "RISKY",
    "catch-all": "RISKY",
    "unknown": "RISKY",
    "spamtrap": "INVALID",
}


def _parse_response(payload: dict[str, Any]) -> ProviderVerificationResult:
    data = payload.get("data")
    if not isinstance(data, dict):
        raise EmailValidationProviderError(
            f"Unexpected Clearout response shape (no 'data' object): {payload!r}"
        )

    raw_status = data.get("status")
    if not isinstance(raw_status, str):
        raise EmailValidationProviderError(
            f"Unexpected Clearout response shape (no 'data.status' string): {payload!r}"
        )

    mapped_status = _STATUS_MAP.get(raw_status.lower())
    if mapped_status is None:
        # Fail toward caution, not toward silently trusting an address: an
        # unrecognized status is treated as RISKY rather than VALID. raw_status is kept
        # on the result for internal debugging, but never appears in the customer-facing
        # reason text.
        return ProviderVerificationResult(
            status="RISKY",
            reasons=[STATUS_FALLBACK_REASON["RISKY"]],
            raw_status=raw_status,
        )

    sub_status = data.get("sub_status")
    # Observed live as an object (`{"code": 406, "desc": "Mailbox not found"}`), not the
    # plain string originally assumed -- extract the human-readable description rather
    # than rendering Python's raw dict repr in the UI.
    if isinstance(sub_status, dict):
        sub_status_text = sub_status.get("desc") or sub_status.get("description")
    elif isinstance(sub_status, str):
        sub_status_text = sub_status
    else:
        sub_status_text = None

    reason = sub_status_text or STATUS_FALLBACK_REASON.get(mapped_status)
    return ProviderVerificationResult(
        status=mapped_status,  # type: ignore[arg-type]
        reasons=[reason] if reason else [],
        raw_status=raw_status,
    )


@dataclass
class ClearoutProvider:
    api_key: str

    async def verify(self, email: str) -> ProviderVerificationResult:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(
                    _VERIFY_URL,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"email": email},
                )
        except httpx.HTTPError as exc:
            raise EmailValidationProviderError(f"Could not reach Clearout: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise EmailValidationProviderError(
                f"Non-JSON response from Clearout (HTTP {response.status_code})"
            ) from exc

        if response.is_error:
            message = payload.get("message") if isinstance(payload, dict) else str(payload)
            raise EmailValidationProviderError(
                f"Clearout returned HTTP {response.status_code}: {message}"
            )

        return _parse_response(payload)
