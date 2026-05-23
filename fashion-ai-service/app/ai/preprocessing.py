import logging
from PIL import Image

logger = logging.getLogger("fashion-ai-service")

class ImagePreprocessor:
    @staticmethod
    def preprocess_image(transparent_img: Image.Image, target_size: int = 512) -> Image.Image:
        """
        Takes a transparent RGBA PIL Image, crops whitespace/transparency margins, 
        pads it to a 1:1 aspect ratio, and resizes to standard target dimensions (e.g., 512x512).
        """
        try:
            # Ensure image is in RGBA mode
            if transparent_img.mode != "RGBA":
                transparent_img = transparent_img.convert("RGBA")

            # 1. Detect transparent bounding box of the actual garment
            bbox = transparent_img.getbbox()
            if not bbox:
                logger.warning("Empty transparent image received. Skipping crop/pad sequence.")
                # Return original resized if no non-transparent pixels exist
                return transparent_img.resize((target_size, target_size), Image.Resampling.LANCZOS)

            # Crop to physical garment edges
            cropped_img = transparent_img.crop(bbox)
            width, height = cropped_img.size
            logger.info(f"Cropped image bounding box from {transparent_img.size} to {cropped_img.size}")

            # 2. Pad to a 1:1 square ratio to prevent distortion
            max_side = max(width, height)
            square_img = Image.new("RGBA", (max_side, max_side), (0, 0, 0, 0))
            
            # Center the cropped garment in the square frame
            offset_x = (max_side - width) // 2
            offset_y = (max_side - height) // 2
            square_img.paste(cropped_img, (offset_x, offset_y))
            
            # 3. Resize to target dimension (e.g., 512x512) using high-quality Lanczos resampling
            final_img = square_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
            logger.info(f"Padded and resized image to {target_size}x{target_size} square PNG.")
            
            return final_img

        except Exception as e:
            logger.error(f"Error in image preprocessing: {str(e)}")
            raise RuntimeError(f"Preprocessing failed: {str(e)}")
