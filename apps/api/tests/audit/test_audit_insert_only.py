"""Insert-only enforcement test (GRX-AUDIT-001 / THREAT_MODEL.md T10).

Static/unit-tier: no database needed. Introspects the audit module's public surface and
asserts no function even named like an update/delete operation exists, so a future change
can't quietly add a mutation path for an insert-only table.
"""

import inspect

from growixa_api.audit import repositories, services

_FORBIDDEN_SUBSTRINGS = ("update", "delete", "modify", "edit")


def _public_function_names(module: object) -> list[str]:
    return [
        name
        for name, member in inspect.getmembers(module, inspect.isfunction)
        if not name.startswith("_")
    ]


def test_audit_repositories_has_no_update_or_delete_function() -> None:
    names = _public_function_names(repositories)
    assert names, "expected at least one public function to audit"
    for name in names:
        lowered = name.lower()
        assert not any(word in lowered for word in _FORBIDDEN_SUBSTRINGS), (
            f"growixa_api.audit.repositories.{name} looks like a mutation path on an "
            "insert-only table"
        )


def test_audit_services_has_no_update_or_delete_function() -> None:
    names = _public_function_names(services)
    assert names, "expected at least one public function to audit"
    for name in names:
        lowered = name.lower()
        assert not any(word in lowered for word in _FORBIDDEN_SUBSTRINGS), (
            f"growixa_api.audit.services.{name} looks like a mutation path on an insert-only table"
        )
