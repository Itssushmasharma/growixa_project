import asyncio
import logging
from typing import Any
from growixa_api.db import get_session
from growixa_api.automations.models import Workflow, WorkflowRun
from sqlalchemy import select, update

logger = logging.getLogger(__name__)

async def process_workflow_run(run_id: str) -> None:
    """
    Background task to execute a workflow run.
    """
    async for session in get_session():
        try:
            # 1. Fetch Run
            run = await session.get(WorkflowRun, run_id)
            if not run or run.status != "PENDING":
                return
                
            # 2. Mark as RUNNING
            run.status = "RUNNING"
            await session.commit()
            
            # 3. Fetch Workflow
            workflow = await session.get(Workflow, run.workflow_id)
            if not workflow or workflow.status != "ACTIVE":
                run.status = "FAILED"
                run.logs = run.logs + [{"error": "Workflow is inactive or deleted"}]
                await session.commit()
                return

            # 4. Evaluate Conditions
            # TODO: Implement condition evaluation logic based on trigger_payload and conditions JSON
            conditions_met = True 
            
            if not conditions_met:
                run.status = "SUCCESS"
                run.logs = run.logs + [{"info": "Conditions not met. Execution skipped."}]
                await session.commit()
                return

            # 5. Execute Actions
            for action in workflow.actions:
                # TODO: Implement actual action execution (e.g. tag contact, send email, etc.)
                action_type = action.get("type")
                run.logs = run.logs + [{"info": f"Executing action {action_type}"}]

            # 6. Mark as SUCCESS
            run.status = "SUCCESS"
            await session.commit()
            
        except Exception as e:
            logger.exception(f"Error processing workflow run {run_id}")
            if run:
                run.status = "FAILED"
                run.logs = run.logs + [{"error": str(e)}]
                await session.commit()
