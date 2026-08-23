"""Dynamic Personalization Renderer for Growixa Worker (DEC-GRX-036 / GRX-CONTENT-001).

Channel-agnostic token renderer supporting:
1. Two token scopes: Recipient-scope and Account/Sender-scope.
2. Bounded regex token parsing: `{{ token_name }}` and `{{ token_name | default:"fallback" }}`.
3. Strict allowlist: only declared standard fields and account custom fields where
   `is_personalization_usable` is true.
4. Internal fields (source, id, account_id, timestamps, etc.) are strictly prohibited.
5. Default fallback filter (`| default:"..."`) support.
6. Automatic HTML escaping for untrusted values when `is_html=True`.
7. Unknown tokens and unhandled missing values block execution.
"""

from __future__ import annotations

import html
import re
from typing import Any

# Standard recipient-scope fields
RECIPIENT_STANDARD_TOKENS: frozenset[str] = frozenset(
    {"first_name", "last_name", "email", "phone", "unsubscribe_url"}
)

# Standard account/sender-scope fields
ACCOUNT_TOKENS: frozenset[str] = frozenset({"company_name", "website_url", "sender_name"})

# Explicitly prohibited internal / sensitive fields that must NEVER be resolved or rendered
PROHIBITED_FIELDS: frozenset[str] = frozenset(
    {
        "id",
        "account_id",
        "created_by_user_id",
        "status",
        "deleted_at",
        "created_at",
        "updated_at",
        "source",
    }
)

# Regex to match {{ token }} or {{ token | default:"fallback" }} or {{ token | default:'fallback' }}
# Bounded pattern: only alphanumeric + underscores for token names, optional default filter.
TOKEN_PATTERN = re.compile(
    r"\{\{\s*([a-zA-Z0-9_]+)(?:\s*\|\s*default:\s*(?:\"([^\"]*)\"|'([^']*)'))?\s*\}\}"
)

# Catch-all pattern to detect malformed or unclosed {{ ... }} tags
GENERIC_CURLY_PATTERN = re.compile(r"\{\{([^{}]*)\}\}")


class PersonalizationError(Exception):
    """Base class for all personalization errors."""


class UnknownTokenError(PersonalizationError):
    """Raised when an unknown, prohibited, or unusable token is encountered."""

    def __init__(
        self,
        token: str,
        message: str | None = None,
        *,
        allowed_tokens: set[str] | frozenset[str] | None = None,
    ) -> None:
        self.token = token
        if message:
            err_msg = message
        else:
            avail = (
                ", ".join(f"{{{{{t}}}}}" for t in sorted(allowed_tokens)) if allowed_tokens else ""
            )
            err_msg = f"Invalid personalization token '{{{{{token}}}}}'."
            if avail:
                err_msg += f" Available tokens: {avail}"
            else:
                err_msg = f"Unknown or unauthorized personalization token '{{{{{token}}}}}'"
        super().__init__(err_msg)


class MissingTokenValueError(PersonalizationError):
    """Raised when recipient is missing a token value and no default was provided."""

    def __init__(self, token: str, recipient: str | None = None) -> None:
        self.token = token
        self.recipient = recipient
        if not recipient:
            msg = f"Missing value for token '{{{{{token}}}}}' with no fallback default"
        else:
            msg = (
                f"Recipient '{recipient}' is missing a value for token "
                f"'{{{{{token}}}}}' with no fallback default"
            )
        super().__init__(msg)


def extract_template_tokens(template_str: str) -> list[tuple[str, str | None]]:
    """Extracts all valid (token_name, default_value) pairs from a template string."""
    if not template_str:
        return []
    results: list[tuple[str, str | None]] = []
    for match in TOKEN_PATTERN.finditer(template_str):
        token_name = match.group(1)
        default_val = match.group(2) if match.group(2) is not None else match.group(3)
        results.append((token_name, default_val))
    return results


def validate_template_tokens(
    template_str: str,
    *,
    allowed_custom_field_keys: set[str] | frozenset[str] | None = None,
    is_broadcast: bool = False,
) -> None:
    """Validates that all tokens in template_str are syntactically valid and allowed.

    Raises:
        UnknownTokenError: If any unknown token, prohibited field, or malformed tag is encountered.
    """
    if not template_str:
        return

    allowed_custom = set(allowed_custom_field_keys or set())
    allowed_recipient = RECIPIENT_STANDARD_TOKENS | allowed_custom
    all_allowed = ACCOUNT_TOKENS | (set() if is_broadcast else allowed_recipient)

    # First, check for malformed double braces
    for match in GENERIC_CURLY_PATTERN.finditer(template_str):
        raw_inside = match.group(0)
        if not TOKEN_PATTERN.fullmatch(raw_inside):
            # Malformed token syntax e.g. {{invalid syntax!}}
            token_candidate = raw_inside.strip("{} ").split("|")[0].strip()
            raise UnknownTokenError(
                token_candidate,
                f"Invalid or malformed personalization token '{raw_inside}'",
            )

    # Next, check token permissions and allowlist
    for match in TOKEN_PATTERN.finditer(template_str):
        token = match.group(1)
        if token in PROHIBITED_FIELDS:
            raise UnknownTokenError(
                token,
                f"Personalization token '{{{{{token}}}}}' is an internal field and not permitted",
            )

        if token in ACCOUNT_TOKENS:
            continue

        if token in allowed_recipient:
            if is_broadcast:
                raise UnknownTokenError(
                    token,
                    f"Recipient-scope token '{{{{{token}}}}}' is not allowed on broadcast channels",
                )
            continue

        # If it reaches here, token is not recognized
        raise UnknownTokenError(token, allowed_tokens=all_allowed)


def render_personalization(
    template_str: str,
    *,
    recipient_data: dict[str, Any] | None = None,
    account_data: dict[str, Any] | None = None,
    allowed_custom_field_keys: set[str] | frozenset[str] | None = None,
    is_html: bool = False,
    recipient_identifier: str | None = None,
) -> str:
    """Renders dynamic personalization tokens in template_str.

    Args:
        template_str: The text/HTML content containing tokens like `{{first_name}}`.
        recipient_data: Dict of recipient attributes (first_name, custom fields, etc.).
        account_data: Dict of account attributes (company_name, website_url, sender_name).
        allowed_custom_field_keys: Set of custom field keys authorized for personalization.
        is_html: If True, substituted values will be HTML-escaped.
        recipient_identifier: Optional recipient email or ID for error messages.

    Returns:
        Rendered string with all tokens substituted.

    Raises:
        UnknownTokenError: If an unauthorized or unknown token is found.
        MissingTokenValueError: If a recipient is missing a token value with no default filter.
    """
    if not template_str:
        return template_str

    validate_template_tokens(
        template_str,
        allowed_custom_field_keys=allowed_custom_field_keys,
        is_broadcast=(recipient_data is None),
    )

    recipient = recipient_data or {}
    account = account_data or {}

    def _replace_token(match: re.Match[str]) -> str:
        token = match.group(1)
        default_val = match.group(2) if match.group(2) is not None else match.group(3)

        value: Any = None
        if token in account:
            value = account[token]
        elif token in recipient:
            value = recipient[token]

        # Check if value is present and non-empty
        if value is not None and str(value).strip() != "":
            rendered_str = str(value)
        elif default_val is not None:
            rendered_str = default_val
        else:
            rec_id = recipient_identifier or recipient.get("email")
            raise MissingTokenValueError(token, recipient=rec_id)

        if is_html:
            return html.escape(rendered_str, quote=True)
        return rendered_str

    return TOKEN_PATTERN.sub(_replace_token, template_str)
