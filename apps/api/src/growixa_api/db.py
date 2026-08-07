from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from growixa_api.config import get_settings


class Base(DeclarativeBase):
    pass


def _normalize_database_url(url: str) -> str:
    """
    Normalize DATABASE_URL to use asyncpg driver if no dialect is specified.
    Render sets DATABASE_URL without a driver prefix (postgresql://...), which defaults to
    psycopg2. This function ensures asyncpg is used explicitly.
    """
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(
    _normalize_database_url(get_settings().database_url), pool_pre_ping=True
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
