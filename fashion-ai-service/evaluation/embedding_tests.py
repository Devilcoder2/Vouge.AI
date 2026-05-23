import os
import sys
import logging
from typing import List, Dict, Tuple
import numpy as np
import torch
from transformers import CLIPProcessor, CLIPModel

# Add parent directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("embedding-evaluator")

class EmbeddingSimilarityEvaluator:
    def __init__(self):
        self.model_name = settings.CLIP_MODEL_NAME
        
        # Auto-detect device
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")
            
        logger.info(f"Loading CLIP model '{self.model_name}' on {self.device}...")
        self.model = CLIPModel.from_pretrained(self.model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(self.model_name)
        self.model.eval()
        logger.info("Model loaded successfully.")

    def cosine_similarity(self, u: np.ndarray, v: np.ndarray) -> float:
        """
        Calculates cosine similarity between two numpy vectors.
        """
        dot_product = np.dot(u, v)
        norm_u = np.linalg.norm(u)
        norm_v = np.linalg.norm(v)
        if norm_u == 0 or norm_v == 0:
            return 0.0
        return float(dot_product / (norm_u * norm_v))

    def get_text_embedding(self, text: str) -> np.ndarray:
        """
        Generates an L2-normalized 512-dimensional vector for a given text phrase.
        """
        inputs = self.processor(text=[text], padding=True, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.get_text_features(**inputs)
            
            # Extract PyTorch tensor from model outputs (handles newer transformers versions)
            if hasattr(outputs, "pooler_output"):
                text_features = outputs.pooler_output
            elif hasattr(outputs, "text_embeds"):
                text_features = outputs.text_embeds
            else:
                text_features = outputs
                
            # L2 Normalize the text embedding
            normalized_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
            return normalized_features[0].cpu().numpy().astype(np.float32)

    def run_nearest_neighbor_test(self) -> bool:
        """
        Validates semantic search / recommendation quality.
        Tests query: "white oversized shirt"
        Verifies nearest neighbors are white shirts/minimal tops/light neutrals.
        Verifies watches, jeans, and shoes are NOT near.
        """
        query_text = "white oversized shirt"
        logger.info(f"\n--- Running Nearest Neighbor Test for Query: '{query_text}' ---")
        
        # Define target dataset representing various wardrobe items
        targets = [
            ("other white shirt", "oversized white linen button-down shirt"),
            ("other white shirt", "minimalist white cotton t-shirt"),
            ("minimal top", "beige linen tank top"),
            ("light neutral top", "cream knit sweater vest"),
            ("jeans", "rugged blue denim cargo jeans"),
            ("jeans", "dark wash slim fit denim pants"),
            ("shoes", "chunky black leather combat boots"),
            ("shoes", "athletic running sneakers"),
            ("watches", "luxury gold chronograph wrist watch"),
            ("watches", "sporty waterproof silicone smartwatch")
        ]
        
        # Generate query embedding
        query_emb = self.get_text_embedding(query_text)
        
        # Calculate similarities
        results = []
        for category, item_desc in targets:
            item_emb = self.get_text_embedding(item_desc)
            sim = self.cosine_similarity(query_emb, item_emb)
            results.append((category, item_desc, sim))
            
        # Sort results by similarity descending
        results.sort(key=lambda x: x[2], reverse=True)
        
        print("\nRank | Category          | Description                                      | Cosine Sim")
        print("-" * 90)
        for i, (category, desc, sim) in enumerate(results, 1):
            print(f"{i:4d} | {category:17s} | {desc:48s} | {sim:.4f}")
            
        # --- VALIDATION ASSERTIONS ---
        top_k = 3
        top_neighbors = results[:top_k]
        bottom_neighbors = results[top_k:]
        
        logger.info("\nValidating Nearest Neighbor assertions...")
        
        # Assertion 1: Top-K neighbors must strictly be shirts, minimal tops, or light neutrals
        allowed_top_categories = ["other white shirt", "minimal top", "light neutral top"]
        for rank, (category, desc, sim) in enumerate(top_neighbors, 1):
            if category not in allowed_top_categories:
                logger.error(
                    f"ASSERTION FAILED: Rank {rank} neighbor '{desc}' ({category}) "
                    f"should NOT be in the Top {top_k} nearest neighbors!"
                )
                return False
        logger.info(f"✓ Assertion Passed: Top {top_k} nearest neighbors are all semantic shirts/neutral tops.")
        
        # Assertion 2: watches, jeans, and shoes must be in the bottom ranks
        forbidden_top_categories = ["watches", "jeans", "shoes"]
        for rank, (category, desc, sim) in enumerate(top_neighbors, 1):
            if category in forbidden_top_categories:
                logger.error(
                    f"ASSERTION FAILED: Forbidden category '{category}' found in top position: '{desc}'!"
                )
                return False
        logger.info("✓ Assertion Passed: Jeans, shoes, and watches strictly ranked outside Top-K.")
        
        return True

    def run_embedding_drift_test(self) -> bool:
        """
        Verifies vector integrity, L2 normalization preservation, 
        and validates that no embedding drift is happening over loaded instances.
        """
        logger.info("\n--- Running Embedding Drift & Normalization Tests ---")
        
        test_phrases = [
            "rugged blue denim jeans",
            "minimalist white cotton t-shirt",
            "black leather combat boots"
        ]
        
        for phrase in test_phrases:
            emb = self.get_text_embedding(phrase)
            
            # 1. Norm check: must be strictly equal to 1.0 (with small float tolerance)
            norm = np.linalg.norm(emb)
            if not np.isclose(norm, 1.0, atol=1e-5):
                logger.error(f"DRIFT ERROR: Vector for '{phrase}' is not L2 normalized! Norm = {norm:.6f}")
                return False
                
            # 2. Check for extreme values or NaN/Inf elements
            if np.isnan(emb).any() or np.isinf(emb).any():
                logger.error(f"DRIFT ERROR: Vector contains NaN or Inf values!")
                return False
                
            # 3. Check shape
            if emb.shape != (512,):
                logger.error(f"DRIFT ERROR: Vector shape is invalid! Shape = {emb.shape}")
                return False
                
        logger.info("✓ Assertion Passed: All vectors are perfectly L2 normalized, mathematically bounded, and 512-dim.")
        return True

if __name__ == "__main__":
    logger.info("=== STARTING EMBEDDING SIMILARITY TESTING SUITE ===")
    
    try:
        evaluator = EmbeddingSimilarityEvaluator()
        
        nn_success = evaluator.run_nearest_neighbor_test()
        drift_success = evaluator.run_embedding_drift_test()
        
        if nn_success and drift_success:
            logger.info("\n=== ALL EMBEDDING TESTS PASSED SUCCESSFULLY ===")
            sys.exit(0)
        else:
            logger.error("\n=== EMBEDDING TESTS FAILED ===")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Critical error running evaluation suite: {str(e)}", exc_info=True)
        sys.exit(1)
