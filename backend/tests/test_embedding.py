# backend/tests/test_embedding.py
import numpy as np
import pytest
from unittest.mock import patch, MagicMock


def test_embedding_pipeline_singleton():
    """Pipeline should be a singleton - same instance on repeated calls."""
    from app.ai.embedding import EmbeddingPipeline

    with patch("app.ai.embedding.ChineseCLIPModel") as mock_model, \
         patch("app.ai.embedding.ChineseCLIPProcessor") as mock_processor:
        mock_model.from_pretrained.return_value = MagicMock()
        mock_processor.from_pretrained.return_value = MagicMock()

        # Reset singleton for test
        EmbeddingPipeline._instance = None

        p1 = EmbeddingPipeline.get_instance()
        p2 = EmbeddingPipeline.get_instance()
        assert p1 is p2


def test_embedding_pipeline_has_correct_dim():
    """Pipeline should expose dim=512."""
    from app.ai.embedding import EmbeddingPipeline

    with patch("app.ai.embedding.ChineseCLIPModel") as mock_model, \
         patch("app.ai.embedding.ChineseCLIPProcessor") as mock_processor:
        mock_model.from_pretrained.return_value = MagicMock()
        mock_processor.from_pretrained.return_value = MagicMock()

        EmbeddingPipeline._instance = None
        pipeline = EmbeddingPipeline.get_instance()
        assert pipeline.dim == 512


@patch("app.ai.embedding.ChineseCLIPProcessor")
@patch("app.ai.embedding.ChineseCLIPModel")
def test_embed_images_returns_normalized_vectors(mock_model_cls, mock_processor_cls):
    """embed_images should return (N, 512) float32 normalized vectors."""
    from app.ai.embedding import EmbeddingPipeline
    import numpy as np

    mock_model = MagicMock()
    mock_processor = MagicMock()
    mock_model_cls.from_pretrained.return_value = mock_model
    mock_processor_cls.from_pretrained.return_value = mock_processor

    # Simulate batch-size-aware output. batch_size=2 produces two calls: 2 imgs then 1 img.
    batch1 = np.random.randn(2, 512).astype(np.float32)
    batch1 = batch1 / np.linalg.norm(batch1, axis=1, keepdims=True)
    batch2 = np.random.randn(1, 512).astype(np.float32)
    batch2 = batch2 / np.linalg.norm(batch2, axis=1, keepdims=True)
    mock_model.get_image_features.side_effect = [batch1, batch2]

    EmbeddingPipeline._instance = None
    pipeline = EmbeddingPipeline.get_instance()

    # Bypass actual image loading for test
    with patch("PIL.Image.open"):
        result = pipeline.embed_images(["/fake/1.jpg", "/fake/2.jpg", "/fake/3.jpg"], batch_size=2)

    assert result.shape == (3, 512)
    assert result.dtype == np.float32
    norms = np.linalg.norm(result, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


@patch("app.ai.embedding.ChineseCLIPProcessor")
@patch("app.ai.embedding.ChineseCLIPModel")
def test_embed_text_returns_normalized_vectors(mock_model_cls, mock_processor_cls):
    """embed_text should return (N, 512) float32 normalized vectors."""
    from app.ai.embedding import EmbeddingPipeline
    import numpy as np

    mock_model = MagicMock()
    mock_processor = MagicMock()
    mock_model_cls.from_pretrained.return_value = mock_model
    mock_processor_cls.from_pretrained.return_value = mock_processor

    fake_embeddings = np.random.randn(2, 512).astype(np.float32)
    fake_embeddings = fake_embeddings / np.linalg.norm(fake_embeddings, axis=1, keepdims=True)
    mock_model.get_text_features.return_value = fake_embeddings

    EmbeddingPipeline._instance = None
    pipeline = EmbeddingPipeline.get_instance()

    result = pipeline.embed_text(["沙滩日落", "家庭聚会"])

    assert result.shape == (2, 512)
    assert result.dtype == np.float32
    norms = np.linalg.norm(result, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)
