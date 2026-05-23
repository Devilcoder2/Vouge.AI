import logging
from PIL import Image
import io
from rembg import remove

logger = logging.getLogger("fashion-ai-service")

class BackgroundRemover:
    @staticmethod
    def remove_background(image_path_or_bytes) -> Image.Image:
        """
        Removes the background from a clothing image, outputting a transparent PNG PIL Image.
        Accepts either a file path (string/Path) or raw byte data.
        """
        try:
            if isinstance(image_path_or_bytes, (str, io.BytesIO)) or hasattr(image_path_or_bytes, "read"):
                # Open image using Pillow
                img = Image.open(image_path_or_bytes)
            else:
                # Assume raw bytes
                img = Image.open(io.BytesIO(image_path_or_bytes))

            # rembg expects input in standard PIL or numpy formats
            # Converts non-RGBA modes (e.g. RGB, CMYK, Palette) automatically
            logger.info("Starting background removal process using rembg...")
            transparent_img = remove(img)
            logger.info("Successfully removed background.")
            
            return transparent_img
            
        except Exception as e:
            logger.error(f"Error in background removal service: {str(e)}")
            raise RuntimeError(f"Background removal failed: {str(e)}")
