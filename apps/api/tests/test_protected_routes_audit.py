"""Route-protection audit test (GRX-RBAC-001).

Per TEST_STRATEGY.md's RBAC section: a dedicated test proves require_permission() is
actually attached to every non-public route, so a future route can't accidentally ship
unprotected. Currently trivial (the only route is the public /health check) — it starts
doing real work the moment the first protected route is added.
"""

from collections.abc import Iterator

from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute
from starlette.routing import BaseRoute

from growixa_api.app import create_app
from growixa_api.permissions.dependencies import RequirePermission

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


def test_every_non_public_route_requires_a_permission() -> None:
    app = create_app()

    routes = list(_iter_api_routes(app.routes))
    assert routes, "expected at least one APIRoute to audit"

    for route in routes:
        if route.path in PUBLIC_ROUTE_PATHS:
            continue
        assert _is_permission_protected(route.dependant), (
            f"{route.path} is neither guarded by require_permission() nor listed in "
            "PUBLIC_ROUTE_PATHS"
        )
