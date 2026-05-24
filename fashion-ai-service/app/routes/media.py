import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse

from app.config import settings
from app.auth.dependencies import get_current_active_user
from app.database.models import User
from app.schemas.media import PresignedUrlRequest, PresignedUrlResponse
from app.services.storage_service import storage_service

logger = logging.getLogger("fashion-ai-service")
router = APIRouter(prefix="/v1/media", tags=["Media Storage"])

# Standard set of allowed MIME types
ALLOWED_MIMES = {"image/jpeg", "image/png", "image/webp"}


@router.post(
    "/request-upload-url",
    response_model=PresignedUrlResponse,
    status_code=status.HTTP_200_OK,
)
async def request_upload_url(
    payload: PresignedUrlRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    Generates a secure presigned upload URL allowing direct client uploads.
    Enforces rigid MIME validation to reject invalid file types.
    """
    mime = payload.content_type.lower()
    if mime not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid MIME type '{payload.content_type}'. Allowed types: {', '.join(ALLOWED_MIMES)}",
        )

    folder = payload.folder.strip("/").lower()
    if folder not in {"raw", "processed", "thumbnails", "previews"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid folder destination. Allowed: raw, processed, thumbnails, previews",
        )

    # Resolve file extension safely
    ext = "png"
    if "jpeg" in mime or "jpg" in mime:
        ext = "jpg"
    elif "webp" in mime:
        ext = "webp"

    # Generate unique storage filename to prevent name collisions
    unique_filename = f"{uuid.uuid4()}.{ext}"
    
    try:
        # Generate the secure direct PUT endpoint
        upload_url = storage_service.generate_presigned_upload_url(
            folder=folder, filename=unique_filename, content_type=payload.content_type
        )
        
        # Construct the clean persistent download / public CDN url
        # If in S3 mode, uses S3 region/CDN formatting, if in local mode returns relative GET url
        if settings.USE_S3:
            if settings.CDN_BASE_URL:
                download_url = f"{settings.CDN_BASE_URL.rstrip('/')}/{folder}/{unique_filename}"
            else:
                region = settings.AWS_S3_REGION_NAME
                if settings.AWS_S3_ENDPOINT_URL:
                    download_url = f"{settings.AWS_S3_ENDPOINT_URL.rstrip('/')}/{settings.AWS_S3_BUCKET_NAME}/{folder}/{unique_filename}"
                else:
                    download_url = f"https://{settings.AWS_S3_BUCKET_NAME}.s3.{region}.amazonaws.com/{folder}/{unique_filename}"
        else:
            download_url = f"/v1/media/file/{folder}/{unique_filename}"

        file_key = f"{folder}/{unique_filename}"

        logger.info(f"MediaRouter: Generated upload URL for '{file_key}' requested by user {current_user.id}")
        return PresignedUrlResponse(
            upload_url=upload_url,
            download_url=download_url,
            file_key=file_key
        )
        
    except Exception as e:
        logger.error(f"MediaRouter: Failed generating presigned URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize upload ticket: {str(e)}"
        )


@router.put(
    "/upload-local/{folder}/{filename}",
    status_code=status.HTTP_200_OK,
)
async def upload_local_file(
    folder: str,
    filename: str,
    request: Request
):
    """
    PUT stream receiver fallback. Direct upload receiver to simulate S3 client PUT 
    operations in local offline development environments.
    """
    clean_folder = folder.strip("/").lower()
    if clean_folder not in {"raw", "processed", "thumbnails", "previews"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid folder destination.",
        )

    local_dir = settings.UPLOAD_DIR / clean_folder
    local_dir.mkdir(parents=True, exist_ok=True)
    local_path = local_dir / filename

    # Stream binary request body chunks and enforce size limits
    size_counter = 0
    try:
        with open(local_path, "wb") as f:
            async for chunk in request.stream():
                size_counter += len(chunk)
                if size_counter > settings.MAX_CONTENT_LENGTH:
                    f.close()
                    local_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="File size exceeds maximum content length limit."
                    )
                f.write(chunk)
                
        logger.info(f"MediaRouter: Local simulation PUT upload successful for '{clean_folder}/{filename}' ({size_counter} bytes).")
        return {"success": True, "message": "Uploaded successfully to local mock storage."}
        
    except Exception as e:
        local_path.unlink(missing_ok=True)
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"MediaRouter: Local simulation upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get(
    "/file/{folder}/{filename}",
    status_code=status.HTTP_200_OK,
)
async def serve_local_file(folder: str, filename: str):
    """
    Serves local files securely from the operational uploads subdirectories.
    Used under local fallback operations.
    """
    clean_folder = folder.strip("/").lower()
    local_path = settings.UPLOAD_DIR / clean_folder / filename
    
    if not local_path.exists() or not local_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested media asset not found."
        )
        
    return FileResponse(local_path)
