"""Onboard and configure complete IITDeveloper tenant profile, users, and assets.

Usage (run from repo root):
    docker compose exec api python -m growixa_api.cli.onboard_iitdeveloper
    # or locally:
    uv run --directory apps/api python -m growixa_api.cli.onboard_iitdeveloper

Options (env vars):
    ONBOARD_ACCOUNT_EMAIL   target customer user email to onboard (default: admin@growixa.local)
"""

import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select

# Register all tables in Base.metadata for FK resolution
from growixa_api.accounts import models as accounts_models  # noqa: F401
from growixa_api.accounts.models import Account
from growixa_api.ai import models as ai_models  # noqa: F401
from growixa_api.audit import models as audit_models  # noqa: F401
from growixa_api.auth import models as auth_models  # noqa: F401
from growixa_api.auth.encryption import encrypt_secret
from growixa_api.auth.security import hash_password
from growixa_api.billing import models as billing_models  # noqa: F401
from growixa_api.billing.models import (
    AccountCreditBalance,
    AccountSubscription,
    SubscriptionPlan,
)
from growixa_api.brand import models as brand_models  # noqa: F401
from growixa_api.brand.models import BrandProfile
from growixa_api.campaigns import models as campaigns_models  # noqa: F401
from growixa_api.company import models as company_models  # noqa: F401
from growixa_api.company.models import CompanyProfile
from growixa_api.contacts import models as contacts_models  # noqa: F401
from growixa_api.db import async_session_factory
from growixa_api.email_delivery import models as email_delivery_models  # noqa: F401
from growixa_api.email_validation import models as email_validation_models  # noqa: F401
from growixa_api.integrations import models as integrations_models  # noqa: F401
from growixa_api.integrations.models import EmailProviderConnection, SenderIdentity
from growixa_api.notifications import models as notifications_models  # noqa: F401
from growixa_api.permissions import models as permissions_models  # noqa: F401
from growixa_api.platform_admin import models as platform_admin_models  # noqa: F401
from growixa_api.platform_auth import models as platform_auth_models  # noqa: F401
from growixa_api.roles import models as roles_models  # noqa: F401
from growixa_api.roles.models import Role
from growixa_api.social import models as social_models  # noqa: F401
from growixa_api.templates import models as templates_models  # noqa: F401
from growixa_api.users import models as users_models  # noqa: F401
from growixa_api.users.models import User, UserRole

IITDEVELOPER_COMPANY: dict[str, Any] = {
    "name": "IITDeveloper",
    "logo_url": "https://iitdeveloper.com/logo.png",
    "website": "https://iitdeveloper.com",
    "industry": "Custom Software, AI Automation & DevOps",
    "timezone": "Asia/Kolkata",
    "default_language": "en",
    "legal_footer": (
        "© 2019-2026 IITDeveloper. All rights reserved. "
        "Registered Business in India. Remote-First Distributed Engineering Team."
    ),
    "contact_details": {
        "email": "info@iitdeveloper.com",
        "phone": "+91-73027-55534",
        "support_availability": "24/7 Support Available",
        "founded_year": 2019,
        "team_model": "Remote-First Distributed Team",
        "headquarters": "India",
        "tagline": "Custom Software, AI Automation & DevOps for Growing Businesses",
        "services_count": 12,
        "core_services": [
            "Website & Web App Development (Next.js, React, Node.js, Python)",
            "Mobile App Development (iOS & Android)",
            "AI Agents & Autonomous Workflows (LLMs, MCP protocols, automation)",
            "Cloud Infrastructure & DevOps (AWS, GCP, Docker, Kubernetes, CI/CD)",
            "Shopify Store Design & Ecommerce Solutions",
            "Salesforce CRM Consulting & Integrations",
            "Performance Marketing & B2B Lead Generation",
            "SEO & SMM Optimization",
            "Graphic Design, Visual Identity & Motion Graphics",
        ],
        "social_links": {
            "website": "https://iitdeveloper.com",
            "linkedin": "https://www.linkedin.com/in/iitdeveloper-com-655a57213/",
            "github": "https://github.com/iitdeveloper-git",
            "instagram": "https://instagram.com/iitdeveloper_official",
            "x": "https://x.com/developer_iit",
        },
    },
}

