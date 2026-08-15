"""Email validation tests (GRX-SAAS-016).

`checks.py`/`services.py` are pure/no-DB, so most of this suite mocks the DNS layer
directly (no real network calls, fast and offline-capable) rather than hitting live
resolvers. The endpoint tests use the real Postgres-backed `user_factory`/RBAC stack
(integration-tier, matching this project's convention) but still mock DNS underneath.
"""

import io
import uuid
from collections.abc import Awaitable, Callable
from unittest.mock import AsyncMock

import dns.exception
import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from growixa_api.app import create_app
from growixa_api.config import get_settings
from growixa_api.email_validation import checks, services
from growixa_api.email_validation.api import _enforce_bulk_rate_limit
from growixa_api.email_validation.services import MAX_BULK_ROWS


def _access_token_cookie(user_id: uuid.UUID) -> dict[str, str]:
    token = jwt.encode({"sub": str(user_id)}, get_settings().jwt_signing_key, algorithm="HS256")
    return {"access_token": token}


class _FakeAnswer(list[object]):
    """dnspython resolve() returns something list-like; len() is all this code checks."""


# ---------------------------------------------------------------------------
# checks.py -- pure logic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "email,expected",
    [
        ("someone@example.com", True),
        ("first.last+tag@sub.example.co.uk", True),
        ("not-an-email", False),
        ("missing-domain@", False),
        ("@missing-local.com", False),
        ("has spaces@example.com", False),
        ("double@@example.com", False),
    ],
)
def test_check_syntax(email: str, expected: bool) -> None:
    assert checks.check_syntax(email) is expected


def test_extract_domain_and_local_part() -> None:
    assert checks.extract_domain("Someone@Example.COM") == "example.com"
    assert checks.extract_local_part("Someone@Example.COM") == "someone"


def test_is_disposable_matches_known_domains() -> None:
    assert checks.is_disposable("mailinator.com") is True
    assert checks.is_disposable("MAILINATOR.COM") is True
    assert checks.is_disposable("gmail.com") is False


def test_is_role_account_matches_known_prefixes() -> None:
    assert checks.is_role_account("admin") is True
    assert checks.is_role_account("ADMIN") is True
    assert checks.is_role_account("jane.doe") is False


