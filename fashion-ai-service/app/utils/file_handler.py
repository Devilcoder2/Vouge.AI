import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from app.config import settings

class FileHandler:
    @staticmethod
    def get_extension(filename: str) -> str:
        """Extracts the file extension in lowercase format."""
        if not filename or "." not in filename:
            return ""
        return filename.rsplit(".", 1)[1].lower()

    @staticmethod
    def validate_image(file: UploadFile) -> str:
        """
        Validates the uploaded file for format and size constraints.
        Returns the clean file extension if valid, else raises HTTPException.
        """
        filename = file.filename or ""
        ext = FileHandler.get_extension(filename)
        
        # 1. Format validation
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '.{ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        return ext

    @staticmethod
    async def save_upload(file: UploadFile) -> Path:
        """
        Asynchronously validates and saves an incoming UploadFile to the uploads directory.
        Enforces size limits and returns the resulting Path.
        """
        ext = FileHandler.validate_image(file)
        
        # Generate unique UUID filename to avoid name collisions
        unique_name = f"{uuid.uuid4()}.{ext}"
        destination_path = settings.UPLOAD_DIR / unique_name
        
        # 2. Size validation and async writing
        size_counter = 0
        try:
            with open(destination_path, "wb") as buffer:
                while chunk := await file.read(1024 * 1024):  # Read in 1MB chunks
                    size_counter += len(chunk)
                    if size_counter > settings.MAX_CONTENT_LENGTH:
                        # Exceeded size limit, clean up the partially written file
                        buffer.close()
                        destination_path.unlink(missing_ok=True)
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds maximum size of {settings.MAX_CONTENT_LENGTH // (1024 * 1024)}MB."
                        )
                    buffer.write(chunk)
        except Exception as e:
            # Clean up on any unexpected file handling failures
            destination_path.unlink(missing_ok=True)
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save upload locally: {str(e)}"
            )
            
        return destination_path
        
    @staticmethod
    def delete_file(path: Path) -> None:
        """Deletes a file safely from disk if it exists."""
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
