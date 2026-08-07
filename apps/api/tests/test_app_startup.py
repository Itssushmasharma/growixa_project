"""App-level import-graph smoke test.

Regression guard for a real production bug: `growixa_api.accounts.models` (the `Account`
ORM class every `account_id` foreign key points to) was never imported anywhere in
`app.py`'s import graph -- only `migrations/env.py` imported it, for Alembic autogenerate.
SQLAlchemy never registered the `accounts` table in `Base.metadata`, so every
`ForeignKey("accounts.id")` reference failed to resolve the moment SQLAlchemy needed to
order tables for an INSERT (e.g. on the first `/auth/login`, inserting a `RefreshToken`)
-- while `/health` kept returning 200, since it doesn't touch the ORM. `configure_mappers()`
alone does *not* catch this: FK-target resolution for plain Core `ForeignKey` columns (not
`relationship()`) is deferred until a flush actually needs table sort order, so this
checks the real, direct signal instead -- whether the `accounts` table ever made it into
`Base.metadata.tables` at all.

Must run in a fresh subprocess: importing `tests/conftest.py` (as every other test in this
suite implicitly does) already imports `growixa_api.accounts.models` directly for its own
fixtures, which would mask this exact bug if this test shared that process.
"""

import subprocess
import sys


def test_create_app_registers_the_accounts_table_every_account_id_fk_points_to() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from growixa_api.app import create_app\n"
            "from growixa_api.db import Base\n"
            "create_app()\n"
            "assert 'accounts' in Base.metadata.tables, "
            "'accounts table never registered -- growixa_api.accounts.models was never "
            "imported anywhere in the app import graph'\n",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
