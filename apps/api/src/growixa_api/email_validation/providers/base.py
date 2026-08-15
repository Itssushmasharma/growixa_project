from dataclasses import dataclass
from typing import Protocol

from growixa_api.email_validation.schemas import EmailValidationStatus

TIMEOUT_SECONDS = 15.0


class EmailValidationProviderError(Exception):
    """Wraps any failure talking to a real-time email-validation vendor (network, auth,
    or an unrecognized response shape) behind one type, mirroring this codebase's
    AIProviderError/EmailSendError convention."""


@dataclass
class ProviderVerificationResult:
    status: EmailValidationStatus
    reasons: list[str]
    # The vendor's own raw status string, kept for debugging/audit even after mapping
    # to this module's own vocabulary -- useful if the mapping ever needs correcting.
    raw_status: str


class EmailValidationProvider(Protocol):
    """Adapter interface for a real-time, vendor-backed mailbox-verification check
    (GRX-SAAS-016 follow-up pass). One concrete implementation per vendor
    (clearout_provider.py today, more can be added the same way); resolved per account
    by providers/factory.py, gated to paid-plan accounts with an active platform
    config. Deliberately not exposed to the free tier -- see checks.py's own docstring
    for why real mailbox probing isn't self-hosted."""

    async def verify(self, email: str) -> ProviderVerificationResult: ...


# Customer-facing fallback text used when a vendor gives no per-address detail to show
# instead of this module's own `EmailValidationStatus` vocabulary. Lives here, not in
# any one vendor's own adapter file, because it describes *our* status vocabulary
# (INVALID/DISPOSABLE/ROLE/RISKY), not anything Clearout-specific -- every vendor
# adapter reuses the exact same wording, so a customer sees consistent phrasing
# regardless of which vendor the platform admin has configured. Deliberately never
# names a vendor (e.g. "Clearout"): the account only knows "Growixa verified this in
# real time," not which third party did the work.
STATUS_FALLBACK_REASON: dict[str, str] = {
    "INVALID": "This mailbox does not appear to exist",
    "DISPOSABLE": "Domain is a known disposable/throwaway provider",
    "ROLE": "Address looks like a shared role account, not a person",
    "RISKY": "Could not confirm this mailbox's existence with confidence",
}
