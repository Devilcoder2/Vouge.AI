import io
import logging
from typing import Dict, Tuple
from PIL import Image, ImageOps

logger = logging.getLogger("fashion-ai-service")


class ImageOptimizer:
    @staticmethod
    def validate_and_load(file_data: bytes) -> Image.Image:
        """
        Validates the raw image bytes for integrity and format.
        Throws ValueError if the image is corrupted or invalid.
        Returns a fresh PIL Image object ready for processing.
        """
        try:
            # 1. First open and run verify() to audit integrity
            stream = io.BytesIO(file_data)
            img = Image.open(stream)
            img.verify()
            
            # 2. PIL verify() invalidates the open file pointer, so we re-open for actual loading
            stream.seek(0)
            loaded_img = Image.open(stream)
            loaded_img.load()  # Force loading bytes to catch truncated errors
            
            logger.info(f"ImageOptimizer: Validated image successfully. Format: {loaded_img.format}, Size: {loaded_img.size}")
            return loaded_img
        except Exception as e:
            logger.error(f"ImageOptimizer: Image validation failed: {str(e)}")
            raise ValueError(f"Corrupted or invalid image: {str(e)}")

    @staticmethod
    def compress_image(img: Image.Image, max_width: int, quality: int = 85) -> bytes:
        """
        Resizes an image preserving aspect ratio to a maximum width limit.
        Compresses and saves to appropriate formats:
        - PNG (with optimize=True) if transparent/RGBA.
        - JPEG (with quality parameter) otherwise.
        """
        width, height = img.size
        
        # Scale down if width exceeds max boundary
        if width > max_width:
            ratio = max_width / width
            new_size = (max_width, int(height * ratio))
            # Use high-quality Resampling Lanczos filter
            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"ImageOptimizer: Scaled image from {width}px to {max_width}px width.")
        else:
            resized_img = img

        output = io.BytesIO()
        
        # Preserve transparency (Alpha channel)
        if resized_img.mode in ("RGBA", "LA") or (resized_img.mode == "P" and "transparency" in resized_img.info):
            # Save as PNG with optimization
            resized_img.save(output, format="PNG", optimize=True)
            content_type = "image/png"
        else:
            # Convert to RGB (required for JPEG)
            rgb_img = resized_img.convert("RGB")
            rgb_img.save(output, format="JPEG", quality=quality, optimize=True)
            content_type = "image/jpeg"

        return output.getvalue()

    @classmethod
    def generate_variants(cls, file_data: bytes) -> Dict[str, bytes]:
        """
        Takes raw image bytes and returns a dictionary of optimized variant bytes:
        - "thumbnail": aspect-fit square cropping (150x150, quality=75)
        - "mobile": max-width 750px scaled (quality=80)
        - "web": max-width 1200px scaled (quality=85)
        """
        img = cls.validate_and_load(file_data)
        
        # 1. Generate Thumbnail (Square crop using ImageOps.fit)
        # Excellent for high-speed wardrobe grids and catalogs
        thumbnail_img = ImageOps.fit(img, (150, 150), Image.Resampling.LANCZOS)
        thumb_io = io.BytesIO()
        if thumbnail_img.mode in ("RGBA", "LA"):
            thumbnail_img.save(thumb_io, format="PNG", optimize=True)
        else:
            rgb_thumb = thumbnail_img.convert("RGB")
            rgb_thumb.save(thumb_io, format="JPEG", quality=75, optimize=True)
        thumbnail_bytes = thumb_io.getvalue()

        # 2. Generate Mobile Optimized (max width 750px)
        mobile_bytes = cls.compress_image(img, max_width=750, quality=80)

        # 3. Generate Web Optimized (max width 1200px)
        web_bytes = cls.compress_image(img, max_width=1200, quality=85)

        return {
            "thumbnail": thumbnail_bytes,
            "mobile": mobile_bytes,
            "web": web_bytes
        }
