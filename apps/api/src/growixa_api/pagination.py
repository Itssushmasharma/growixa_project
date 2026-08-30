"""Shared pagination convention for `GET` list endpoints (GRX-PERF-001).

Every paginated list route uses the same two query params:

- ``limit``: page size. Defaults to :data:`DEFAULT_LIMIT` when omitted. A client-requested
  value above :data:`MAX_LIMIT` is **clamped down to the max, not rejected** (matches how
  optional query params are handled elsewhere in this codebase).
- ``offset``: rows to skip. Defaults to ``0``.

Response shape is intentionally unchanged: routes keep returning a bare ``list[X]``
(``response_model=list[X]``), never an ``{items, total, limit, offset}`` envelope — an
envelope is a coordinated, breaking API/frontend change out of scope here (see the
`GRX-PERF-001` row in `docs/00-project-control/MASTER_TASK_TRACKER.md`).

``LIMIT``/``OFFSET`` must always be applied at the SQL level via SQLAlchemy's
``.limit()``/``.offset()`` in the repository layer — never fetch-then-slice in Python.

Reuse this module for every future paginated list endpoint (`GRX-PERF-002`) instead of
re-deriving the convention.
"""

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


def clamp_limit(limit: int) -> int:
    """Clamp a client-requested page size into ``[1, MAX_LIMIT]``.

    A non-positive value falls back to :data:`DEFAULT_LIMIT` rather than being rejected,
    and a value above :data:`MAX_LIMIT` is capped at the max — the client's request is
    always honored as closely as possible instead of erroring.
    """
    if limit < 1:
        return DEFAULT_LIMIT
    return min(limit, MAX_LIMIT)
