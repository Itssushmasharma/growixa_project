import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# RISKY only comes from a real-time vendor call (catch-all domains, ambiguous/unknown
# vendor verdicts) -- the free tier's checks.py can never produce it, since detecting
# "accepts everything" or "couldn't determine" needs an actual mailbox probe.
EmailValidationStatus = Literal["VALID", "INVALID", "DISPOSABLE", "ROLE", "RISKY"]

# Which check level actually produced a result: the free, in-house heuristics, or a
# real-time vendor call (GRX-SAAS-016 follow-up pass, paid plans only).
VerificationLevel = Literal["BASIC", "REALTIME"]


class EmailValidationIn(BaseModel):
    email: str
    # Lets a paid-plan account opt out of the real-time vendor call for a given check
    # and get the free basic result instead -- e.g. to save vendor credits on a quick
    # check. Ignored (has no effect) for accounts with no real-time check available in
    # the first place, so the checkbox can just always render without extra branching
    # in the frontend.
    use_realtime: bool = True


class EmailValidationResultOut(BaseModel):
    email: str
    status: EmailValidationStatus
    reasons: list[str]
    verification_level: VerificationLevel = "BASIC"


class BulkEmailValidationSummaryOut(BaseModel):
    total: int
    valid: int
    invalid: int
    disposable: int
    role: int


class PlatformEmailValidationProviderConfigIn(BaseModel):
    provider: Literal["CLEAROUT"]
    api_key: str


class PlatformEmailValidationProviderConfigOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    provider: Literal["CLEAROUT"]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Never the api_key or its encrypted form, in any response.
