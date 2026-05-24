import logging
import time
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from PIL import Image
import numpy as np

from app.config import settings
from app.utils.file_handler import FileHandler
from app.ai.background_removal import BackgroundRemover
from app.ai.preprocessing import ImagePreprocessor
from app.ai.classifier import FashionClassifier
from app.ai.color_extractor import ColorExtractor
from app.ai.embedding_service import FashionEmbeddingService
from app.database.models import ClothingItem
from app.services.duplicate_detector import DuplicateDetector


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
        
        # Track start time of entire pipeline execution
        pipeline_start = time.perf_counter()
        
        try:
            # 1. Image Upload: Save incoming raw upload to disk
            logger.info(f"Pipeline started for raw upload: {file.filename}")
            upload_start = time.perf_counter()
            raw_filepath = await FileHandler.save_upload(file)
            upload_latency = (time.perf_counter() - upload_start) * 1000
            logger.info(f"Raw image saved locally: {raw_filepath} (time: {upload_latency:.2f}ms)")

            # 2. Background Removal: Remove background to get transparent PNG
            bg_removal_start = time.perf_counter()
            with open(raw_filepath, "rb") as f:
                raw_bytes = f.read()
            
            transparent_img = BackgroundRemover.remove_background(raw_bytes)
            bg_removal_latency = (time.perf_counter() - bg_removal_start) * 1000
            logger.info(f"Successfully removed background (time: {bg_removal_latency:.2f}ms)")

            # 3. Image Preprocessing: Crop transparent margins, pad to square, resize to 512x512
            preprocess_start = time.perf_counter()
            processed_img = ImagePreprocessor.preprocess_image(transparent_img, target_size=512)

            # Save transparent standardized 512x512 image in the processed folder
            processed_filename = f"{raw_filepath.stem}_processed.png"
            processed_filepath = settings.PROCESSED_DIR / processed_filename
            processed_img.save(processed_filepath, format="PNG")
            preprocess_latency = (time.perf_counter() - preprocess_start) * 1000
            logger.info(f"Processed transparent image written to disk: {processed_filepath} (time: {preprocess_latency:.2f}ms)")

            # 4. Fashion Classification: Feed transparent garment into Gemini Vision
            # Use raw filename as a hint in case we run in mock mode
            classify_start = time.perf_counter()
            extracted_metadata = self.classifier.classify_garment(processed_img, filename_hint=file.filename)
            classify_latency = (time.perf_counter() - classify_start) * 1000
            logger.info(f"Fashion classification step completed successfully (time: {classify_latency:.2f}ms).")

            # --- Multi-Item Validation Check ---
            # Reject uploads containing more than 1 item to maintain wardrobe quality
            if extracted_metadata.detected_items_count > 1:
                logger.warning(
                    f"Multi-item validation failed: Detected {extracted_metadata.detected_items_count} clothing items."
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Detected {extracted_metadata.detected_items_count} clothing items. Please upload one item only."
                )

            # 5. Color Extraction: OpenCV LAB KMeans (Returns Names + Precise Hexes)
            color_start = time.perf_counter()
            primary_color, secondary_colors, primary_hex, secondary_hexes = ColorExtractor.extract_colors(processed_img)
            color_latency = (time.perf_counter() - color_start) * 1000
            logger.info(f"Color extraction completed: Primary hex: {primary_hex} (time: {color_latency:.2f}ms)")

            # 6. Embedding Generation: PyTorch local CLIP
            embedding_start = time.perf_counter()
            embedding = self.embedding_service.generate_image_embedding(processed_img)
            
            # Save raw numpy array binary file locally
            embedding_filepath = FashionEmbeddingService.save_embedding_to_disk(embedding, raw_filepath.stem)
            embedding_latency = (time.perf_counter() - embedding_start) * 1000
            logger.info(f"CLIP embedding generated and saved (time: {embedding_latency:.2f}ms)")

            # --- Duplicate Detection (Double-Moat: dHash + Cosine) ---
            duplicate_start = time.perf_counter()
            perceptual_hash = DuplicateDetector.calculate_dhash(processed_img)
            
            # Retrieve existing wardrobe items
            result = await db.execute(select(ClothingItem))
            existing_items = result.scalars().all()
            
            is_duplicate, duplicate_of_id = DuplicateDetector.check_duplicates(
                processed_img,
                embedding,
                existing_items
            )
            
            duplicate_latency = (time.perf_counter() - duplicate_start) * 1000

            # 7. Database Persistence: Save full structured details to PostgreSQL
            db_start = time.perf_counter()
            db_item = ClothingItem(
                original_image_path=str(raw_filepath),
                processed_image_path=str(processed_filepath),
                category=extracted_metadata.category.value,
                confidence_category=extracted_metadata.category.confidence,
                subcategory=extracted_metadata.subcategory.value,
                confidence_subcategory=extracted_metadata.subcategory.confidence,
                primary_color=extracted_metadata.primary_color,
                primary_color_hex=primary_hex,
                secondary_colors=extracted_metadata.secondary_colors,
                secondary_colors_hex=secondary_hexes,
                fit=extracted_metadata.fit.value,
                confidence_fit=extracted_metadata.fit.confidence,
                style=extracted_metadata.style.value,
                confidence_style=extracted_metadata.style.confidence,
                formality=extracted_metadata.formality,
                seasons=extracted_metadata.seasons,
                pattern=extracted_metadata.pattern.value,
                confidence_pattern=extracted_metadata.pattern.confidence,
                prompt_version=self.classifier.PROMPT_VERSION,
                detected_items_count=extracted_metadata.detected_items_count,
                is_duplicate=is_duplicate,
                duplicate_of_id=duplicate_of_id,
                perceptual_hash=perceptual_hash,
                embedding_path=str(embedding_filepath)
            )


            db.add(db_item)
            await db.commit()
            await db.refresh(db_item)
            db_latency = (time.perf_counter() - db_start) * 1000
            
            total_latency = (time.perf_counter() - pipeline_start) * 1000
            
            # --- Latency & Pipeline Traceability Logging ---
            logger.info(
                f"\n=== PIPELINE EXECUTION SUCCESS TRACE ===\n"
                f"File Processed: {file.filename}\n"
                f"Item Database ID: {db_item.id}\n"
                f"Stage Latencies:\n"
                f"  - Upload Save:       {upload_latency:.2f}ms\n"
                f"  - BG Removal (rembg): {bg_removal_latency:.2f}ms\n"
                f"  - Image Preprocess:  {preprocess_latency:.2f}ms\n"
                f"  - Gemini Classifier: {classify_latency:.2f}ms\n"
                f"  - Color Extractor:   {color_latency:.2f}ms\n"
                f"  - CLIP Embedding:    {embedding_latency:.2f}ms\n"
                f"  - Duplicate Check:   {duplicate_latency:.2f}ms\n"
                f"  - DB Persistence:    {db_latency:.2f}ms\n"
                f"Total Pipeline Latency: {total_latency:.2f}ms\n"
                f"========================================="
            )
            
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
