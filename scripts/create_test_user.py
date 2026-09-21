import os
import sys
from dotenv import load_dotenv

# Explicitly load apps/api/.env before importing growixa_api modules
env_path = os.path.join(os.path.dirname(__file__), "..", "apps", "api", ".env")
load_dotenv(env_path)

import asyncio
import uuid
from datetime import datetime, timezone
UTC = timezone.utc
from sqlalchemy import select

from growixa_api.db import async_session_factory
from growixa_api.accounts.models import Account
from growixa_api.roles.models import Role
from growixa_api.users.models import User, UserRole
from growixa_api.company.models import CompanyProfile
from growixa_api.brand.models import BrandProfile
from growixa_api.auth.security import hash_password

async def seed_user():
    now = datetime.now(UTC)
    async with async_session_factory() as session:
        # 1. Resolve or ensure Account
        acc_stmt = select(Account).where(Account.id == uuid.UUID("00000000-0000-0000-0000-000000000001"))
        account = (await session.execute(acc_stmt)).scalar_one_or_none()
        if not account:
            account = Account(
                id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                name="Growixa Primary Account",
                status="ACTIVE"
            )
            session.add(account)
            await session.flush()
            print("[+] Created primary Account.")
        else:
            print(f"[*] Found Account: {account.name} ({account.id})")

        # 2. Find Super Admin role
        role_stmt = select(Role).where(Role.name == "Super Admin")
        super_admin_role = (await session.execute(role_stmt)).scalar_one()

        # 3. Create users
        test_pwd = os.getenv("TEST_USER_PASSWORD", "dev_mock_password_123")
        test_users = [
            ("test@growixa.local", test_pwd, "Growixa Tester"),
            ("admin@growixa.local", test_pwd, "Admin Lead"),
            ("admin@iitdeveloper.local", test_pwd, "IITDeveloper Admin"),
        ]

        for email, password, full_name in test_users:
            u_stmt = select(User).where(User.email == email)
            user = (await session.execute(u_stmt)).scalar_one_or_none()
            if user is None:
                user = User(
                    id=uuid.uuid4(),
                    account_id=account.id,
                    email=email,
                    password_hash=hash_password(password),
                    full_name=full_name,
                    status="ACTIVE",
                    created_at=now,
                    updated_at=now,
                )
                session.add(user)
                await session.flush()
                session.add(
                    UserRole(
                        account_id=account.id,
                        user_id=user.id,
                        role_id=super_admin_role.id,
                    )
                )
                print(f"[+] Created test user: {email}")
            else:
                user.account_id = account.id
                user.status = "ACTIVE"
                user.password_hash = hash_password(password)
                user.full_name = full_name
                ur_stmt = select(UserRole).where(UserRole.user_id == user.id)
                ur = (await session.execute(ur_stmt)).scalars().first()
                if not ur:
                    session.add(
                        UserRole(
                            account_id=account.id,
                            user_id=user.id,
                            role_id=super_admin_role.id,
                        )
                    )
                print(f"[*] Updated existing user: {email}")

        # 4. Ensure CompanyProfile exists
        cp_stmt = select(CompanyProfile).where(CompanyProfile.account_id == account.id)
        cp = (await session.execute(cp_stmt)).scalar_one_or_none()
        if cp is None:
            cp = CompanyProfile(
                id=uuid.uuid4(),
                account_id=account.id,
                name="Growixa Growth Team",
                website="http://localhost:3000",
                industry="Marketing & Analytics",
                timezone="UTC",
                default_language="en",
            )
            session.add(cp)
            print("[+] Created default CompanyProfile.")

        # 5. Ensure BrandProfile exists
        bp_stmt = select(BrandProfile).where(BrandProfile.account_id == account.id)
        bp = (await session.execute(bp_stmt)).scalar_one_or_none()
        if bp is None:
            bp = BrandProfile(
                id=uuid.uuid4(),
                account_id=account.id,
                company_id=cp.id,
                brand_voice="Professional, Analytical, High Growth",
                persona_tags=["Professional", "Confident"],
                voice_settings={"formality": 75, "energy": 80, "technical_depth": 70},
            )
            session.add(bp)
            print("[+] Created default BrandProfile.")

        await session.commit()
        print("[SUCCESS] All test users and company profiles initialized!")

if __name__ == "__main__":
    asyncio.run(seed_user())
