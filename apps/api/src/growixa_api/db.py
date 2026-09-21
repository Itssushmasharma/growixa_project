from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from growixa_api.config import get_settings


class Base(DeclarativeBase):
    pass


def _normalize_database_url(url: str) -> str:
    """
    Normalize DATABASE_URL to use asyncpg driver and handle quotes, spaces, schemes,
    and accidentally pasted key prefixes (e.g. DATABASE_URL=...).
    """
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


engine = create_async_engine(
    _normalize_database_url(get_settings().database_url),
    pool_pre_ping=True,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession | None, None]:
    try:
        async with async_session_factory() as session:
            yield session
    except Exception:
        yield None