@pytest.mark.asyncio
async def test_domain_has_mail_exchanger_true_on_mx_record(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_resolve(self: object, domain: str, rdtype: str) -> _FakeAnswer:
        assert rdtype == "MX"
        return _FakeAnswer([object()])

    monkeypatch.setattr("dns.asyncresolver.Resolver.resolve", fake_resolve)
    assert await checks.domain_has_mail_exchanger("example.com") is True


@pytest.mark.asyncio
async def test_domain_has_mail_exchanger_falls_back_to_a_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_resolve(self: object, domain: str, rdtype: str) -> _FakeAnswer:
        if rdtype == "MX":
            raise dns.exception.DNSException("no MX")  # type: ignore[no-untyped-call]
        if rdtype == "A":
            return _FakeAnswer([object()])
        raise dns.exception.DNSException("no AAAA")  # type: ignore[no-untyped-call]

    monkeypatch.setattr("dns.asyncresolver.Resolver.resolve", fake_resolve)
    assert await checks.domain_has_mail_exchanger("example.com") is True


@pytest.mark.asyncio
async def test_domain_has_mail_exchanger_false_when_nothing_resolves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_resolve(self: object, domain: str, rdtype: str) -> _FakeAnswer:
        raise dns.exception.DNSException("nope")  # type: ignore[no-untyped-call]

    monkeypatch.setattr("dns.asyncresolver.Resolver.resolve", fake_resolve)
    assert await checks.domain_has_mail_exchanger("this-domain-does-not-exist.invalid") is False


# ---------------------------------------------------------------------------
# services.py -- orchestration, mocked at the services-module's own bound name
# (direct-reference imports aren't affected by patching the source module, per this
# project's own established test-authoring gotcha -- see AGENT_HANDOFF.md's GRX-SAAS-013
# entry).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_email_malformed_is_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    mx_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(services, "domain_has_mail_exchanger", mx_mock)

    result = await services.validate_email("not-an-email")
    assert result.status == "INVALID"
    mx_mock.assert_not_called()


@pytest.mark.asyncio
async def test_validate_email_no_mx_is_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(services, "domain_has_mail_exchanger", AsyncMock(return_value=False))

    result = await services.validate_email("someone@example.com")
    assert result.status == "INVALID"
    assert "mail server" in result.reasons[0]


@pytest.mark.asyncio
async def test_validate_email_disposable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(services, "domain_has_mail_exchanger", AsyncMock(return_value=True))

    result = await services.validate_email("test@mailinator.com")
    assert result.status == "DISPOSABLE"


@pytest.mark.asyncio
async def test_validate_email_role_account(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(services, "domain_has_mail_exchanger", AsyncMock(return_value=True))

    result = await services.validate_email("admin@example.com")
    assert result.status == "ROLE"


@pytest.mark.asyncio
async def test_validate_email_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(services, "domain_has_mail_exchanger", AsyncMock(return_value=True))

    result = await services.validate_email("someone@example.com")
    assert result.status == "VALID"
    assert result.reasons == []


@pytest.mark.asyncio
async def test_validate_emails_caches_mx_lookup_per_domain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Three addresses share one domain -- the MX lookup must run once, not three times."""
    mx_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(services, "domain_has_mail_exchanger", mx_mock)

    results = await services.validate_emails(["a@example.com", "b@example.com", "c@example.com"])
    assert all(r.status == "VALID" for r in results)
    assert mx_mock.call_count == 1


@pytest.mark.asyncio
async def test_validate_emails_skips_mx_lookup_for_malformed_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mx_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(services, "domain_has_mail_exchanger", mx_mock)

    results = await services.validate_emails(["not-an-email", "ok@example.com"])
    statuses = {r.email: r.status for r in results}
    assert statuses["not-an-email"] == "INVALID"
    assert statuses["ok@example.com"] == "VALID"
    mx_mock.assert_called_once_with("example.com")


# ---------------------------------------------------------------------------
# Rate limiter wiring (unit-level, no live Redis needed -- same shape as
# test_auth_rate_limit.py's own fake-Redis approach)
# ---------------------------------------------------------------------------


class _AlwaysOverLimitRedis:
    async def incr(self, name: str) -> int:
        return 10_000

    async def expire(self, name: str, time: int) -> bool:
        return True


class _Request:
    def __init__(self) -> None:
        class _Client:
            host = "203.0.113.5"

        self.client = _Client()


@pytest.mark.asyncio
async def test_enforce_bulk_rate_limit_raises_429_once_exceeded() -> None:
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        await _enforce_bulk_rate_limit(_AlwaysOverLimitRedis(), _Request())  # type: ignore[arg-type]
    assert exc_info.value.status_code == 429


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_check_route_requires_authentication() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/email-validation/check", json={"email": "a@example.com"})
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.integration
async def test_check_route_denies_users_without_contacts_view(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    user_id = await user_factory(full_name="No Access", role_name="Content Creator")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(user_id)
    ) as client:
        response = await client.post("/email-validation/check", json={"email": "a@example.com"})
    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_check_route_returns_validation_result(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(services, "domain_has_mail_exchanger", AsyncMock(return_value=True))
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/email-validation/check", json={"email": "test@mailinator.com"}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "DISPOSABLE"
    assert body["email"] == "test@mailinator.com"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bulk_csv_returns_status_column(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(services, "domain_has_mail_exchanger", AsyncMock(return_value=True))
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")

    csv_bytes = b"email,name\nok@example.com,Someone\ntest@mailinator.com,Throwaway\n"

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/email-validation/bulk-csv",
            files={"file": ("contacts.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
    assert response.status_code == 200
    text = response.text
    assert "validation_status" in text
    assert "ok@example.com,Someone,VALID" in text
    assert "test@mailinator.com,Throwaway,DISPOSABLE" in text
    import json

    summary = json.loads(response.headers["x-validation-summary"])
    assert summary == {"total": 2, "valid": 1, "invalid": 0, "disposable": 1, "role": 0}


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bulk_csv_without_email_column_returns_400(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    csv_bytes = b"name\nSomeone\n"

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/email-validation/bulk-csv",
            files={"file": ("contacts.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
    assert response.status_code == 400


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bulk_csv_over_row_cap_returns_400(
    user_factory: Callable[..., Awaitable[uuid.UUID]],
) -> None:
    admin_id = await user_factory(full_name="Test Admin", role_name="Admin")
    rows = "\n".join(f"row{i}@example.com" for i in range(MAX_BULK_ROWS + 1))
    csv_bytes = f"email\n{rows}\n".encode()

    transport = ASGITransport(app=create_app())
    async with AsyncClient(
        transport=transport, base_url="http://test", cookies=_access_token_cookie(admin_id)
    ) as client:
        response = await client.post(
            "/email-validation/bulk-csv",
            files={"file": ("contacts.csv", io.BytesIO(csv_bytes), "text/csv")},
        )
    assert response.status_code == 400
    assert str(MAX_BULK_ROWS) in response.text
