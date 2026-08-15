"""Development demo-data seed command.

Populates a local dev account with realistic contacts, contact lists, email templates,
campaigns (DRAFT/SCHEDULED only), and social posts (DRAFT/SCHEDULED/PUBLISHED)
so that every dashboard page shows rich, meaningful data immediately.

Usage (run from repo root):
    docker compose exec api python -m growixa_api.cli.seed_demo_data
    # or locally:
    uv run --directory apps/api python -m growixa_api.cli.seed_demo_data

Options (env vars):
    SEED_ACCOUNT_EMAIL   email of the customer account to seed into
                         (default: admin@growixa.local)
    SEED_FORCE           set to "1" to wipe existing seed data and re-seed

Safe by design:
  - Never touches platform_admins, billing rows, or RBAC permission tables.
  - Idempotent: skips resources that already exist unless SEED_FORCE=1.
  - Campaign seeding is DRAFT/SCHEDULED only — no dispatching is triggered.
"""

import asyncio
import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from typing import TypedDict

from sqlalchemy import delete as sa_delete
from sqlalchemy import select

# Register all tables in Base.metadata for FK resolution
from growixa_api.accounts import models as accounts_models  # noqa: F401
from growixa_api.ai import models as ai_models  # noqa: F401
from growixa_api.audit import models as audit_models  # noqa: F401
from growixa_api.auth import models as auth_models  # noqa: F401
from growixa_api.auth.encryption import encrypt_secret
from growixa_api.billing import models as billing_models  # noqa: F401
from growixa_api.brand import models as brand_models  # noqa: F401
from growixa_api.campaigns import models as campaigns_models  # noqa: F401
from growixa_api.campaigns.models import Campaign, CampaignRecipient, CampaignVersion
from growixa_api.company import models as company_models  # noqa: F401
from growixa_api.contacts import models as contacts_models  # noqa: F401
from growixa_api.contacts.models import (
    Contact,
    ContactList,
    ContactListMember,
    ContactTag,
    Tag,
)
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
from growixa_api.social import models as social_models  # noqa: F401
from growixa_api.social.models import (
    SocialConnection,
    SocialPost,
    SocialPostMedia,
    SocialPostVersion,
)
from growixa_api.templates import models as templates_models  # noqa: F401
from growixa_api.templates.models import EmailTemplate, EmailTemplateVersion
from growixa_api.usage import models as usage_models  # noqa: F401
from growixa_api.users import models as users_models  # noqa: F401
from growixa_api.users.models import User


class ContactData(TypedDict):
    email: str
    first_name: str
    last_name: str
    status: str
    tags: list[str]


class ListData(TypedDict):
    name: str
    tag: str


class TemplateData(TypedDict):
    name: str
    subject: str
    body_html: str


class SocialPostData(TypedDict):
    caption: str
    status: str
    days_offset: int


class CampaignData(TypedDict):
    name: str
    subject: str
    body_html: str
    status: str
    days_offset: int | None


# ---------------------------------------------------------------------------
# Demo data definitions
# ---------------------------------------------------------------------------

