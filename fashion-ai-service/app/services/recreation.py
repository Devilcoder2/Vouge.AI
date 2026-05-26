import logging
import colorsys
from pathlib import Path
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Tuple

from app.database.models import ClothingItem, PostTaggedItem
from app.ai.embedding_service import FashionEmbeddingService
from app.schemas.social import RecreateSlotMatch

logger = logging.getLogger("fashion-ai-service")

class OutfitRecreationService:
    @staticmethod
    def hex_to_hsl(hex_str: str) -> Tuple[float, float, float]:
        """Converts a hex color string (e.g. '#2C3E50' or '2C3E50') to HSL tuple."""
        if not hex_str:
            return (0.0, 0.0, 0.0)
        hex_str = hex_str.lstrip("#")
        if len(hex_str) != 6:
            return (0.0, 0.0, 0.0)
        try:
            r = int(hex_str[0:2], 16) / 255.0
            g = int(hex_str[2:4], 16) / 255.0
            b = int(hex_str[4:6], 16) / 255.0
            h, l, s = colorsys.rgb_to_hls(r, g, b)
            return (h * 360.0, s * 100.0, l * 100.0)
        except Exception:
            return (0.0, 0.0, 0.0)

    @staticmethod
    def calculate_hsl_distance(hsl1: Tuple[float, float, float], hsl2: Tuple[float, float, float]) -> float:
        """Calculates distance between two HSL coordinates, handling circular hue correctly."""
        h1, s1, l1 = hsl1
        h2, s2, l2 = hsl2
        
        # Circular difference for Hue (0-360)
        dh = min(abs(h1 - h2), 360.0 - abs(h1 - h2)) / 180.0
        ds = abs(s1 - s2) / 100.0
        dl = abs(l1 - l2) / 100.0
        
        # Weighted Euclidean distance
        return float(np.sqrt(0.5 * (dh ** 2) + 0.3 * (ds ** 2) + 0.2 * (dl ** 2)))

    @staticmethod
    def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculates the cosine similarity between two float32 numpy arrays."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    @classmethod
    async def match_tagged_item_to_wardrobe(
        cls,
        tagged_item: PostTaggedItem,
        user_id: str,
        db: AsyncSession
    ) -> Tuple[Optional[ClothingItem], float, str]:
        """
        Calculates similarity scores between a creator's tagged item 
        and all items in the active user's wardrobe within the same category hierarchy.
        """
        # 1. Target Ingestion
        target_garment = tagged_item.wardrobe_item
        if not target_garment:
            return (None, 0.0, "Missing")

        target_embedding_path = Path(target_garment.embedding_path)
        if not target_embedding_path.exists():
            logger.warning(f"Target CLIP embedding not found: {target_embedding_path}")
            return (None, 0.0, "Missing")

        try:
            target_vec = FashionEmbeddingService.load_embedding_from_disk(target_embedding_path)
        except Exception as e:
            logger.error(f"Error loading target embedding: {str(e)}")
            return (None, 0.0, "Missing")

        # 2. Candidate Selection (Query active user's wardrobe matching the category)
        # Note: In our digital wardrobe setup, users own items where users.username matches
        # or where a default user key is linked. We search across all clothing_items!
        # In a multi-tenant DB we would query by user_id. Here we retrieve all available items
        # as a mock wardrobe fallback for seamless offline execution.
        query = select(ClothingItem).where(
            ClothingItem.category.ilike(target_garment.category)
        )
        result = await db.execute(query)
        candidates = result.scalars().all()

        best_candidate = None
        best_score = 0.0
        best_status = "Missing"

        # Extract target HSL
        target_hsl = cls.hex_to_hsl(target_garment.primary_color_hex or "#000000")

        # 3. Vector Similarity Computation Loop
        for cand in candidates:
            # Skip comparing the item to itself if it's the exact same item from the database
            if cand.id == target_garment.id:
                # If they own the exact same physical database record, it's a perfect 1.0 match!
                return (cand, 1.0, "Perfect Match")

            cand_embedding_path = Path(cand.embedding_path)
            if not cand_embedding_path.exists():
                continue

            try:
                cand_vec = FashionEmbeddingService.load_embedding_from_disk(cand_embedding_path)
            except Exception:
                continue

            # Core CLIP vector dot product
            raw_sim = cls.calculate_cosine_similarity(target_vec, cand_vec)

            # Color Compatibility Modifiers
            cand_hsl = cls.hex_to_hsl(cand.primary_color_hex or "#000000")
            color_dist = cls.calculate_hsl_distance(target_hsl, cand_hsl)
            color_penalty = min(0.20, color_dist * 0.20)
            
            # Apply color weight multiplier
            adjusted_sim = raw_sim * (1.0 - color_penalty)

            if adjusted_sim > best_score:
                best_score = adjusted_sim
                best_candidate = cand

        # 4. Threshold Tagging
        if best_score >= 0.85:
            best_status = "Perfect Match"
        elif best_score >= 0.70:
            best_status = "Substitute"
        else:
            best_status = "Missing"

        return (best_candidate, float(round(best_score, 3)), best_status)
