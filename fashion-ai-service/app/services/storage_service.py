import logging
import os
from pathlib import Path
from typing import Optional
import boto3
from botocore.config import Config

from app.config import settings

logger = logging.getLogger("fashion-ai-service")


class StorageService:
    def __init__(self):
        self.use_s3 = settings.USE_S3
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        self.s3_client = None

        if self.use_s3:
            try:
                # Configure custom region / credentials securely
                config = Config(
                    region_name=settings.AWS_S3_REGION_NAME,
                    signature_version="s3v4",
                    retries={"max_attempts": 3, "mode": "standard"},
                )
                
                kwargs = {
                    "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                    "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
                    "config": config,
                }
                
                # Check for custom endpoint url (e.g. MinIO, LocalStack, Cloudflare R2)
                if settings.AWS_S3_ENDPOINT_URL:
                    kwargs["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL

                self.s3_client = boto3.client("s3", **kwargs)
                logger.info(
                    f"StorageService: Initialized S3 client securely on bucket '{self.bucket_name}'."
                )
            except Exception as e:
                logger.error(
                    f"StorageService: Failed to initialize boto3 S3 client: {str(e)}. "
                    "Falling back to local storage.",
                    exc_info=True
                )
                self.use_s3 = False

    def upload_file(
        self,
        file_data: bytes,
        folder: str,
        filename: str,
        content_type: str = "image/png"
    ) -> str:
        """
        Uploads binary file bytes into cloud storage (S3 bucket) or a local fallback directory.
        Returns the absolute HTTP public download URL.
        """
        clean_folder = folder.strip("/")
        
        # 1. Cloud S3 Upload
        if self.use_s3 and self.s3_client:
            s3_key = f"{clean_folder}/{filename}"
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file_data,
                    ContentType=content_type
                )
                logger.info(f"StorageService: Successfully uploaded '{s3_key}' to S3.")
                
                # Construct public download URL or custom CDN url
                if settings.CDN_BASE_URL:
                    return f"{settings.CDN_BASE_URL.rstrip('/')}/{s3_key}"
                
                # Default S3 endpoint URL formatting
                region = settings.AWS_S3_REGION_NAME
                if settings.AWS_S3_ENDPOINT_URL:
                    return f"{settings.AWS_S3_ENDPOINT_URL.rstrip('/')}/{self.bucket_name}/{s3_key}"
                return f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
                
            except Exception as e:
                logger.error(
                    f"StorageService: S3 PutObject failed for key '{s3_key}': {str(e)}. "
                    "Attempting local storage write fallback.",
                    exc_info=True
                )

        # 2. Local Fallback Upload
        local_dir = settings.UPLOAD_DIR / clean_folder
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / filename
        
        try:
            with open(local_path, "wb") as f:
                f.write(file_data)
            logger.info(f"StorageService: Successfully saved '{filename}' locally under '{clean_folder}/'.")
            
            # Return server relative download link
            return f"/v1/media/file/{clean_folder}/{filename}"
        except Exception as local_err:
            logger.error(f"StorageService: Local storage write failed for '{filename}': {str(local_err)}")
            raise local_err

    def generate_presigned_upload_url(
        self,
        folder: str,
        filename: str,
        content_type: str
    ) -> str:
        """
        Generates a secure upload URL allowing direct client uploads.
        * S3 Presigned PUT URL in Cloud Mode.
        * Server Relative mock endpoint route in Local Fallback Mode.
        """
        clean_folder = folder.strip("/")
        
        # 1. Cloud S3 Presigned URL
        if self.use_s3 and self.s3_client:
            s3_key = f"{clean_folder}/{filename}"
            try:
                upload_url = self.s3_client.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={
                        "Bucket": self.bucket_name,
                        "Key": s3_key,
                        "ContentType": content_type
                    },
                    ExpiresIn=3600
                )
                logger.info(f"StorageService: Presigned S3 upload URL generated for '{s3_key}'.")
                return upload_url
            except Exception as e:
                logger.warning(
                    f"StorageService: S3 presigned generation failed: {str(e)}. "
                    "Falling back to local direct URL simulation."
                )

        # 2. Local Endpoint URL Simulation
        return f"http://localhost:{settings.PORT}/v1/media/upload-local/{clean_folder}/{filename}"

    def delete_file(self, file_url: str) -> None:
        """
        Parses a saved file URL and deletes it from either S3 cloud or local disk layout.
        """
        if not file_url:
            return

        # 1. Local Fallback URL deletion
        if "/v1/media/file/" in file_url:
            parts = file_url.split("/v1/media/file/", 1)[1].split("/")
            if len(parts) >= 2:
                folder, filename = parts[0], parts[1]
                local_path = settings.UPLOAD_DIR / folder / filename
                try:
                    local_path.unlink(missing_ok=True)
                    logger.info(f"StorageService: Deleted local file '{local_path}'.")
                except Exception as e:
                    logger.warning(f"StorageService: Failed deleting local file '{local_path}': {str(e)}")
            return

        # 2. Cloud S3 Deletion
        if self.use_s3 and self.s3_client:
            # Parse S3 Key from absolute URL
            # Standard formats:
            # https://bucket.s3.region.amazonaws.com/folder/filename
            # cdn.domain.com/folder/filename
            # endpoint_url/bucket/folder/filename
            s3_key = ""
            try:
                if settings.CDN_BASE_URL and settings.CDN_BASE_URL in file_url:
                    s3_key = file_url.split(settings.CDN_BASE_URL)[1].lstrip("/")
                elif self.bucket_name in file_url:
                    s3_key = file_url.split(self.bucket_name)[1].lstrip("/")
                    # If endpoint URL put the bucket name as first folder
                    if s3_key.startswith("/"):
                        s3_key = s3_key[1:]
                else:
                    # Generic slash parsing
                    url_parts = file_url.split("/")
                    if len(url_parts) > 4:
                        s3_key = "/".join(url_parts[4:])
                
                if s3_key:
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                    logger.info(f"StorageService: Deleted S3 cloud object '{s3_key}' successfully.")
            except Exception as e:
                logger.warning(f"StorageService: Cloud S3 deletion failed for '{file_url}': {str(e)}")


# Singleton instance
storage_service = StorageService()
