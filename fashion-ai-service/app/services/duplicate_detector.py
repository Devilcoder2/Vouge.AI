"""
Duplicate Detection Service for Vouge.AI.
Combines image perceptual hashing (dHash) and CLIP embedding cosine similarity
to flag identical product uploads, cropped variations, and duplicate screenshots.
"""
from typing import List, Tuple, Optional, Any
import numpy as np
from PIL import Image
from uuid import UUID
from pathlib import Path
import logging

logger = logging.getLogger("fashion-ai-service")

class DuplicateDetector:
    @classmethod
    def calculate_dhash(cls, image: Image.Image, hash_size: int = 8) -> str:
        """
        Calculates the Difference Hash (dHash) of a PIL Image.
        dHash is extremely robust against image resizing, compression, and cropping.
        
        Algorithm:
        1. Resize the image to (hash_size + 1, hash_size) - 9x8 pixels by default.
        2. Convert the image to grayscale.
        3. Compare adjacent pixels horizontally to yield a 64-bit boolean diff matrix.
        4. Convert the 64-bit matrix into a 16-character hexadecimal string.
        """
        # 1. Convert to grayscale and resize to (hash_size + 1, hash_size)
        gray_img = image.convert("L").resize(
            (hash_size + 1, hash_size), 
            Image.Resampling.BILINEAR
        )
        pixels = np.array(gray_img)
        
        # 2. Compare adjacent pixels horizontally
        diff = pixels[:, 1:] > pixels[:, :-1]
        
        # 3. Convert row of booleans to 1 byte, then to hex string
        hex_str = ""
        for row in diff:
            decimal = 0
            for bit in row:
                decimal = (decimal << 1) | int(bit)
            hex_str += f"{decimal:02x}"
            
        return hex_str

    @classmethod
    def hamming_distance(cls, hash1: str, hash2: str) -> int:
        """
        Calculates the Hamming distance between two hex string hashes.
        Hamming distance is the number of bits that differ between the two hashes.
        A distance of 0 means identical visual hashes; <= 4 represents probable crops/screenshots.
        """
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return 999  # Large distance indicating no match
            
        try:
            # Convert hex string hashes to 64-bit binary strings padded with leading zeros
            bin1 = bin(int(hash1, 16))[2:].zfill(len(hash1) * 4)
            bin2 = bin(int(hash2, 16))[2:].zfill(len(hash2) * 4)
            
            return sum(b1 != b2 for b1, b2 in zip(bin1, bin2))
        except Exception as e:
            logger.error(f"Error calculating Hamming distance between '{hash1}' and '{hash2}': {str(e)}")
            return 999

    @classmethod
    def check_duplicates(
        cls,
        image: Image.Image,
        embedding: np.ndarray,
        existing_items: List[Any],
        hash_threshold: int = 4,
        cosine_threshold: float = 0.95
    ) -> Tuple[bool, Optional[UUID]]:
        """
        Double-Moat Duplicate Auditing logic:
        1. Computes the dHash of the new uploaded PIL image.
        2. Loops through existing closet items.
        3. Flags a duplicate if:
           - Hamming Distance between dHashes <= 4 OR
           - Cosine Similarity between CLIP embeddings > 0.95
        """
        if not existing_items:
            return False, None

        # A. Calculate the new image's dHash
        new_dhash = cls.calculate_dhash(image)
        
        # B. L2 normalize the new CLIP vector
        new_vector = embedding / np.linalg.norm(embedding) if np.linalg.norm(embedding) > 0 else embedding

        for item in existing_items:
            # Skip items already flagged as duplicate to avoid propagation
            if getattr(item, "is_duplicate", False):
                continue

            # Moat 1: Image Perceptual Hash Check
            existing_dhash = getattr(item, "perceptual_hash", None)
            if existing_dhash:
                h_dist = cls.hamming_distance(new_dhash, existing_dhash)
                if h_dist <= hash_threshold:
                    logger.warning(
                        f"Duplicate Detected (Perceptual Hashing Moat)! "
                        f"New upload matches item {item.id} with Hamming Distance {h_dist}."
                    )
                    return True, item.id

            # Moat 2: CLIP Embedding Cosine Similarity Check
            existing_emb_path = getattr(item, "embedding_path", None)
            if existing_emb_path and Path(existing_emb_path).exists():
                try:
                    ext_vector = np.load(existing_emb_path)
                    ext_vector_norm = ext_vector / np.linalg.norm(ext_vector) if np.linalg.norm(ext_vector) > 0 else ext_vector
                    
                    similarity = float(np.dot(new_vector, ext_vector_norm))
                    if similarity > cosine_threshold:
                        logger.warning(
                            f"Duplicate Detected (Embedding Cosine Moat)! "
                            f"New upload matches item {item.id} with Cosine Similarity {similarity:.4f}."
                        )
                        return True, item.id
                except Exception as e:
                    logger.error(f"Failed to calculate similarity against existing item {item.id}: {str(e)}")

        return False, None
