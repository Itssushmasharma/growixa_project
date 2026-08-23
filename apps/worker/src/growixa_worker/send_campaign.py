import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growixa_worker.billing_quota import QuotaExceededError, check_and_consume_email_quota
from growixa_worker.config import get_settings
from growixa_worker.email_sender import EmailSendError, send_email
from growixa_worker.encryption import decrypt_secret
from growixa_worker.models import (
    Campaign,
    CampaignRecipient,
    CampaignVersion,
    CompanyProfile,
    ConsentRecord,
    ContactCustomField,
    ContactFieldValue,
    DeliveryAttempt,
    EmailProviderConnection,
    MessageDelivery,
    SenderIdentity,
    SuppressionEntry,
    UsageRecord,
)
from growixa_worker.personalization import (
    PersonalizationError,
    render_personalization,
    validate_template_tokens,
)
from growixa_worker.recipients import resolve_recipients

logger = logging.getLogger("growixa_worker")


async def _is_suppressed_or_withdrawn(
    session: AsyncSession, account_id: uuid.UUID, contact_id: Any, email: str
) -> bool:
    """Per DEC-GRX-008 / SPRINT_03's acceptance criteria: an address on the suppression
    list OR whose most recent EMAIL consent is WITHDRAWN is excluded from sending.
    Scoped to the sending campaign's own account (GRX-SAAS-001) -- one account's
    suppression/consent state must never affect another account's send, even for the
    same email address. Also checks whole-domain blocks (GRX-SAAS-015 ad hoc pass) --
    a domain entry has `email IS NULL`, so it can never match the exact-email query
    above; it's matched here by the recipient's own domain instead."""
    suppression_result = await session.execute(
        select(SuppressionEntry.id)
        .where(SuppressionEntry.account_id == account_id, SuppressionEntry.email == email)
        .limit(1)
    )
    if suppression_result.scalar_one_or_none() is not None:
        return True

    domain = email.rsplit("@", 1)[-1].lower() if "@" in email else None
    if domain is not None:
        domain_result = await session.execute(
            select(SuppressionEntry.id)
            .where(SuppressionEntry.account_id == account_id, SuppressionEntry.domain == domain)
            .limit(1)
        )
        if domain_result.scalar_one_or_none() is not None:
            return True

    consent_result = await session.execute(
        select(ConsentRecord.status)
        .where(
            ConsentRecord.account_id == account_id,
            ConsentRecord.contact_id == contact_id,
            ConsentRecord.channel == "EMAIL",
        )
        .order_by(ConsentRecord.recorded_at.desc())
        .limit(1)
    )
    latest_status = consent_result.scalar_one_or_none()
    return latest_status == "WITHDRAWN"


def _with_unsubscribe_footer(
    body_html: str, body_text: str | None, campaign_recipient_id: uuid.UUID
) -> tuple[str, str | None]:
    """Every real send embeds a per-recipient unsubscribe link (GRX-EMAIL-005) — no
    merge-tag infrastructure exists yet, so this is a plain footer append, not a
    `{{unsubscribe_url}}` substitution. Identified only by the campaign_recipient's own
    unguessable UUID, matching how the public /unsubscribe/{id} route authenticates it."""
    url = f"{get_settings().api_public_url}/unsubscribe/{campaign_recipient_id}"
    html = f'{body_html}<p><a href="{url}">Unsubscribe</a></p>'
    text = f"{body_text}\n\nUnsubscribe: {url}" if body_text else f"Unsubscribe: {url}"
    return html, text


def _unsubscribe_headers(campaign_recipient_id: uuid.UUID) -> dict[str, str]:
    """Gmail/Yahoo's 2024+ bulk-sender requirements mandate a List-Unsubscribe header
    with one-click support (RFC 8058) on every bulk campaign send, on top of (not instead
    of) the visible footer link above — reuses the exact same /unsubscribe/{id} route,
    just surfaced as a header instead of only a body link."""
    url = f"{get_settings().api_public_url}/unsubscribe/{campaign_recipient_id}"
    return {
        "List-Unsubscribe": f"<{url}>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
    }


def _campaign_email_headers(
    campaign_recipient_id: uuid.UUID,
    delivery_id: uuid.UUID,
    campaign_id: uuid.UUID,
) -> dict[str, str]:
    headers = _unsubscribe_headers(campaign_recipient_id)
    headers["X-Postal-Tag"] = str(campaign_id)
    headers["X-Growixa-Delivery-ID"] = str(delivery_id)
    headers["X-Growixa-Recipient-ID"] = str(campaign_recipient_id)
    return headers


