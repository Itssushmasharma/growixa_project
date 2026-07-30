import uuid

from fastapi import APIRouter, Depends

from growixa_api.jobs.producer import publish_job
from growixa_api.jobs.schemas import SYSTEM_HEALTHCHECK_QUEUE, JobEnvelope
from growixa_api.permissions.dependencies import require_permission

router = APIRouter(prefix="/system", tags=["system"])

# admin.access, not a job-specific permission: Sprint 1 has no dedicated "jobs" permission
# code, and this route's only purpose is an ops smoke-check that the RabbitMQ pipeline
# works end-to-end, which fits admin.access's existing Super Admin/Admin-only grant.
_require_admin = require_permission("admin.access")


@router.post("/jobs/healthcheck", status_code=202)
async def trigger_healthcheck_job(
    actor_id: uuid.UUID = Depends(_require_admin),
) -> dict[str, str]:
    envelope = JobEnvelope(
        idempotency_key=str(uuid.uuid4()),
        job_type=SYSTEM_HEALTHCHECK_QUEUE,
        created_by_user_id=actor_id,
    )
    await publish_job(SYSTEM_HEALTHCHECK_QUEUE, envelope)
    return {"job_id": str(envelope.job_id)}
