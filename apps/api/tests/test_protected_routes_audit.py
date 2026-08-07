"""Route-protection audit test (GRX-RBAC-001).

Per TEST_STRATEGY.md's RBAC section: a dedicated test proves require_permission() is
actually attached to every non-public route, so a future route can't accidentally ship
unprotected. Currently trivial (the only route is the public /health check) — it starts
doing real work the moment the first protected route is added.

Since GRX-SAAS-005 (the first real feature route under require_platform_permission()),
"protected" means guarded by either permission class — the two-classes-never-both
invariant is enforced separately below by
test_no_route_is_guarded_by_both_permission_classes_at_once.
"""

from collections.abc import Iterator

from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute
from starlette.routing import BaseRoute

from growixa_api.app import create_app
from growixa_api.permissions.dependencies import RequirePermission
from growixa_api.platform_auth.dependencies import RequirePlatformPermission

# FastAPI's own /docs, /redoc, /openapi.json routes are plain Starlette Routes, not
# APIRoute, so they're already excluded by the isinstance check below and don't need to be
# listed here. Only application-defined routes that are intentionally public go here.
# /auth/login, /auth/refresh, /auth/logout, /auth/logout-all identify their actor via the
# credential/token in the request body or cookie itself (password, refresh token), not via
# require_permission() — there is no session yet (login) or the route's whole job is
# managing that session directly (refresh/logout/logout-all), so a permission check on top
# would be redundant, not an oversight. /users/invitations/accept is the same shape as
# login: the invitee has no session yet, identity comes from the invitation token itself.
# /auth/me is the same shape as /refresh: identity comes from the access-token cookie
# itself via get_current_user_id(), and any authenticated user may know who they are —
# there's no separate permission to check.
# /webhooks/postmark has no user session at all — Postmark itself is the caller,
# authenticated via HTTP Basic Auth checked against the active connection's own webhook
# credentials (THREAT_MODEL.md's T14), not require_permission(). /unsubscribe/{id} is
# fully public by design: the recipient clicking it has no account, identified only by
# the unguessable campaign_recipient_id UUID in the link itself (same shape as the
# invitation-accept token).
# /platform/auth/login, /platform/auth/logout, /platform/auth/me are the platform-admin
# analogues of the /auth/* routes above, for the exact same reasons — see
# RequirePlatformPermission's own coverage below (GRX-SAAS-002 Phase B).
# /accounts/register and /accounts/verify-email are the same shape as
# /users/invitations/accept: no session exists yet, identity comes from the
# credential/token in the request itself (GRX-SAAS-003 Phase C).
# /accounts/support-session-status is the same shape as /auth/me: identity comes from
# get_current_account_id() via the access-token cookie, and any authenticated user of
# the account may know whether support currently has an active session on it -- there's
# no separate permission to check (GRX-SAAS-010 / DEC-GRX-022 point 6).
PUBLIC_ROUTE_PATHS = {
    "/health",
    "/auth/login",
    "/auth/logout",
    "/auth/refresh",
    "/auth/logout-all",
    "/auth/me",
    "/auth/password-reset/request",
    "/auth/password-reset/complete",
    "/users/invitations/accept",
    "/webhooks/postmark",
    "/unsubscribe/{campaign_recipient_id}",
    "/platform/auth/login",
    "/platform/auth/logout",
    "/platform/auth/me",
    "/accounts/register",
    "/accounts/verify-email",
    "/accounts/support-session-status",
}


def _iter_api_routes(routes: list[BaseRoute]) -> Iterator[APIRoute]:
    # app.include_router(...) doesn't always flatten sub-router routes directly into
    # app.routes (this FastAPI version wraps them, exposing the originals via
    # `original_router`); recurse through that wrapper wherever it appears rather than
    # depending on its private class name.
    for route in routes:
        if isinstance(route, APIRoute):
            yield route
            continue
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            yield from _iter_api_routes(original_router.routes)


def _is_permission_protected(dependant: Dependant) -> bool:
    for dependency in dependant.dependencies:
        if isinstance(dependency.call, RequirePermission):
            return True
        if _is_permission_protected(dependency):
            return True
    return False


def _is_platform_permission_protected(dependant: Dependant) -> bool:
    for dependency in dependant.dependencies:
        if isinstance(dependency.call, RequirePlatformPermission):
            return True
        if _is_platform_permission_protected(dependency):
            return True
    return False


def test_every_non_public_route_requires_a_permission() -> None:
    app = create_app()

    routes = list(_iter_api_routes(app.routes))
    assert routes, "expected at least one APIRoute to audit"

    for route in routes:
        if route.path in PUBLIC_ROUTE_PATHS:
            continue
        protected = _is_permission_protected(route.dependant) or _is_platform_permission_protected(
            route.dependant
        )
        assert protected, (
            f"{route.path} is neither guarded by require_permission() nor "
            "require_platform_permission(), nor listed in PUBLIC_ROUTE_PATHS"
        )


def test_require_permission_and_require_platform_permission_are_distinct_classes() -> None:
    """GRX-SAAS-002 Phase B's own acceptance criterion: the two dependency classes must
    be structurally separate, not the same function with a flag — accidentally using
    the wrong one on a route must be a type error waiting to happen, not a runtime
    footgun. See RBAC.md's Sprint 5 Phase B section and THREAT_MODEL.md's T21."""
    assert not issubclass(RequirePlatformPermission, RequirePermission)
    assert not issubclass(RequirePermission, RequirePlatformPermission)


def test_no_route_is_guarded_by_both_permission_classes_at_once() -> None:
    """No route may accidentally mix an account-scoped permission check with a
    platform-scoped one — that combination would mean a route is reachable by whichever
    identity class satisfies either check, defeating the whole point of the boundary."""
    app = create_app()

    routes = list(_iter_api_routes(app.routes))
    assert routes, "expected at least one APIRoute to audit"

    for route in routes:
        account_scoped = _is_permission_protected(route.dependant)
        platform_scoped = _is_platform_permission_protected(route.dependant)
        assert not (account_scoped and platform_scoped), (
            f"{route.path} is guarded by both require_permission() and "
            "require_platform_permission() — a route must use exactly one identity "
            "class's dependency, never both"
        )
