from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from growixa_worker.config import get_settings


class Base(DeclarativeBase):
    pass


def _normalize_database_url(url: str) -> str:
    if not url:
        return url
    url = url.strip().strip("'\"")
    for prefix in (
        "export DATABASE_URL=",
        "DATABASE_URL=",
        "DATABASE_URL:",
        "DATABASE_URL = ",
        "DATABASE_URL : ",
    ):
        if url.startswith(prefix):
            url = url[len(prefix) :].strip().strip("'\"")
    if url.startswith("psql "):
        url = url[5:].strip().strip("'\"")
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + url[len("postgresql+psycopg2://") :]
    if url.startswith("postgresql+psycopg://"):
        return "postgresql+asyncpg://" + url[len("postgresql+psycopg://") :]
    return url


def _make_session_factory() -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(
        _normalize_database_url(get_settings().database_url), pool_pre_ping=True
    )
    return async_sessionmaker(engine, expire_on_commit=False)


_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = _make_session_factory()
    return _session_factory
