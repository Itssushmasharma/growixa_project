from typing import Literal

from pydantic import BaseModel

EmailValidationStatus = Literal["VALID", "INVALID", "DISPOSABLE", "ROLE"]


class EmailValidationIn(BaseModel):
    email: str


class EmailValidationResultOut(BaseModel):
    email: str
    status: EmailValidationStatus
    reasons: list[str]


class BulkEmailValidationSummaryOut(BaseModel):
    total: int
    valid: int
    invalid: int
    disposable: int
    role: int
