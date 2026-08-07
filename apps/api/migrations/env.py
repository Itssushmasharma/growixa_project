import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Imported for their side effect of registering tables on Base.metadata (required for
# --autogenerate); the modules themselves are otherwise unused here.
from growixa_api.accounts import models as accounts_models  # noqa: F401
from growixa_api.audit import models as audit_models  # noqa: F401
from growixa_api.auth import models as auth_models  # noqa: F401
from growixa_api.brand import models as brand_models  # noqa: F401
from growixa_api.campaigns import models as campaigns_models  # noqa: F401
from growixa_api.company import models as company_models  # noqa: F401
from growixa_api.config import get_settings
from growixa_api.contacts import models as contacts_models  # noqa: F401
from growixa_api.db import Base
from growixa_api.email_delivery import models as email_delivery_models  # noqa: F401
from growixa_api.integrations import models as integrations_models  # noqa: F401
from growixa_api.permissions import models as permissions_models  # noqa: F401
from growixa_api.platform_auth import models as platform_auth_models  # noqa: F401
from growixa_api.roles import models as roles_models  # noqa: F401
from growixa_api.templates import models as templates_models  # noqa: F401
from growixa_api.usage import models as usage_models  # noqa: F401
from growixa_api.users import models as users_models  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
