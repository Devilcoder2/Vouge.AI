import logging
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from PIL import Image

from app.config import settings
from app.utils.file_handler import FileHandler
from app.ai.background_removal import BackgroundRemover
from app.ai.preprocessing import ImagePreprocessor
from app.ai.classifier import FashionClassifier
from app.ai.color_extractor import ColorExtractor
from app.ai.embedding_service import FashionEmbeddingService
from app.database.models import ClothingItem

logger = logging.getLogger("fashion-ai-service")

class FashionIntelligencePipeline:
    def __init__(self):
        # Lazy load pipeline components
        self.classifier = FashionClassifier()
        self.embedding_service = FashionEmbeddingService()

    async def process_new_clothing(self, file: UploadFile, db: AsyncSession) -> ClothingItem:
        """
        Orchestrates the entire Clothing Intelligence Pipeline end-to-end:
        Upload -> BG Removal -> Pad & Resize -> Gemini Classify -> LAB Colors -> CLIP Embed -> DB Save.
        """
        raw_filepath = None
        processed_filepath = None
        embedding_filepath = None
        
        try:
            # 1. Image Upload: Save incoming raw upload to disk
            logger.info(f"Pipeline started for raw upload: {file.filename}")
            raw_filepath = await FileHandler.save_upload(file)
            logger.info(f"Raw image saved locally: {raw_filepath}")

            # 2. Background Removal: Remove background to get transparent PNG
            # Load raw bytes for rembg U2-Net
            with open(raw_filepath, "rb") as f:
                raw_bytes = f.read()
            
            transparent_img = BackgroundRemover.remove_background(raw_bytes)

            # 3. Image Preprocessing: Crop transparent margins, pad to square, resize to 512x512
            processed_img = ImagePreprocessor.preprocess_image(transparent_img, target_size=512)

            # Save transparent standardized 512x512 image in the processed folder
            processed_filename = f"{raw_filepath.stem}_processed.png"
            processed_filepath = settings.PROCESSED_DIR / processed_filename
            processed_img.save(processed_filepath, format="PNG")
            logger.info(f"Processed transparent image written to disk: {processed_filepath}")

            # 4. Fashion Classification: Feed transparent garment into Gemini Vision
            # Use raw filename as a hint in case we run in mock mode
            extracted_metadata = self.classifier.classify_garment(processed_img, filename_hint=file.filename)
            logger.info("Fashion classification step completed successfully.")

            # 5. Color Extraction: OpenCV LAB KMeans (Returns Names + Precise Hexes)
            primary_color, secondary_colors, primary_hex, secondary_hexes = ColorExtractor.extract_colors(processed_img)

            # 6. Embedding Generation: PyTorch local CLIP
            embedding = self.embedding_service.generate_image_embedding(processed_img)
            
            # Save raw numpy array binary file locally
            embedding_filepath = FashionEmbeddingService.save_embedding_to_disk(embedding, raw_filepath.stem)

            # 7. Database Persistence: Save full structured details to PostgreSQL
            # We store relative or absolute paths (here we store paths as string)
            db_item = ClothingItem(
                original_image_path=str(raw_filepath),
                processed_image_path=str(processed_filepath),
                category=extracted_metadata.category,
                subcategory=extracted_metadata.subcategory,
                primary_color=extracted_metadata.primary_color, # Natively parsed by Vision LLM
                primary_color_hex=primary_hex, # Math centroid hex
                secondary_colors=extracted_metadata.secondary_colors, # Natively parsed by Vision LLM
                secondary_colors_hex=secondary_hexes, # Math centroid hexes
                fit=extracted_metadata.fit,
                style=extracted_metadata.style,
                formality=extracted_metadata.formality,
                seasons=extracted_metadata.seasons,
                pattern=extracted_metadata.pattern,
                embedding_path=str(embedding_filepath)
            )

            db.add(db_item)
            await db.commit()
            await db.refresh(db_item)
            
            logger.info(f"Pipeline succeeded! Saved clothing item to DB with UUID: {db_item.id}")
            return db_item

        except Exception as e:
            # 8. Clean up intermediate disk writes on pipeline failure to preserve storage
            logger.error(f"Clothing pipeline execution failed: {str(e)}. Cleaning up intermediate files...")
            
            if raw_filepath:
                FileHandler.delete_file(raw_filepath)
            if processed_filepath:
                FileHandler.delete_file(processed_filepath)
            if embedding_filepath:
                FileHandler.delete_file(embedding_filepath)

            # Propagate clean FastAPI HTTPException
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Pipeline processing failed: {str(e)}"
            )
