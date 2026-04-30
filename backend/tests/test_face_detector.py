# backend/tests/test_face_detector.py
import sys
import numpy as np
import pytest
from unittest.mock import patch, MagicMock


def test_face_detector_singleton():
    """FaceDetector should be a singleton - same instance on repeated calls."""
    mock_is = MagicMock()
    mock_app = MagicMock()
    mock_is.app.FaceAnalysis.return_value = mock_app

    with patch.dict(sys.modules, {"insightface": mock_is}):
        from app.ai.face_detector import FaceDetector

        # Reset singleton for test
        FaceDetector._instance = None

        d1 = FaceDetector.get_instance()
        d2 = FaceDetector.get_instance()
        assert d1 is d2

        # Second call should not re-import (once loaded)
        mock_is.app.FaceAnalysis.assert_called_once_with(name="buffalo_l")


def test_face_detector_prepares_model():
    """First get_instance call should create model and call prepare(ctx_id=0)."""
    mock_is = MagicMock()
    mock_app = MagicMock()
    mock_is.app.FaceAnalysis.return_value = mock_app

    with patch.dict(sys.modules, {"insightface": mock_is}):
        from app.ai.face_detector import FaceDetector

        # Reset singleton for test
        FaceDetector._instance = None

        FaceDetector.get_instance()

        mock_is.app.FaceAnalysis.assert_called_once_with(name="buffalo_l")
        mock_app.prepare.assert_called_once_with(ctx_id=0, det_size=(640, 640))


def test_detect_returns_faces(tmp_path):
    """detect should return bbox, embedding, thumb_path for each detected face."""
    from PIL import Image

    # Create a simple test image
    img = Image.new("RGB", (640, 480), color=(255, 200, 200))
    img_path = str(tmp_path / "test.jpg")
    img.save(img_path, "JPEG")

    thumb_dir = str(tmp_path / "faces")
    fake_bbox = [10.0, 20.0, 100.0, 120.0]
    fake_embedding = np.random.randn(512).astype(np.float32)

    mock_face = MagicMock()
    mock_face.bbox = fake_bbox
    mock_face.embedding = fake_embedding

    mock_is = MagicMock()
    mock_model = MagicMock()
    mock_model.get.return_value = [mock_face]
    mock_is.app.FaceAnalysis.return_value = mock_model

    with patch.dict(sys.modules, {"insightface": mock_is}):
        from app.ai.face_detector import FaceDetector

        # Reset singleton for test
        FaceDetector._instance = None

        detector = FaceDetector.get_instance()
        results = detector.detect(img_path, thumb_dir=thumb_dir)

    assert len(results) == 1
    r = results[0]
    assert r["bbox"] == fake_bbox
    assert isinstance(r["embedding"], np.ndarray)
    assert np.array_equal(r["embedding"], fake_embedding)
    assert r["thumb_path"] is not None
    assert r["thumb_path"].endswith(".jpg")
    assert "faces" in r["thumb_path"]


def test_detect_no_faces(tmp_path):
    """When model returns no faces, detect should return empty list."""
    from PIL import Image

    img = Image.new("RGB", (640, 480), color=(255, 200, 200))
    img_path = str(tmp_path / "test.jpg")
    img.save(img_path, "JPEG")

    mock_is = MagicMock()
    mock_model = MagicMock()
    mock_model.get.return_value = []
    mock_is.app.FaceAnalysis.return_value = mock_model

    with patch.dict(sys.modules, {"insightface": mock_is}):
        from app.ai.face_detector import FaceDetector

        # Reset singleton for test
        FaceDetector._instance = None

        detector = FaceDetector.get_instance()
        results = detector.detect(img_path)

    assert results == []
