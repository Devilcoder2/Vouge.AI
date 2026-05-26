import logging
from pathlib import Path
from PIL import Image
import numpy as np
import torch
from transformers import CLIPProcessor, CLIPModel
from app.config import settings

logger = logging.getLogger("fashion-ai-service")

class FashionEmbeddingService:
    def __init__(self):
        self.model_name = settings.CLIP_MODEL_NAME
        self.model = None
        self.processor = None
        
        # 1. Device Auto-Detection: support MPS (Apple Silicon GPU), CUDA (Nvidia), and CPU
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
            logger.info("FashionEmbeddingService: Apple Silicon GPU (MPS) detected for local acceleration.")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
            logger.info("FashionEmbeddingService: NVIDIA GPU (CUDA) detected.")
        else:
            self.device = torch.device("cpu")
            logger.info("FashionEmbeddingService: Fallback to CPU execution.")

    def _lazy_load(self):
        """Loads CLIP model and processor into VRAM/RAM lazily on first request."""
        if self.model is None or self.processor is None:
            logger.info(f"Loading local CLIP model '{self.model_name}' into {self.device} memory...")
            try:
                self.model = CLIPModel.from_pretrained(self.model_name).to(self.device)
                self.processor = CLIPProcessor.from_pretrained(self.model_name)
                # Set evaluation mode to disable dropouts/gradients
                self.model.eval()
                logger.info("CLIP model successfully loaded.")
            except Exception as e:
                logger.error(f"Failed to load CLIP model: {str(e)}")
                raise RuntimeError(f"Neural net loading failed: {str(e)}")

    def generate_image_embedding(self, pil_image: Image.Image) -> np.ndarray:
        """
        Passes a PIL Image through CLIP, executes L2 normalization, 
        and outputs a 512-dimensional float32 numpy vector.
        """
        self._lazy_load()
        
        try:
            # 2. Preprocess image using HuggingFace processor
            inputs = self.processor(images=pil_image, return_tensors="pt")
            
            # Move inputs to target hardware (GPU/MPS/CPU)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # 3. Feed-forward pass with gradient tracking disabled
            with torch.no_grad():
                outputs = self.model.get_image_features(**inputs)
                
                # Extract PyTorch tensor from model outputs (handles newer transformers versions)
                if hasattr(outputs, "pooler_output"):
                    image_features = outputs.pooler_output
                else:
                    image_features = outputs
                
                # 4. Standardize embedding: Perform L2 normalization
                # L2 norm allows simple dot-products for cosine similarity matches in vector DBs
                normalized_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
                
                # Copy tensor from device memory back to CPU numpy array
                embedding = normalized_features[0].cpu().numpy().astype(np.float32)
                
            logger.info(f"Generated CLIP embedding array with shape: {embedding.shape}")
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise RuntimeError(f"Embedding pipeline failed: {str(e)}")

    def generate_text_embedding(self, text: str) -> np.ndarray:
        """
        Passes a text query through CLIP processor, executes L2 normalization,
        and outputs a 512-dimensional float32 numpy vector.
        """
        self._lazy_load()
        
        try:
            inputs = self.processor(text=[text], return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.get_text_features(**inputs)
                normalized_features = outputs / outputs.norm(p=2, dim=-1, keepdim=True)
                embedding = normalized_features[0].cpu().numpy().astype(np.float32)
                
            logger.info(f"Generated CLIP text embedding array with shape: {embedding.shape}")
            return embedding

        except Exception as e:
            logger.error(f"Text embedding generation failed: {str(e)}")
            raise RuntimeError(f"Text embedding pipeline failed: {str(e)}")


    @staticmethod
    def save_embedding_to_disk(embedding: np.ndarray, item_id: str) -> Path:
        """Saves a raw numpy vector array as a binary float32 .npy file locally."""
        filename = f"{item_id}.npy"
        filepath = settings.EMBEDDING_DIR / filename
        
        try:
            np.save(filepath, embedding)
            logger.info(f"Saved binary vector file locally: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to write vector file: {str(e)}")
            raise IOError(f"Disk write for vector failed: {str(e)}")

    @staticmethod
    def load_embedding_from_disk(filepath: Path) -> np.ndarray:
        """Loads a binary float32 numpy array vector back from local disk."""
        try:
            return np.load(filepath)
        except Exception as e:
            logger.error(f"Failed to read vector file: {str(e)}")
            raise IOError(f"Disk read for vector failed: {str(e)}")