CONTACTS: list[ContactData] = [
    {
        "email": "alex.morgan@techcorp.io",
        "first_name": "Alex",
        "last_name": "Morgan",
        "status": "ACTIVE",
        "tags": ["VIP", "Enterprise"],
    },
    {
        "email": "sarah.chen@innovate.co",
        "first_name": "Sarah",
        "last_name": "Chen",
        "status": "ACTIVE",
        "tags": ["Lead", "SaaS"],
    },
    {
        "email": "james.rodriguez@startup.io",
        "first_name": "James",
        "last_name": "Rodriguez",
        "status": "ACTIVE",
        "tags": ["Lead"],
    },
    {
        "email": "priya.patel@globalcorp.com",
        "first_name": "Priya",
        "last_name": "Patel",
        "status": "ACTIVE",
        "tags": ["Enterprise", "VIP"],
    },
    {
        "email": "liam.johnson@agency.co",
        "first_name": "Liam",
        "last_name": "Johnson",
        "status": "ACTIVE",
        "tags": [],
    },
    {
        "email": "nina.kowalski@design.io",
        "first_name": "Nina",
        "last_name": "Kowalski",
        "status": "ACTIVE",
        "tags": ["Creative"],
    },
    {
        "email": "omar.hassan@fintech.com",
        "first_name": "Omar",
        "last_name": "Hassan",
        "status": "ACTIVE",
        "tags": ["Enterprise"],
    },
    {
        "email": "emily.wang@retail.shop",
        "first_name": "Emily",
        "last_name": "Wang",
        "status": "ACTIVE",
        "tags": ["SaaS"],
    },
    {
        "email": "marcus.lee@ventures.vc",
        "first_name": "Marcus",
        "last_name": "Lee",
        "status": "ACTIVE",
        "tags": ["VIP", "Lead"],
    },
    {
        "email": "sofia.garcia@media.net",
        "first_name": "Sofia",
        "last_name": "Garcia",
        "status": "ACTIVE",
        "tags": ["Creative"],
    },
    {
        "email": "henry.wilson@logistics.io",
        "first_name": "Henry",
        "last_name": "Wilson",
        "status": "ACTIVE",
        "tags": [],
    },
    {
        "email": "anna.brown@healthtech.co",
        "first_name": "Anna",
        "last_name": "Brown",
        "status": "ACTIVE",
        "tags": ["Lead"],
    },
    {
        "email": "dev.null@bounced.example",
        "first_name": "Dev",
        "last_name": "Null",
        "status": "ARCHIVED",
        "tags": [],
    },
    {
        "email": "test.user@legacy.org",
        "first_name": "Test",
        "last_name": "User",
        "status": "ARCHIVED",
        "tags": [],
    },
    {
        "email": "carlos.ruiz@ecommerce.io",
        "first_name": "Carlos",
        "last_name": "Ruiz",
        "status": "ACTIVE",
        "tags": ["SaaS", "Enterprise"],
    },
    {
        "email": "mei.zhang@marketplace.co",
        "first_name": "Mei",
        "last_name": "Zhang",
        "status": "ACTIVE",
        "tags": ["Lead"],
    },
    {
        "email": "david.kim@cloudops.dev",
        "first_name": "David",
        "last_name": "Kim",
        "status": "ACTIVE",
        "tags": ["VIP"],
    },
    {
        "email": "ines.dupont@fashion.fr",
        "first_name": "Ines",
        "last_name": "Dupont",
        "status": "ACTIVE",
        "tags": ["Creative"],
    },
    {
        "email": "tom.nguyen@gaming.gg",
        "first_name": "Tom",
        "last_name": "Nguyen",
        "status": "ACTIVE",
        "tags": [],
    },
    {
        "email": "rebecca.scott@nonprofit.org",
        "first_name": "Rebecca",
        "last_name": "Scott",
        "status": "ACTIVE",
        "tags": ["Lead"],
    },
]

LISTS: list[ListData] = [
    {"name": "VIP Customers", "tag": "VIP"},
    {"name": "Enterprise Accounts", "tag": "Enterprise"},
    {"name": "New Leads", "tag": "Lead"},
]

TEMPLATES_DATA: list[TemplateData] = [
    {
        "name": "Welcome — Onboarding Series",
        "subject": "Welcome to Growixa — Let's get started",
        "body_html": (
            "<html><body style='font-family:Inter,sans-serif;color:#0b1b33;"
            "max-width:600px;margin:0 auto;padding:32px 24px'>"
            "<h1>Welcome to Growixa!</h1>"
            "<p>Hi {{first_name}}, we're thrilled to have you on board.</p>"
            "<a href='https://app.growixa.io/dashboard'>Get started</a>"
            "</body></html>"
        ),
    },
    {
        "name": "Monthly Product Update — Newsletter",
        "subject": "What's new in Growixa — Monthly Update",
        "body_html": (
            "<html><body style='font-family:Inter,sans-serif;color:#0b1b33;"
            "max-width:600px;margin:0 auto;padding:32px 24px'>"
            "<h1>What's new this month</h1>"
            "<p>Hi {{first_name}}, here's a round-up of the latest features.</p>"
            "</body></html>"
        ),
    },
    {
        "name": "Re-Engagement — Win Back",
        "subject": "We miss you, {{first_name}} — Here's what you've missed",
        "body_html": (
            "<html><body style='font-family:Inter,sans-serif;color:#0b1b33;"
            "max-width:600px;margin:0 auto;padding:32px 24px'>"
            "<h1>It's been a while, {{first_name}}</h1>"
            "<p>We noticed you haven't logged in recently.</p>"
            "</body></html>"
        ),
    },
    {
        "name": "Webinar Invitation — Event Announcement",
        "subject": "You're invited: {{event_name}} — Reserve your spot",
        "body_html": (
            "<html><body style='font-family:Inter,sans-serif;color:#0b1b33;"
            "max-width:600px;margin:0 auto;padding:32px 24px'>"
            "<h1>You're invited!</h1>"
            "<p>Join us for an exclusive live session, {{first_name}}.</p>"
            "</body></html>"
        ),
    },
]

