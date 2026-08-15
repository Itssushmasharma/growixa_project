import csv
import io
import json
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_api.auth.rate_limit import RateLimitExceededError, enforce_rate_limit
from growixa_api.db import get_session
from growixa_api.email_validation.providers.factory import get_effective_email_validation_provider
from growixa_api.email_validation.schemas import EmailValidationIn, EmailValidationResultOut
from growixa_api.email_validation.services import MAX_BULK_ROWS, validate_email, validate_emails
from growixa_api.permissions.dependencies import get_current_account_id, require_permission
from growixa_api.redis import get_redis

router = APIRouter(prefix="/email-validation", tags=["email-validation"])

_require_view = require_permission("contacts.view")

_VALIDATION_COLUMNS = ("validation_status", "validation_reasons")


async def _enforce_bulk_rate_limit(redis_client: Redis, request: Request) -> None:
    """Each bulk call can trigger up to MAX_BULK_ROWS synchronous DNS lookups -- without a
    limit, a scripted loop of bulk-CSV calls could turn this endpoint into a DNS-query
    amplifier against the platform's own outbound resolver. Keyed on source IP, same shape
    as the login/coupon-redemption limiters (THREAT_MODEL.md pattern)."""
    ip = request.client.host if request.client else "unknown"
    try:
        await enforce_rate_limit(redis_client, bucket="email_validation_bulk", identifier=ip)
    except RateLimitExceededError as exc:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Please try again later."
        ) from exc


@router.get("/availability")
async def get_availability_route(
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    """Tells the frontend whether a real-time vendor check is even reachable for this
    account (paid plan + an active platform vendor configured) -- lets the "use
    real-time verification" checkbox render only when it would actually do anything,
    without running an actual check just to find out."""
    provider = await get_effective_email_validation_provider(session, account_id)
    return {"realtime_available": provider is not None}


@router.post("/check", response_model=EmailValidationResultOut)
async def check_email_route(
    payload: EmailValidationIn,
    _actor_id: uuid.UUID = Depends(_require_view),
    account_id: uuid.UUID = Depends(get_current_account_id),
    session: AsyncSession = Depends(get_session),
) -> EmailValidationResultOut:
    provider = (
        await get_effective_email_validation_provider(session, account_id)
        if payload.use_realtime
        else None
    )
    return await validate_email(payload.email, provider=provider)


@router.post("/bulk-csv")
async def bulk_validate_csv_route(
    request: Request,
    file: UploadFile = File(...),
    _actor_id: uuid.UUID = Depends(_require_view),
    redis_client: Redis = Depends(get_redis),
) -> Response:
    await _enforce_bulk_rate_limit(redis_client, request)

    raw = await file.read()
    try:
        csv_text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File must be UTF-8 encoded CSV") from exc

    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 'CSV must have a header column named "email"'
        )
    email_column = next(
        (name for name in reader.fieldnames if name.strip().lower() == "email"), None
    )
    if email_column is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 'CSV must have a header column named "email"'
        )

    rows = list(reader)
    if len(rows) > MAX_BULK_ROWS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"CSV has {len(rows)} rows; this tool supports up to {MAX_BULK_ROWS} rows per upload",
        )

    emails = [(row.get(email_column) or "").strip() for row in rows]
    non_empty = [email for email in emails if email]
    results_by_email = {result.email: result for result in await validate_emails(non_empty)}

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[*reader.fieldnames, *_VALIDATION_COLUMNS])
    writer.writeheader()

    counts = {"VALID": 0, "INVALID": 0, "DISPOSABLE": 0, "ROLE": 0}
    for row, email in zip(rows, emails, strict=True):
        result = results_by_email.get(email)
        if result is None:
            writer.writerow({**row, "validation_status": "", "validation_reasons": "empty email"})
            continue
        counts[result.status] += 1
        writer.writerow(
            {
                **row,
                "validation_status": result.status,
                "validation_reasons": "; ".join(result.reasons),
            }
        )

    summary = {"total": len(non_empty), **{k.lower(): v for k, v in counts.items()}}
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="email-validation-results.csv"',
            "X-Validation-Summary": json.dumps(summary),
        },
    )
