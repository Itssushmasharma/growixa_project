"""Lead Generation API router for landing page form capture & CRM routing."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(
    tags=["lead-gen"],
)


class LeadCaptureIn(BaseModel):
    form_id: str = Field(default="form_default")
    email: str = Field(min_length=3, max_length=254)
    full_name: str | None = None
    phone: str | None = None
    company: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None


class LeadCaptureOut(BaseModel):
    status: str = "CAPTURED"
    lead_id: str
    crm_status: str = "ROUTED_TO_CRM"
    email: str


class FormIn(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    target_crm_list: str = Field(default="Default Leads")
    redirect_url: str | None = None


class FormOut(FormIn):
    id: str
    submissions_count: int = 0
    embed_code: str


_FORMS_STORE: list[dict[str, Any]] = [
    {
        "id": "form_demo_01",
        "title": "Homepage Growth Assessment Form",
        "target_crm_list": "Inbound Leads",
        "redirect_url": "/thank-you",
        "submissions_count": 48,
        "embed_code": '<iframe src="https://growixa.com/forms/embed/form_demo_01" width="100%" height="400"></iframe>',
    }
]


@router.post("/api/v1/leads/capture", response_model=LeadCaptureOut)
async def capture_lead(payload: LeadCaptureIn) -> LeadCaptureOut:
    lead_id = f"lead_{len(_FORMS_STORE) * 100 + 42}"
    return LeadCaptureOut(
        status="CAPTURED",
        lead_id=lead_id,
        crm_status="ROUTED_TO_CRM",
        email=payload.email,
    )


@router.get("/api/v1/lead-gen/forms", response_model=list[FormOut])
async def list_forms() -> list[FormOut]:
    return [FormOut(**f) for f in _FORMS_STORE]


@router.post("/api/v1/lead-gen/forms", response_model=FormOut)
async def create_form(payload: FormIn) -> FormOut:
    form_id = f"form_custom_{len(_FORMS_STORE) + 1}"
    new_form = {
        "id": form_id,
        **payload.model_dump(),
        "submissions_count": 0,
        "embed_code": f'<iframe src="https://growixa.com/forms/embed/{form_id}" width="100%" height="400"></iframe>',
    }
    _FORMS_STORE.append(new_form)
    return FormOut(**new_form)