IITDEVELOPER_BRAND: dict[str, Any] = {
    "brand_voice": (
        "Direct, witty, engineering-driven, reliable, and results-focused. "
        "We automate things… including your headaches. We turn caffeine into high-performance "
        "code, build production-ready systems, and scale businesses with AI workflows and "
        "modern tech. Fast, reliable, tested on real users, and built to last."
    ),
    "required_facts": [
        (
            "Founded in 2019 as a remote-first engineering and AI automation "
            "company registered in India."
        ),
        (
            "Delivers 12 core services spanning custom web/mobile apps, AI agents, "
            "cloud DevOps, and growth marketing."
        ),
        "Provides 24/7 support availability for production systems and client operations.",
        (
            "Official company website is https://iitdeveloper.com with direct contact "
            "at info@iitdeveloper.com."
        ),
    ],
    "forbidden_claims": [
        (
            "Never make unverified promises of overnight #1 Google ranking or instant traffic "
            "without data."
        ),
        (
            "Never present IITDeveloper as a generic body shop; emphasize senior engineering "
            "ownership and craftsmanship."
        ),
        "Never ship unverified AI hallucinations or non-functional code snippets.",
    ],
}


async def onboard_account(target_email: str) -> None:
    print(f"[*] Onboarding IITDeveloper profile for target email: {target_email}")
    now = datetime.now(UTC)

    async with async_session_factory() as session:
        # 1. Resolve Account
        acc_stmt = (
            select(Account).where(Account.name.ilike("%IIT%")).order_by(Account.created_at.asc())
        )
        account = (await session.execute(acc_stmt)).scalars().first()
        if not account:
            acc_stmt = select(Account).where(
                Account.id == uuid.UUID("00000000-0000-0000-0000-000000000001")
            )
            account = (await session.execute(acc_stmt)).scalar_one()

        account.name = "IITDeveloper"
        print(f"[*] Target Account ID: {account.id} (Name: {account.name})")

        # 2. Get Super Admin role
        role_stmt = select(Role).where(Role.name == "Super Admin")
        super_admin_role = (await session.execute(role_stmt)).scalar_one()

        # 3. Ensure Users
        users_to_ensure = [
            ("admin@iitdeveloper.com", "YourNewSecretPassword123!", "Ravi Kant Yadav"),
            ("info@iitdeveloper.com", "YourNewSecretPassword123!", "IITDeveloper Support"),
            ("ravikantyadav.web@gmail.com", "YourNewSecretPassword123!", "Ravi Kant Yadav"),
            ("admin@growixa.local", "SmokeTest123!", "Admin Lead"),
        ]

        for email, password, full_name in users_to_ensure:
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
                print(f"[+] Created active user: {email} with Super Admin role")
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
                print(f"[+] Updated active user: {email}")

        # 4. Upsert CompanyProfile
        cp_stmt = select(CompanyProfile).where(CompanyProfile.account_id == account.id)
        company_profile = (await session.execute(cp_stmt)).scalar_one_or_none()

        if company_profile is None:
            company_profile = CompanyProfile(
                id=uuid.uuid4(),
                account_id=account.id,
                **IITDEVELOPER_COMPANY,
            )
            session.add(company_profile)
            await session.flush()
            print("[+] Created new CompanyProfile for IITDeveloper")
        else:
            for k, v in IITDEVELOPER_COMPANY.items():
                setattr(company_profile, k, v)
            await session.flush()
            print("[+] Updated existing CompanyProfile for IITDeveloper")

        # 5. Upsert BrandProfile
        bp_stmt = select(BrandProfile).where(BrandProfile.account_id == account.id)
        brand_profile = (await session.execute(bp_stmt)).scalar_one_or_none()

        if brand_profile is None:
            brand_profile = BrandProfile(
                id=uuid.uuid4(),
                account_id=account.id,
                company_id=company_profile.id,
                **IITDEVELOPER_BRAND,
            )
            session.add(brand_profile)
            await session.flush()
            print("[+] Created new BrandProfile for IITDeveloper")
        else:
            brand_profile.company_id = company_profile.id
            for k, v in IITDEVELOPER_BRAND.items():
                setattr(brand_profile, k, v)
            await session.flush()
            print("[+] Updated existing BrandProfile for IITDeveloper")

        # 6. Ensure Pro Plan Subscription
        plan_stmt = select(SubscriptionPlan).where(SubscriptionPlan.slug == "pro")
        pro_plan = (await session.execute(plan_stmt)).scalar_one_or_none()
        if pro_plan:
            sub_stmt = select(AccountSubscription).where(
                AccountSubscription.account_id == account.id
            )
            sub = (await session.execute(sub_stmt)).scalar_one_or_none()
            if sub is None:
                sub = AccountSubscription(
                    id=uuid.uuid4(),
                    account_id=account.id,
                    plan_id=pro_plan.id,
                    status="ACTIVE",
                    billing_interval="MONTHLY",
                    currency="INR",
                    current_period_start=now,
                    current_period_end=now + timedelta(days=365),
                    period_email_used=0,
                    period_ai_used=0,
                )
                session.add(sub)
                print("[+] Created Pro subscription for IITDeveloper")
            else:
                sub.plan_id = pro_plan.id
                sub.status = "ACTIVE"
                sub.current_period_end = now + timedelta(days=365)
                print("[+] Upgraded IITDeveloper subscription to Pro Plan")

        # 7. Ensure Credit Balances
        for credit_type, balance in [("AI_RUNS", 5000), ("EMAIL_SENDS", 100000)]:
            cb_stmt = select(AccountCreditBalance).where(
                AccountCreditBalance.account_id == account.id,
                AccountCreditBalance.credit_type == credit_type,
            )
            cb = (await session.execute(cb_stmt)).scalar_one_or_none()
            if cb is None:
                session.add(
                    AccountCreditBalance(
                        id=uuid.uuid4(),
                        account_id=account.id,
                        credit_type=credit_type,
                        remaining_credits=balance,
                        updated_at=now,
                    )
                )
            else:
                cb.remaining_credits = max(cb.remaining_credits, balance)

        # 8. Ensure Email Provider Connection & Sender Identities
        #
        # Priority rule: if the user has already configured a real SMTP connection via
        # the UI (smtp_host != the onboarding placeholder), prefer that one so test-send
        # and campaign-send always use the user-supplied credentials, not the placeholder.
        all_epc_stmt = select(EmailProviderConnection).where(
            EmailProviderConnection.account_id == account.id,
            EmailProviderConnection.is_active,
        )
        all_epcs = (await session.execute(all_epc_stmt)).scalars().all()

        PLACEHOLDER_HOST = "smtp.iitdeveloper.com"
        # Prefer any real user-configured connection over the placeholder.
        real_epcs = [e for e in all_epcs if e.smtp_host != PLACEHOLDER_HOST]
        placeholder_epcs = [e for e in all_epcs if e.smtp_host == PLACEHOLDER_HOST]

        if real_epcs:
            # User has already configured their own SMTP — use it.
            epc = real_epcs[0]
            # Deactivate the placeholder so it is no longer returned by list endpoints.
            for ph in placeholder_epcs:
                ph.is_active = False
                print(f"[~] Deactivated placeholder SMTP connection: {ph.smtp_host}")
            print(f"[✓] Using real user-configured SMTP: {epc.smtp_host}:{epc.smtp_port}")
        elif placeholder_epcs:
            epc = placeholder_epcs[0]
            print(
                f"[~] Only placeholder SMTP found: {epc.smtp_host}"
                " — configure real SMTP via Settings > Integrations"
            )
        else:
            # No connection at all — create the placeholder so sender identities can be seeded.
            epc = EmailProviderConnection(
                id=uuid.uuid4(),
                account_id=account.id,
                provider="CUSTOM_SMTP",
                smtp_host=PLACEHOLDER_HOST,
                smtp_port=587,
                smtp_username="info@iitdeveloper.com",
                smtp_password_encrypted=encrypt_secret("placeholder_smtp_pw"),
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            session.add(epc)
            await session.flush()
            print("[+] Created placeholder SMTP connection (replace via Settings > Integrations)")

        for from_name, from_email in [
            ("IITDeveloper Team", "info@iitdeveloper.com"),
            ("Ravi Kant Yadav", "ravi@iitdeveloper.com"),
        ]:
            si_stmt = select(SenderIdentity).where(
                SenderIdentity.account_id == account.id,
                SenderIdentity.from_email == from_email,
            )
            si = (await session.execute(si_stmt)).scalars().first()
            if si is None:
                session.add(
                    SenderIdentity(
                        id=uuid.uuid4(),
                        account_id=account.id,
                        email_provider_connection_id=epc.id,
                        from_name=from_name,
                        from_email=from_email,
                        reply_to_email=from_email,
                        verification_status="VERIFIED",
                        created_at=now,
                        updated_at=now,
                    )
                )
            elif si.email_provider_connection_id != epc.id:
                # Reassign to the preferred (real) connection if it changed.
                si.email_provider_connection_id = epc.id
                print(f"[~] Reassigned sender identity {from_email} -> {epc.smtp_host}")

        await session.commit()
        print("\n[✓] Successfully onboarded IITDeveloper profile, users & assets!")


async def main() -> None:
    target_email = os.getenv("ONBOARD_ACCOUNT_EMAIL", "admin@growixa.local").strip()
    await onboard_account(target_email)


if __name__ == "__main__":
    asyncio.run(main())
