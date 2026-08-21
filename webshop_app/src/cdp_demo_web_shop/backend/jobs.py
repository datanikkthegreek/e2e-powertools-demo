"""Trigger the cdp-triggered pipeline job from the Analytics page.

The job is resolved by name (config.triggered_job_name) rather than a
hardcoded ID, then launched via the Jobs ``run_now`` API. The frontend polls
the run status until it reaches a terminal life-cycle state.
"""

from __future__ import annotations

from databricks.sdk import WorkspaceClient
from fastapi import HTTPException, status

from .core import Dependencies, create_router, logger
from .models import PipelineRunOut, PipelineRunStatusOut

router = create_router()

# Life-cycle states that mean the run is no longer executing.
_TERMINAL_STATES = {"TERMINATED", "SKIPPED", "INTERNAL_ERROR"}


def _resolve_job_id(ws: WorkspaceClient, name: str) -> int:
    """Resolve a Databricks job ID by its (unique) name."""
    for job in ws.jobs.list(name=name):
        if job.job_id is not None:
            return job.job_id
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No Databricks job found with name '{name}'",
    )


@router.post(
    "/jobs/triggered-pipeline/run",
    response_model=PipelineRunOut,
    operation_id="runTriggeredPipeline",
)
def run_triggered_pipeline(
    ws: Dependencies.Client,
    config: Dependencies.Config,
) -> PipelineRunOut:
    job_id = _resolve_job_id(ws, config.triggered_job_name)

    try:
        waiter = ws.jobs.run_now(job_id=job_id)
    except Exception as exc:  # noqa: BLE001 - surface any Jobs API error cleanly
        logger.exception("Failed to trigger job '%s'", config.triggered_job_name)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to trigger job: {exc}",
        ) from exc

    run_id = waiter.run_id
    if run_id is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Jobs API did not return a run_id",
        )

    run_page_url: str | None = None
    try:
        run_page_url = ws.jobs.get_run(run_id=run_id).run_page_url
    except Exception:  # noqa: BLE001 - URL is best-effort, don't fail the trigger
        logger.warning("Could not fetch run_page_url for run %s", run_id)

    return PipelineRunOut(run_id=run_id, run_page_url=run_page_url)


@router.get(
    "/jobs/triggered-pipeline/runs/{run_id}",
    response_model=PipelineRunStatusOut,
    operation_id="getTriggeredPipelineRun",
)
def get_triggered_pipeline_run(
    run_id: int,
    ws: Dependencies.Client,
) -> PipelineRunStatusOut:
    try:
        run = ws.jobs.get_run(run_id=run_id)
    except Exception as exc:  # noqa: BLE001 - surface any Jobs API error cleanly
        logger.exception("Failed to fetch run %s", run_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch run status: {exc}",
        ) from exc

    life_cycle_state: str | None = None
    result_state: str | None = None
    if run.state is not None:
        if run.state.life_cycle_state is not None:
            life_cycle_state = run.state.life_cycle_state.value
        if run.state.result_state is not None:
            result_state = run.state.result_state.value

    return PipelineRunStatusOut(
        run_id=run_id,
        life_cycle_state=life_cycle_state,
        result_state=result_state,
        finished=life_cycle_state in _TERMINAL_STATES,
    )
