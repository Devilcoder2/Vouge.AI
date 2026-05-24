from pydantic import BaseModel, Field
from typing import Optional

class PresignedUrlRequest(BaseModel):
    filename: str = Field(..., description="Original filename of the media upload")
    content_type: str = Field(..., description="MIME content type (e.g. image/jpeg, image/png, image/webp)")
    folder: str = Field("raw", description="Destination bucket folder/prefix: raw, processed, thumbnails, previews")

class PresignedUrlResponse(BaseModel):
    upload_url: str = Field(..., description="Secure signed endpoint to PUT the file directly")
    download_url: str = Field(..., description="CDN-ready public download URL after successful upload")
    file_key: str = Field(..., description="Unique persistent identifier / path in storage")
