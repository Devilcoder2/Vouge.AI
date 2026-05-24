"""
Background Jobs Router — prefix /v1/jobs
"""

import logging
import uuid
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.auth.dependencies import get_current_active_user
from app.database.models import User, BackgroundJob
from app.database.session import get_db
from app.utils.file_handler import FileHandler
from app.schemas.jobs import JobCreateResponse, JobStatusResponse
from app.schemas.recommendation import GenerateOutfitsRequest
from app.tasks import (
    clothing_processing_job,
    outfit_generation_job,
    gap_analysis_job,
)

logger = logging.getLogger("fashion-ai-service")
router = APIRouter(prefix="/v1/jobs", tags=["Background Jobs"])

# ── Resilient Enqueue Helper ──────────────────────────────────────────────────

def enqueue_background_job(
    job_uuid: UUID,
    task_func,
    *args,
    background_tasks: BackgroundTasks = None,
    **kwargs
):
    """
    Attempts to enqueue job in Celery worker pool (using Redis).
    If Celery is disabled or Redis broker is unreachable, falls back instantly
    to local in-process FastAPI BackgroundTasks queue.
    """
    if settings.USE_CELERY:
        try:
            # Enqueue in Celery
            task_func.delay(str(job_uuid), *args, **kwargs)
            logger.info(f"Successfully enqueued job {job_uuid} in Celery worker pool.")
            return
        except Exception as celery_err:
            logger.warning(
                f"Celery broker unavailable: {str(celery_err)}. "
                f"Falling back to local FastAPI BackgroundTasks for job {job_uuid}."
            )

    # Local fallback
    if background_tasks:
        background_tasks.add_task(task_func, str(job_uuid), *args, **kwargs)
        logger.info(f"Successfully enqueued job {job_uuid} in local FastAPI BackgroundTasks queue.")
    else:
        # Fallback to synchronous run if no BackgroundTasks context exists (e.g. testing)
        logger.info(f"Executing job {job_uuid} synchronously inside route thread.")
        try:
            task_func(str(job_uuid), *args, **kwargs)
        except Exception as sync_err:
            logger.error(f"Synchronous execution of job {job_uuid} failed: {str(sync_err)}")


# ── POST /v1/jobs/process-clothing ────────────────────────────────────────────

@router.post(
    "/process-clothing",
    response_model=JobCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_clothing_processing_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Creates an asynchronous clothing processing job.
    Saves raw uploaded image instantly and delegates AI analysis to background workers.
    """
    try:
        # 1. Instantly save raw file to uploads directory
        raw_filepath = await FileHandler.save_upload(file)

        # 2. Create job row
        job_id = uuid.uuid4()
        job = BackgroundJob(
            id=job_id,
            user_id=current_user.id,
            job_type="clothing_processing_job",
            status="queued",
            progress=0,
        )
        db.add(job)
        await db.commit()

        # 3. Enqueue the task
        enqueue_background_job(
            job_id,
            clothing_processing_job,
            str(raw_filepath),
            str(current_user.id),
            background_tasks=background_tasks,
        )

        return JobCreateResponse(job_id=job_id, status="queued")

    except Exception as e:
        logger.error(f"Failed to launch clothing processing job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Background job initialization failed: {str(e)}"
        )


# ── POST /v1/jobs/generate-outfits ────────────────────────────────────────────

@router.post(
    "/generate-outfits",
    response_model=JobCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_outfit_generation_job(
    payload: GenerateOutfitsRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Creates an asynchronous outfit generation and personalized ranking job.
    """
    try:
        # Create job row
        job_id = uuid.uuid4()
        job = BackgroundJob(
            id=job_id,
            user_id=current_user.id,
            job_type="outfit_generation_job",
            status="queued",
            progress=0,
        )
        db.add(job)
        await db.commit()

        # Enqueue the task
        # Passes User UUID as target user for personalization
        enqueue_background_job(
            job_id,
            outfit_generation_job,
            str(current_user.id),
            payload.occasion,
            payload.season,
            background_tasks=background_tasks,
        )

        return JobCreateResponse(job_id=job_id, status="queued")

    except Exception as e:
        logger.error(f"Failed to launch outfit generation job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Background job initialization failed: {str(e)}"
        )


# ── POST /v1/jobs/gap-analysis ────────────────────────────────────────────────

@router.post(
    "/gap-analysis",
    response_model=JobCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_gap_analysis_job(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Creates an asynchronous wardrobe gap analysis and unlock forecasting job.
    """
    try:
        # Create job row
        job_id = uuid.uuid4()
        job = BackgroundJob(
            id=job_id,
            user_id=current_user.id,
            job_type="gap_analysis_job",
            status="queued",
            progress=0,
        )
        db.add(job)
        await db.commit()

        # Enqueue the task
        enqueue_background_job(
            job_id,
            gap_analysis_job,
            str(current_user.id),
            background_tasks=background_tasks,
        )

        return JobCreateResponse(job_id=job_id, status="queued")

    except Exception as e:
        logger.error(f"Failed to launch gap analysis job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Background job initialization failed: {str(e)}"
        )


# ── GET /v1/jobs/{job_id} ──────────────────────────────────────────────────────

@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_background_job_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieves the status, progress, errors, and resulting metadata of a background job by UUID.
    """
    result = await db.execute(
        select(BackgroundJob)
        .where(BackgroundJob.id == job_id)
        .where(BackgroundJob.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )

    # Return SQLAlchemy object mapped to JobStatusResponse
    return JobStatusResponse(
        job_id=job.id,
        job_type=job.job_type,
        status=job.status,
        progress=job.progress,
        error_message=job.error_message,
        result_reference=job.result_reference,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


# ── POST /v1/jobs/{job_id}/cancel ─────────────────────────────────────────────

@router.post(
    "/{job_id}/cancel",
    status_code=status.HTTP_200_OK,
)
async def cancel_background_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Cancels an active background job.
    """
    result = await db.execute(
        select(BackgroundJob)
        .where(BackgroundJob.id == job_id)
        .where(BackgroundJob.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )

    if job.status in ["completed", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with final state '{job.status}'."
        )

    # Transition to cancelled.
    # The worker task polls this state and halts execution.
    job.status = "cancelled"
    db.add(job)
    await db.commit()

    logger.info(f"Job {job_id} cancellation requested by user {current_user.id}.")
    return {"success": True, "message": f"Cancellation requested for job '{job_id}'."}
