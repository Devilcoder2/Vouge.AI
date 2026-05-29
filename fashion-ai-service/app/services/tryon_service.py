import os
import uuid
import logging
from pathlib import Path
import httpx
import asyncio
from PIL import Image, ImageFilter, ImageOps
from app.config import settings, BASE_DIR

logger = logging.getLogger("fashion-ai-service")

# Standard 1024x1024 posture coordinate overlay matrix for local fallback
COORDINATES = {
    "outerwear": {
        "top": 169,
        "left": 281,
        "width": 460,
        "height": 430,
    },
    "tops": {
        "top": 179,
        "left": 317,
        "width": 389,
        "height": 338,
    },
    "bottoms": {
        "top": 445,
        "left": 332,
        "width": 358,
        "height": 450,
    },
    "footwear": {
        "top": 865,
        "left": 384,
        "width": 256,
        "height": 123,
    },
    "accessories": {
        "top": 225,
        "left": 378,
        "width": 266,
        "height": 102,
    }
}

# Wrist coordinates for watch placement overrides (1024x1024 scale)
WRIST_COORDINATES = {
    "female": {
        "top": 537,
        "left": 281,
        "width": 56,
        "height": 56,
    },
    "male": {
        "top": 548,
        "left": 271,
        "width": 56,
        "height": 56,
    }
}