SOCIAL_POSTS_DATA: list[SocialPostData] = [
    {
        "caption": (
            "Big news! We've just launched our redesigned AI Marketing Copilot — "
            "generate email subject lines, social captions, and ad copy in seconds. "
            "#EmailMarketing #AI #SaaS"
        ),
        "status": "PUBLISHED",
        "days_offset": -5,
    },
    {
        "caption": (
            "Did you know? Personalized email campaigns get 6x higher open rates than "
            "generic blasts. Deliver the right message every time with Growixa. #EmailMarketing"
        ),
        "status": "PUBLISHED",
        "days_offset": -2,
    },
    {
        "caption": (
            "Just shipped: Social Content Calendar redesign! View all your scheduled and "
            "published posts in a beautiful timeline. Head to Social Calendar now. #ProductUpdate"
        ),
        "status": "SCHEDULED",
        "days_offset": 2,
    },
    {
        "caption": (
            "Live webinar alert! Join us next week for Email Marketing in 2026: What "
            "Actually Works. Free seats are limited — link in bio! #Webinar #MarketingTips"
        ),
        "status": "SCHEDULED",
        "days_offset": 5,
    },
    {
        "caption": (
            "Pro tip: Use A/B subject line testing to improve open rates by 20-30%. "
            "Our campaign editor lets you test two variants automatically. #EmailTips #Growth"
        ),
        "status": "DRAFT",
        "days_offset": 0,
    },
]

CAMPAIGNS_DATA: list[CampaignData] = [
    {
        "name": "Welcome Series — New Subscribers",
        "subject": "Welcome to Growixa — Let's get started",
        "body_html": "<p>Welcome, {{first_name}}! We're thrilled to have you.</p>",
        "status": "DRAFT",
        "days_offset": None,
    },
    {
        "name": "Monthly Product Update — August 2026",
        "subject": "What's new in Growixa — August Update",
        "body_html": "<p>Hi {{first_name}}, here's what we shipped this month.</p>",
        "status": "DRAFT",
        "days_offset": None,
    },
    {
        "name": "Re-Engagement — Inactive Subscribers",
        "subject": "We miss you, {{first_name}}",
        "body_html": "<p>It's been a while — here's what you've missed.</p>",
        "status": "DRAFT",
        "days_offset": None,
    },
    {
        "name": "Webinar Invite — Email Marketing in 2026",
        "subject": "You're invited: Email Marketing in 2026 Webinar",
        "body_html": "<p>Join us live next week, {{first_name}}!</p>",
        "status": "SCHEDULED",
        "days_offset": 7,
    },
    {
        "name": "Black Friday Early Access — VIP List",
        "subject": "Early access: Black Friday deals just for you",
        "body_html": "<p>You're getting early access, {{first_name}}. Don't miss it!</p>",
        "status": "SCHEDULED",
        "days_offset": 14,
    },
]


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------


