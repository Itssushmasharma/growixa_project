"""Migration smoke test (GRX-FOUND-005).

Integration-tier test per TEST_STRATEGY.md §Database migration tests — it requires a real,
reachable PostgreSQL instance (the Compose `postgres` service) and is intentionally a plain
sync test: Alembic's async env.py drives its own event loop via `asyncio.run(...)`
internally, which cannot be nested inside an already-running (pytest-asyncio) event loop.
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from growixa_api.config import get_settings

ALEMBIC_INI = Path(__file__).resolve().parent.parent.parent / "alembic.ini"


def _sync_database_url() -> str:
    return get_settings().database_url.replace("+asyncpg", "+psycopg")


def _current_revisions() -> set[str]:
    engine = create_engine(_sync_database_url())
    try:
        with engine.connect() as conn:
            if "alembic_version" not in inspect(conn).get_table_names():
                return set()
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            return {row[0] for row in result}
    finally:
        engine.dispose()


@pytest.mark.integration
def test_alembic_upgrade_head_then_downgrade_base_round_trips_cleanly() -> None:
    config = Config(str(ALEMBIC_INI))
    expected_head = ScriptDirectory.from_config(config).get_current_head()

    command.upgrade(config, "head")
    assert _current_revisions() == {expected_head}

    command.downgrade(config, "base")
    assert _current_revisions() == set()

    command.upgrade(config, "head")
    assert _current_revisions() == {expected_head}
