# backend/app/ai/embedding.py
import threading
import numpy as np
from PIL import Image
import torch
from transformers import ChineseCLIPModel, ChineseCLIPProcessor


class EmbeddingPipeline:
    """Lazy singleton for Chinese CLIP model. Loads on first get_instance() call."""
    _instance = None
    _lock = threading.Lock()
    dim: int = 512

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def _ensure_loaded(self):
        if self._initialized:
            return
        model_name = "OFA-Sys/chinese-clip-vit-base-patch16"
        self.model = ChineseCLIPModel.from_pretrained(model_name)
        self.processor = ChineseCLIPProcessor.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device).eval()
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "EmbeddingPipeline":
        inst = cls()
        inst._ensure_loaded()
        return inst

    def embed_images(self, image_paths: list[str], batch_size: int = 32) -> np.ndarray:
        self._ensure_loaded()
        all_embeddings = []
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            images = []
            for p in batch_paths:
                try:
                    images.append(Image.open(p).convert("RGB"))
                except Exception:
                    continue
            if not images:
                continue
            inputs = self.processor(images=images, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                embeddings = self.model.get_image_features(**inputs)
            if isinstance(embeddings, torch.Tensor):
                embeddings = embeddings.cpu().numpy()
            embeddings = embeddings.astype(np.float32)
            # L2 normalize
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / (norms + 1e-8)
            all_embeddings.append(embeddings)
        return np.concatenate(all_embeddings, axis=0) if all_embeddings else np.empty((0, 512), dtype=np.float32)

    def embed_text(self, texts: list[str]) -> np.ndarray:
        self._ensure_loaded()
        inputs = self.processor(text=texts, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            embeddings = self.model.get_text_features(**inputs)
        if isinstance(embeddings, torch.Tensor):
            embeddings = embeddings.cpu().numpy()
        embeddings = embeddings.astype(np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / (norms + 1e-8)
        return embeddings
