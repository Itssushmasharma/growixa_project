from pydantic import BaseModel, ConfigDict


class TestSendIn(BaseModel):
    to_email: str


class CampaignSendOut(BaseModel):
    job_id: str


class PostmarkWebhookPayload(BaseModel):
    """Deliberately permissive — Postmark's payload shape varies by `RecordType` and
    this hasn't been verified against a live webhook delivery (no Postmark account
    available; see AGENT_HANDOFF.md's evidence gap). Only the fields every event type
    is documented to share are required; everything else is preserved via `extra`
    into `email_events.metadata` rather than dropped."""

    model_config = ConfigDict(extra="allow")

    RecordType: str
    MessageID: str
    Recipient: str | None = None
