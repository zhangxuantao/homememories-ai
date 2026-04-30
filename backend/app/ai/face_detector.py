# backend/app/ai/face_detector.py
import os
import threading
import numpy as np
from PIL import Image


class FaceDetector:
    """Lazy singleton for InsightFace buffalo_l. Detection + embedding in one pass."""
    _instance = None
    _lock = threading.Lock()

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
        import insightface

        self.model = insightface.app.FaceAnalysis(name="buffalo_l")
        self.model.prepare(ctx_id=0, det_size=(640, 640))
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "FaceDetector":
        inst = cls()
        inst._ensure_loaded()
        return inst

    def detect(self, image_path: str, thumb_dir: str | None = None) -> list[dict]:
        self._ensure_loaded()
        try:
            img = Image.open(image_path).convert("RGB")
        except Exception:
            return []

        img_np = np.array(img)
        faces = self.model.get(img_np)

        results = []
        for i, face in enumerate(faces):
            bbox = [float(face.bbox[0]), float(face.bbox[1]),
                    float(face.bbox[2]), float(face.bbox[3])]
            embedding = face.embedding.astype(np.float32)

            thumb_path = None
            if thumb_dir is not None:
                os.makedirs(thumb_dir, exist_ok=True)
                try:
                    face_img = img.crop((int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])))
                    face_img = face_img.resize((160, 160))
                    face_id = abs(hash(f"{image_path}_{i}")) % (10 ** 10)
                    path = os.path.join(thumb_dir, f"{face_id}.jpg")
                    face_img.save(path, "JPEG", quality=85)
                    thumb_path = path
                except Exception:
                    pass

            results.append({"bbox": bbox, "embedding": embedding, "thumb_path": thumb_path})

        return results