async def main() -> int:
    seed_email = os.environ.get("SEED_ACCOUNT_EMAIL", "admin@growixa.local")
    force = os.environ.get("SEED_FORCE", "0") == "1"

    async with async_session_factory() as session:
        # 1. Resolve user and account
        user_row = await session.execute(select(User).where(User.email == seed_email))
        user = user_row.scalar_one_or_none()
        if user is None:
            print(
                f"[seed] ERROR: No user found with email '{seed_email}'.\n"
                "       Set SEED_ACCOUNT_EMAIL to a valid admin email.",
                file=sys.stderr,
            )
            return 1

        account_id: uuid.UUID = user.account_id
        print(f"[seed] Seeding account {account_id} (user: {seed_email})")

        # In force mode, wipe dependent resources in full reverse topological order
        if force:
            print("[seed] SEED_FORCE=1: clearing existing demo data for clean re-seed...")
            await session.execute(
                sa_delete(SocialPostMedia).where(SocialPostMedia.account_id == account_id)
            )
            await session.execute(
                sa_delete(SocialPostVersion).where(SocialPostVersion.account_id == account_id)
            )
            await session.execute(sa_delete(SocialPost).where(SocialPost.account_id == account_id))
            await session.execute(
                sa_delete(CampaignRecipient).where(CampaignRecipient.account_id == account_id)
            )
            await session.execute(
                sa_delete(CampaignVersion).where(CampaignVersion.account_id == account_id)
            )
            await session.execute(sa_delete(Campaign).where(Campaign.account_id == account_id))
            await session.execute(
                sa_delete(EmailTemplateVersion).where(EmailTemplateVersion.account_id == account_id)
            )
            await session.execute(
                sa_delete(EmailTemplate).where(EmailTemplate.account_id == account_id)
            )
            await session.execute(
                sa_delete(ContactListMember).where(ContactListMember.account_id == account_id)
            )
            await session.execute(
                sa_delete(ContactList).where(ContactList.account_id == account_id)
            )
            await session.execute(sa_delete(ContactTag).where(ContactTag.account_id == account_id))
            await session.execute(sa_delete(Contact).where(Contact.account_id == account_id))
            await session.flush()

        # 2. Contacts + Tags
        existing_contact = (
            await session.execute(select(Contact).where(Contact.account_id == account_id).limit(1))
        ).scalar_one_or_none()

        contact_id_map: dict[str, uuid.UUID] = {}

        if existing_contact and not force:
            print("[seed] Contacts: already seeded — skipping.")
            rows = (
                (await session.execute(select(Contact).where(Contact.account_id == account_id)))
                .scalars()
                .all()
            )
            for ct in rows:
                contact_id_map[str(ct.email)] = ct.id
        else:
            for c in CONTACTS:
                contact = Contact(
                    account_id=account_id,
                    email=c["email"],
                    first_name=c["first_name"],
                    last_name=c["last_name"],
                    status=c["status"],
                )
                session.add(contact)
                await session.flush()
                contact_id_map[c["email"]] = contact.id

            tag_id_map: dict[str, uuid.UUID] = {}
            for c_data in CONTACTS:
                for tag_name in c_data["tags"]:
                    if tag_name not in tag_id_map:
                        existing_tag = (
                            await session.execute(
                                select(Tag)
                                .where(Tag.account_id == account_id, Tag.name == tag_name)
                                .limit(1)
                            )
                        ).scalar_one_or_none()
                        if existing_tag:
                            tag_id_map[tag_name] = existing_tag.id
                        else:
                            tag = Tag(account_id=account_id, name=tag_name)
                            session.add(tag)
                            await session.flush()
                            tag_id_map[tag_name] = tag.id

            for c_data in CONTACTS:
                email = c_data["email"]
                cid = contact_id_map.get(email)
                if not cid:
                    continue
                for tag_name in c_data["tags"]:
                    tid = tag_id_map.get(tag_name)
                    if tid:
                        session.add(
                            ContactTag(
                                account_id=account_id,
                                contact_id=cid,
                                tag_id=tid,
                            )
                        )
            await session.flush()
            print(f"[seed] Contacts: created {len(CONTACTS)}, tags: {len(tag_id_map)}")

        # 3. Contact Lists
        existing_list = (
            await session.execute(
                select(ContactList).where(ContactList.account_id == account_id).limit(1)
            )
        ).scalar_one_or_none()

        if existing_list and not force:
            print("[seed] Contact lists: already seeded — skipping.")
        else:
            if contact_id_map:
                for list_def in LISTS:
                    cl = ContactList(
                        account_id=account_id,
                        name=list_def["name"],
                        created_by_user_id=user.id,
                    )
                    session.add(cl)
                    await session.flush()
                    for c_data in CONTACTS:
                        if list_def["tag"] in c_data["tags"]:
                            target_cid = contact_id_map.get(c_data["email"])
                            if target_cid:
                                session.add(
                                    ContactListMember(
                                        account_id=account_id,
                                        list_id=cl.id,
                                        contact_id=target_cid,
                                    )
                                )
                await session.flush()
                print(f"[seed] Contact lists: created {len(LISTS)}")

        # 4. Email Templates
        existing_template = (
            await session.execute(
                select(EmailTemplate).where(EmailTemplate.account_id == account_id).limit(1)
            )
        ).scalar_one_or_none()

        if existing_template and not force:
            print("[seed] Email templates: already seeded — skipping.")
        else:
            for t in TEMPLATES_DATA:
                template = EmailTemplate(
                    account_id=account_id,
                    name=t["name"],
                    created_by_user_id=user.id,
                )
                session.add(template)
                await session.flush()
                version = EmailTemplateVersion(
                    account_id=account_id,
                    template_id=template.id,
                    version_number=1,
                    subject=t["subject"],
                    body_html=t["body_html"],
                    created_by_user_id=user.id,
                )
                session.add(version)
                await session.flush()
            print(f"[seed] Email templates: created {len(TEMPLATES_DATA)}")

        # 5. Integrations & Sender Identity
        sender = (
            await session.execute(
                select(SenderIdentity).where(SenderIdentity.account_id == account_id).limit(1)
            )
        ).scalar_one_or_none()

        if sender is None:
            conn = EmailProviderConnection(
                account_id=account_id,
                provider="POSTMARK",
                smtp_host="smtp.postmarkapp.com",
                smtp_port=587,
                smtp_username="demo-postmark-token",
                smtp_password_encrypted=encrypt_secret("demo-postmark-secret"),
                is_active=True,
                created_by_user_id=user.id,
            )
            session.add(conn)
            await session.flush()

            sender = SenderIdentity(
                account_id=account_id,
                email_provider_connection_id=conn.id,
                from_email="notifications@growixa.local",
                from_name="Growixa Team",
                reply_to_email="support@growixa.local",
                verification_status="VERIFIED",
            )
            session.add(sender)
            await session.flush()
            print("[seed] Integrations: created default verified sender identity")

        # 6. Campaigns
        existing_campaign = (
            await session.execute(
                select(Campaign).where(Campaign.account_id == account_id).limit(1)
            )
        ).scalar_one_or_none()

        if existing_campaign and not force:
            print("[seed] Campaigns: already seeded — skipping.")
        else:
            now = datetime.now(UTC)
            for camp in CAMPAIGNS_DATA:
                days = camp["days_offset"]
                scheduled_at = (
                    now + timedelta(days=days)
                    if days is not None and c["status"] == "SCHEDULED"
                    else None
                )
                campaign = Campaign(
                    account_id=account_id,
                    sender_identity_id=sender.id,
                    name=camp["name"],
                    subject=camp["subject"],
                    body_html=camp["body_html"],
                    body_text="Welcome to Growixa.",
                    status=camp["status"],
                    recipient_type="ALL_CONTACTS",
                    scheduled_at=scheduled_at,
                    created_by_user_id=user.id,
                )
                session.add(campaign)
            await session.flush()
            print(f"[seed] Campaigns: created {len(CAMPAIGNS_DATA)} (DRAFT/SCHEDULED)")

        # 7. Social Connection & Posts
        connection = (
            await session.execute(
                select(SocialConnection).where(SocialConnection.account_id == account_id).limit(1)
            )
        ).scalar_one_or_none()

        if connection is None:
            connection = SocialConnection(
                account_id=account_id,
                provider="INSTAGRAM_BUSINESS",
                ig_business_account_id="17841400000000001",
                ig_username="growixa_official",
                facebook_page_id="100000000000001",
                access_token_encrypted=encrypt_secret("mock_instagram_access_token"),
                is_active=True,
            )
            session.add(connection)
            await session.flush()
            print("[seed] Social: connected mock Instagram Business account (@growixa_official)")

        existing_post = (
            await session.execute(
                select(SocialPost).where(SocialPost.account_id == account_id).limit(1)
            )
        ).scalar_one_or_none()

        if existing_post and not force:
            print("[seed] Social posts: already seeded — skipping.")
        else:
            now = datetime.now(UTC)
            for p in SOCIAL_POSTS_DATA:
                target_status = p["status"]
                offset_days = p["days_offset"]
                scheduled_at = None
                published_at = None
                if target_status == "SCHEDULED" and offset_days:
                    scheduled_at = now + timedelta(days=offset_days)
                if target_status == "PUBLISHED" and offset_days:
                    published_at = now + timedelta(days=offset_days)

                post = SocialPost(
                    account_id=account_id,
                    social_connection_id=connection.id,
                    caption=p["caption"],
                    status=target_status,
                    scheduled_at=scheduled_at,
                    published_at=published_at,
                    created_by_user_id=user.id,
                )
                session.add(post)
            await session.flush()
            print(f"[seed] Social posts: created {len(SOCIAL_POSTS_DATA)}")

        # 8. Commit
        await session.commit()

    print("\n[seed] ✅ Done! All demo resources seeded successfully.")
    print("       Re-run with SEED_FORCE=1 to wipe and re-seed from scratch anytime.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
