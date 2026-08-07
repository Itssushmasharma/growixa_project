"""One-time platform admin seed command.

Usage:
    docker compose exec api python -m growixa_api.cli.seed_platform_admin
    # or, on Render: open the api service's Shell tab and run the same command.

Reads PLATFORM_ADMIN_EMAIL / PLATFORM_ADMIN_PASSWORD (and optionally
PLATFORM_ADMIN_FULL_NAME) from the environment -- same convention .env.example
already documents for the customer-side FIRST_ADMIN_EMAIL/PASSWORD seed. Idempotent:
does nothing but print a message if a platform_admins row with that email already
exists, so it is safe to re-run (e.g. after every deploy) without creating duplicates
or erroring.

Seeds role=platform.owner -- full platform control, per RBAC.md's Sprint 5 Phase B
role table -- since this is meant to be the one account an operator uses to configure
everything else (accounts, usage/campaign oversight, and any future platform.*
capability).
"""

import asyncio
import os
import sys

from sqlalchemy import select

from growixa_api.auth.security import hash_password
from growixa_api.db import async_session_factory
from growixa_api.platform_auth.models import PlatformAdmin


async def main() -> int:
    email = os.environ.get("PLATFORM_ADMIN_EMAIL")
    password = os.environ.get("PLATFORM_ADMIN_PASSWORD")
    full_name = os.environ.get("PLATFORM_ADMIN_FULL_NAME", "Platform Owner")

    if not email or not password:
        print(
            "PLATFORM_ADMIN_EMAIL and PLATFORM_ADMIN_PASSWORD must both be set.",
            file=sys.stderr,
        )
        return 1

    async with async_session_factory() as session:
        existing = await session.execute(select(PlatformAdmin).where(PlatformAdmin.email == email))
        if existing.scalar_one_or_none() is not None:
            print(f"Platform admin {email} already exists -- nothing to do.")
            return 0

        admin = PlatformAdmin(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role="platform.owner",
        )
        session.add(admin)
        await session.commit()

    print(f"Created platform admin {email} (role=platform.owner).")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
