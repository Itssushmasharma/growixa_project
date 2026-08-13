from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from growixa_api.config import get_settings


class Base(DeclarativeBase):
    pass


def _normalize_database_url(url: str) -> str:
    """
    Normalize DATABASE_URL to use asyncpg driver if no dialect is specified.
    Handles postgres://, postgresql://, surrounding quotes, and whitespace.
    """
    if not url:
        return url
    url = url.strip().strip("'\"")
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
    _normalize_database_url(get_settings().database_url), pool_pre_ping=True
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