async def handle_send_campaign(session: AsyncSession, payload: dict[str, Any]) -> None:
    campaign_id = payload["campaign_id"]
    campaign = await session.get(Campaign, campaign_id)
    if campaign is None:
        logger.error("send_campaign: campaign %s not found, dropping job", campaign_id)
        return

    already_sent = await session.execute(
        select(CampaignVersion.id).where(CampaignVersion.campaign_id == campaign.id).limit(1)
    )
    if already_sent.scalar_one_or_none() is not None:
        logger.info("send_campaign: campaign %s already has a snapshot, no-op", campaign_id)
        return

    identity = await session.get(SenderIdentity, campaign.sender_identity_id)
    connection = (
        await session.get(EmailProviderConnection, identity.email_provider_connection_id)
        if identity is not None
        else None
    )
    if identity is None or connection is None:
        logger.error(
            "send_campaign: campaign %s has no resolvable sender identity/connection",
            campaign_id,
        )
        campaign.status = "FAILED"
        await session.commit()
        return

    # Load account data for personalization
    company_profile = (
        await session.execute(
            select(CompanyProfile).where(CompanyProfile.account_id == campaign.account_id).limit(1)
        )
    ).scalar_one_or_none()
    account_data = {
        "company_name": company_profile.name if company_profile else "",
        "website_url": company_profile.website
        if (company_profile and company_profile.website)
        else "",
        "sender_name": identity.from_name or "",
    }

    # Load allowed custom fields for personalization
    custom_fields_res = await session.execute(
        select(ContactCustomField).where(
            ContactCustomField.account_id == campaign.account_id,
            ContactCustomField.is_personalization_usable.is_(True),
        )
    )
    usable_custom_fields = custom_fields_res.scalars().all()
    allowed_custom_keys = {cf.key for cf in usable_custom_fields}
    field_id_to_key = {cf.id: cf.key for cf in usable_custom_fields}

    # Validate template tokens before snapshotting or sending
    try:
        validate_template_tokens(campaign.subject, allowed_custom_field_keys=allowed_custom_keys)
        validate_template_tokens(campaign.body_html, allowed_custom_field_keys=allowed_custom_keys)
        if campaign.body_text:
            validate_template_tokens(
                campaign.body_text, allowed_custom_field_keys=allowed_custom_keys
            )
    except PersonalizationError as exc:
        logger.error("send_campaign: campaign %s template validation failed: %s", campaign_id, exc)
        campaign.status = "FAILED"
        await session.commit()
        return

    contacts = await resolve_recipients(session, campaign)

    recipients: list[CampaignRecipient] = []
    for contact in contacts:
        suppressed = await _is_suppressed_or_withdrawn(
            session, campaign.account_id, contact.id, contact.email
        )
        recipient = CampaignRecipient(
            account_id=campaign.account_id,
            campaign_id=campaign.id,
            contact_id=contact.id,
            email=contact.email,
            status="SUPPRESSED" if suppressed else "PENDING",
        )
        session.add(recipient)
        recipients.append(recipient)
    await session.flush()

    session.add(
        CampaignVersion(
            account_id=campaign.account_id,
            campaign_id=campaign.id,
            subject=campaign.subject,
            body_html=campaign.body_html,
            body_text=campaign.body_text,
            recipient_count=len(recipients),
        )
    )

    # Load custom field values for contacts
    contact_map = {c.id: c for c in contacts}
    contact_ids = list(contact_map.keys())
    field_values_map: dict[uuid.UUID, dict[str, str]] = {cid: {} for cid in contact_ids}
    if contact_ids and field_id_to_key:
        values_res = await session.execute(
            select(
                ContactFieldValue.contact_id,
                ContactFieldValue.field_id,
                ContactFieldValue.value,
            ).where(
                ContactFieldValue.account_id == campaign.account_id,
                ContactFieldValue.contact_id.in_(contact_ids),
                ContactFieldValue.field_id.in_(list(field_id_to_key.keys())),
            )
        )
        for cid, fid, val in values_res.all():
            if val is not None:
                k = field_id_to_key.get(fid)
                if k:
                    field_values_map[cid][k] = val

    smtp_password = decrypt_secret(connection.smtp_password_encrypted)
    sent_count = 0
    cancelled_mid_flight = False
    for recipient in recipients:
        # Check if campaign was cancelled mid-flight (Emergency Stop)
        check_status = await session.scalar(
            select(Campaign.status).where(Campaign.id == campaign.id)
        )
        if check_status == "CANCELLED":
            logger.info(
                "send_campaign: campaign %s cancelled mid-flight (emergency stop) after %s sent",
                campaign_id,
                sent_count,
            )
            cancelled_mid_flight = True
            break

        if recipient.status == "SUPPRESSED":
            continue

        delivery = MessageDelivery(
            account_id=campaign.account_id, campaign_recipient_id=recipient.id, status="QUEUED"
        )
        session.add(delivery)
        await session.flush()

        try:
            await check_and_consume_email_quota(session, account_id=campaign.account_id)
        except QuotaExceededError:
            delivery.status = "FAILED"
            recipient.status = "FAILED"
            session.add(
                DeliveryAttempt(
                    account_id=campaign.account_id,
                    message_delivery_id=delivery.id,
                    attempt_number=1,
                    status="FAILED",
                    error_message="Monthly email quota exceeded and no credits available",
                )
            )
            logger.warning(
                "send_campaign: recipient %s blocked, account %s over email quota",
                recipient.email,
                campaign.account_id,
            )
            continue

        # Resolve personalization per recipient
        target_contact = contact_map.get(recipient.contact_id)
        c_custom = field_values_map.get(recipient.contact_id, {})
        recipient_data = {
            "first_name": target_contact.first_name if target_contact else None,
            "last_name": target_contact.last_name if target_contact else None,
            "email": recipient.email,
            "phone": target_contact.phone if target_contact else None,
            "unsubscribe_url": f"{get_settings().api_public_url}/unsubscribe/{recipient.id}",
            **c_custom,
        }

        try:
            personalized_subject = render_personalization(
                campaign.subject,
                recipient_data=recipient_data,
                account_data=account_data,
                allowed_custom_field_keys=allowed_custom_keys,
                is_html=False,
                recipient_identifier=recipient.email,
            )
            personalized_html = render_personalization(
                campaign.body_html,
                recipient_data=recipient_data,
                account_data=account_data,
                allowed_custom_field_keys=allowed_custom_keys,
                is_html=True,
                recipient_identifier=recipient.email,
            )
            personalized_text = (
                render_personalization(
                    campaign.body_text,
                    recipient_data=recipient_data,
                    account_data=account_data,
                    allowed_custom_field_keys=allowed_custom_keys,
                    is_html=False,
                    recipient_identifier=recipient.email,
                )
                if campaign.body_text
                else None
            )
        except PersonalizationError as exc:
            delivery.status = "FAILED"
            recipient.status = "FAILED"
            session.add(
                DeliveryAttempt(
                    account_id=campaign.account_id,
                    message_delivery_id=delivery.id,
                    attempt_number=1,
                    status="FAILED",
                    error_message=f"Personalization error: {exc}",
                )
            )
            logger.warning("send_campaign: personalization for %s failed: %s", recipient.email, exc)
            continue

        body_html, body_text = _with_unsubscribe_footer(
            personalized_html, personalized_text, recipient.id
        )
        try:
            await send_email(
                smtp_host=connection.smtp_host,
                smtp_port=connection.smtp_port,
                smtp_username=connection.smtp_username,
                smtp_password=smtp_password,
                from_email=identity.from_email,
                from_name=identity.from_name,
                to_email=recipient.email,
                subject=personalized_subject,
                body_html=body_html,
                body_text=body_text,
                extra_headers=_campaign_email_headers(recipient.id, delivery.id, campaign.id),
            )
        except EmailSendError as exc:
            delivery.status = "FAILED"
            recipient.status = "FAILED"
            session.add(
                DeliveryAttempt(
                    account_id=campaign.account_id,
                    message_delivery_id=delivery.id,
                    attempt_number=1,
                    status="FAILED",
                    error_message=str(exc),
                )
            )
            logger.warning("send_campaign: delivery to %s failed: %s", recipient.email, exc)
        else:
            delivery.status = "SENT"
            delivery.sent_at = datetime.now(UTC)
            recipient.status = "SENT"
            sent_count += 1

    if cancelled_mid_flight:
        campaign.status = "CANCELLED"
        if not campaign.cancelled_at:
            campaign.cancelled_at = datetime.now(UTC)
    else:
        campaign.status = "SENT"
        campaign.sent_at = datetime.now(UTC)

    session.add(
        UsageRecord(
            account_id=campaign.account_id,
            operation_type="email.sent",
            quantity=sent_count,
            unit="email",
            created_by_user_id=campaign.created_by_user_id,
        )
    )

    await session.commit()
    logger.info(
        "send_campaign: campaign %s finished (%s) with %s/%s sent",
        campaign_id,
        campaign.status,
        sent_count,
        len(recipients),
    )