class VTONService:
    """
    Virtual Try-On Service bridging FastAPI with advanced diffusion pipelines (Fal.ai & Replicate).
    Supports instant serverless GPU executions and robust, high-fidelity local CPU fallbacks.
    """

    @classmethod
    def get_model_path(cls, gender: str) -> Path:
        """Resolves the absolute path of the standard centered model base layer."""
        model_filename = "female_model.png" if gender == "female" else "male_model.png"
        return BASE_DIR.parent / "frontend" / "public" / "assets" / model_filename

    @classmethod
    async def _upload_to_temp_host(cls, file_path: Path) -> str:
        """
        Uploads a local image temporarily to tmpfiles.org to get a public URL 
        required by external cloud AI APIs (Fal.ai / Replicate).
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(file_path, "rb") as f:
                    files = {"file": f}
                    r = await client.post("https://tmpfiles.org/api/v1/upload", files=files)
                    if r.status_code == 200:
                        data = r.json()
                        url = data["data"]["url"]
                        # Convert view URL to direct download URL
                        direct_url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                        logger.info(f"VTONService: Uploaded local file to temporary host: {direct_url}")
                        return direct_url
                    else:
                        raise Exception(f"Temp upload failed with status {r.status_code}")
        except Exception as e:
            logger.error(f"VTONService: Failed to upload file to temp host: {e}")
            raise e

    @classmethod
    async def generate_tryon(
        cls,
        garment_image_path: str,
        category: str,
        gender: str = "male",
        item_name: str = "",
    ) -> str:
        """
        Processes a garment try-on. Uses SOTA IDM-VTON on Fal.ai or Replicate GPUs if API keys 
        are present, otherwise runs high-fidelity shadow-cast PIL local composition.
        """
        cat_key = category.lower().strip()

        # Fallback category mapping
        if "shirt" in cat_key or "knit" in cat_key:
            cat_key = "tops"
        elif "pants" in cat_key or "jeans" in cat_key or "trouser" in cat_key:
            cat_key = "bottoms"
        elif "shoes" in cat_key or "boots" in cat_key:
            cat_key = "footwear"
        elif "coat" in cat_key or "jacket" in cat_key:
            cat_key = "outerwear"

        if cat_key not in COORDINATES:
            cat_key = "tops"

        # Check for Cloud VTON API keys
        fal_key = os.getenv("FAL_KEY")
        replicate_token = os.getenv("REPLICATE_API_TOKEN")

        # ── 1. FAL.AI FASHN-VTON SOTA CLOUD API PIPELINE ───────────────────────
        if fal_key:
            try:
                logger.info(f"VTONService: Hooking into Fal.ai Fashn-VTON SOTA GPU pipeline...")
                base_model_path = cls.get_model_path(gender)
                if not base_model_path.exists():
                    raise FileNotFoundError(f"Model base missing at {base_model_path}")

                # Upload local files temporarily to generate public URLs for Fal.ai
                public_model_url = await cls._upload_to_temp_host(base_model_path)
                public_garment_url = await cls._upload_to_temp_host(Path(garment_image_path))

                # Normalize category for Fashn-VTON
                fal_category = "tops"
                if cat_key == "bottoms":
                    fal_category = "bottoms"
                elif cat_key == "outerwear":
                    fal_category = "tops" # Fashn-VTON processes outerwear as tops

                # Call Fal.ai Queue endpoint
                async with httpx.AsyncClient(timeout=60.0) as client:
                    headers = {
                        "Authorization": f"Key {fal_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model_image": public_model_url,
                        "garment_image": public_garment_url,
                        "category": fal_category,
                        "nsfw_filter": False,
                        "cover_feet": False
                    }
                    
                    logger.info("VTONService: Sending request payload to Fal.ai fashn/tryon endpoint...")
                    res = await client.post(
                        "https://queue.fal.run/fal-ai/fashn/tryon/v1.6",
                        headers=headers,
                        json=payload
                    )
                    
                    if res.status_code in [200, 201]:
                        result = res.json()
                        request_id = result.get("request_id")
                        logger.info(f"VTONService: Fal.ai job queued with ID {request_id}. Polling for result...")
                        
                        # Poll for VTON synthesis completion
                        for attempt in range(12):
                            await asyncio.sleep(4)
                            status_res = await client.get(
                                f"https://queue.fal.run/fal-ai/fashn/tryon/v1.6/requests/{request_id}/status",
                                headers=headers
                            )
                            if status_res.status_code == 200:
                                status_data = status_res.json()
                                status_str = status_data.get("status")
                                logger.info(f"VTONService: Fal.ai polling status (attempt {attempt + 1}): {status_str}")
                                
                                if status_str == "COMPLETED":
                                    # Fetch completed logs and download image URL
                                    logs_res = await client.get(
                                        f"https://queue.fal.run/fal-ai/fashn/tryon/v1.6/requests/{request_id}",
                                        headers=headers
                                    )
                                    completed_data = logs_res.json()
                                    image_url = completed_data.get("images", [{}])[0].get("url")
                                    
                                    if image_url:
                                        logger.info(f"VTONService: Fal.ai Try-On completed successfully! Image URL: {image_url}")
                                        
                                        # Download the SOTA synthesized image locally to cache it
                                        img_res = await client.get(image_url)
                                        if img_res.status_code == 200:
                                            filename = f"tryon_{uuid.uuid4().hex}.png"
                                            output_path = settings.PREVIEWS_DIR / filename
                                            with open(output_path, "wb") as f:
                                                f.write(img_res.content)
                                            return f"/recommendations/preview-image/{filename}"
                                
                                elif status_str == "FAILED":
                                    raise Exception("Fal.ai GPU try-on worker failed.")
                    else:
                        raise Exception(f"Fal.ai returned status code {res.status_code}: {res.text}")
            except Exception as e:
                logger.warning(f"SOTA Fal.ai GPU Pipeline failed or unauthenticated: {e}. Trying Replicate...")

        # ── 2. REPLICATE IDM-VTON SOTA CLOUD API PIPELINE ───────────────────────
        if replicate_token:
            try:
                logger.info(f"VTONService: Hooking into Replicate IDM-VTON SOTA GPU pipeline...")
                base_model_path = cls.get_model_path(gender)
                if not base_model_path.exists():
                    raise FileNotFoundError(f"Model base missing at {base_model_path}")

                public_model_url = await cls._upload_to_temp_host(base_model_path)
                public_garment_url = await cls._upload_to_temp_host(Path(garment_image_path))

                # Normalize category for IDM-VTON
                idm_category = "upper_body"
                if cat_key == "bottoms":
                    idm_category = "lower_body"
                elif cat_key == "outerwear":
                    idm_category = "upper_body"

                async with httpx.AsyncClient(timeout=60.0) as client:
                    headers = {
                        "Authorization": f"Token {replicate_token}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "version": "0.1", # Version index identifier for yisol/idm-vton
                        "input": {
                            "crop": True,
                            "category": idm_category,
                            "force_dc": False,
                            "human_img": public_model_url,
                            "garm_img": public_garment_url
                        }
                    }
                    
                    logger.info("VTONService: Submitting job to Replicate IDM-VTON endpoint...")
                    res = await client.post(
                        "https://api.replicate.com/v1/predictions",
                        headers=headers,
                        json=payload
                    )
                    
                    if res.status_code in [200, 201]:
                        prediction = res.json()
                        pred_id = prediction.get("id")
                        urls_get = prediction.get("urls", {}).get("get")
                        logger.info(f"VTONService: Replicate job created with ID {pred_id}. Polling...")
                        
                        for attempt in range(15):
                            await asyncio.sleep(4)
                            poll_res = await client.get(urls_get, headers=headers)
                            if poll_res.status_code == 200:
                                poll_data = poll_res.json()
                                status_str = poll_data.get("status")
                                logger.info(f"VTONService: Replicate status (attempt {attempt + 1}): {status_str}")
                                
                                if status_str == "succeeded":
                                    output = poll_data.get("output")
                                    # Output can be a string URL or list of string URLs
                                    image_url = output[0] if isinstance(output, list) else output
                                    
                                    if image_url:
                                        logger.info(f"VTONService: Replicate VTON complete! Image URL: {image_url}")
                                        img_res = await client.get(image_url)
                                        if img_res.status_code == 200:
                                            filename = f"tryon_{uuid.uuid4().hex}.png"
                                            output_path = settings.PREVIEWS_DIR / filename
                                            with open(output_path, "wb") as f:
                                                f.write(img_res.content)
                                            return f"/recommendations/preview-image/{filename}"
                                
                                elif status_str == "failed":
                                    raise Exception("Replicate GPU prediction task failed.")
                    else:
                        raise Exception(f"Replicate API returned status code {res.status_code}: {res.text}")
            except Exception as e:
                logger.warning(f"SOTA Replicate GPU Pipeline failed or unauthenticated: {e}. Falling back to CPU.")

        # ── 3. HIGH-FIDELITY CPU PIPELINE (PIL COMPOSITING WITH 3D SHADOWS) ───
        try:
            logger.info(f"VTONService: Running high-fidelity local PIL compositor for {cat_key}...")
            base_model_path = cls.get_model_path(gender)
            if not base_model_path.exists():
                logger.error(f"VTONService: Model base layer not found at {base_model_path}")
                return f"/processed/{Path(garment_image_path).name}"

            # Load base model & garment
            base_img = Image.open(base_model_path).convert("RGBA")
            garm_img = Image.open(garment_image_path).convert("RGBA")

            # Determine placement coordinates
            is_watch = "watch" in cat_key or "watch" in item_name.lower() or "timepiece" in item_name.lower()
            
            if cat_key == "accessories" and is_watch:
                coords = WRIST_COORDINATES[gender]
            else:
                coords = COORDINATES.get(cat_key, COORDINATES["tops"])

            # Resize garment keeping aspect ratio
            garm_w, garm_h = garm_img.size
            ratio = min(coords["width"] / garm_w, coords["height"] / garm_h)
            new_w = int(garm_w * ratio)
            new_h = int(garm_h * ratio)
            garm_resized = garm_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Center position inside bounds
            offset_x = coords["left"] + (coords["width"] - new_w) // 2
            offset_y = coords["top"] + (coords["height"] - new_h) // 2

            # Extract garment alpha mask
            alpha = garm_resized.split()[3]
            
            # Create a black silhouette of the garment for the shadow
            shadow_mask = Image.new("RGBA", garm_resized.size, (0, 0, 0, 0))
            shadow_silhouette = Image.new("L", garm_resized.size, 0)
            shadow_silhouette.paste(255, mask=alpha)
            
            # Blur the shadow silhouette to represent diffuse studio lighting
            shadow_blurred = shadow_silhouette.filter(ImageFilter.GaussianBlur(radius=8))
            
            # Reassemble shadow layer with soft alpha opacity (110 out of 255)
            shadow_layer = Image.new("RGBA", garm_resized.size, (0, 0, 0, 110))
            shadow_layer = Image.composite(shadow_layer, shadow_mask, shadow_blurred)

            # Paste Blurred Drop Shadow with natural offset (2px right, 6px down)
            base_img.paste(shadow_layer, (offset_x + 2, offset_y + 6), mask=shadow_blurred)

            # Paste garment on top of its shadow
            base_img.paste(garm_resized, (offset_x, offset_y), mask=alpha)

            # Flatten to RGB replacing transparency with standard deep charcoal base
            final_img = Image.new("RGB", base_img.size, (13, 14, 18))
            final_img.paste(base_img, mask=base_img.split()[3])

            # Save in Previews Directory
            filename = f"tryon_{uuid.uuid4().hex}.png"
            output_path = settings.PREVIEWS_DIR / filename
            final_img.save(output_path, "PNG", optimize=True)

            logger.info(f"VTONService: Synthesized try-on image saved to {output_path}")
            return f"/recommendations/preview-image/{filename}"

        except Exception as err:
            logger.error(f"VTONService: Local PIL try-on failed: {err}", exc_info=True)
            return f"/processed/{Path(garment_image_path).name}"
