# backend/tests/test_search_index.py
import numpy as np
import os
import json
import pytest


def test_search_index_build_and_search(tmp_path):
    """Build index with synthetic vectors, search returns correct ids and scores."""
    from app.ai.search_index import SearchIndex

    # Create 100 synthetic 512-dim normalized vectors
    np.random.seed(42)
    vectors = np.random.randn(100, 512).astype(np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / (norms + 1e-8)

    embeddings = [(i + 1, vectors[i].tobytes()) for i in range(100)]

    index = SearchIndex(dim=512)
    index.build(embeddings, nlist=16)  # small nlist for test

    # Search with a known vector
    query = vectors[0].copy().reshape(1, -1)
    results = index.search(query, k=5)

    assert len(results) == 5
    # First result should be the query vector itself (media_id=1)
    assert results[0][0] == 1
    assert results[0][1] > 0.99  # near-perfect cosine similarity

    # All scores should be between -1 and 1
    for _, score in results:
        assert -1.0 <= score <= 1.0


def test_search_index_save_and_load(tmp_path):
    """Index should survive save/load roundtrip."""
    from app.ai.search_index import SearchIndex

    np.random.seed(42)
    vectors = np.random.randn(50, 512).astype(np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / (norms + 1e-8)
    embeddings = [(i + 1, vectors[i].tobytes()) for i in range(50)]

    index = SearchIndex(dim=512)
    index.build(embeddings, nlist=8)
    index.save(str(tmp_path))

    # Verify files exist
    assert os.path.exists(os.path.join(tmp_path, "index.faiss"))
    assert os.path.exists(os.path.join(tmp_path, "id_map.json"))

    # Load into new index
    index2 = SearchIndex(dim=512)
    assert index2.load(str(tmp_path)) is True

    # Search should return same results
    query = vectors[10].copy().reshape(1, -1)
    results1 = index.search(query, k=5)
    results2 = index2.search(query, k=5)
    for r1, r2 in zip(results1, results2):
        assert r1[0] == r2[0]
        assert abs(r1[1] - r2[1]) < 1e-5


def test_search_index_empty_build():
    """Building with empty data should create a valid but empty index."""
    from app.ai.search_index import SearchIndex

    index = SearchIndex(dim=512)
    index.build([], nlist=8)

    query = np.random.randn(1, 512).astype(np.float32)
    results = index.search(query, k=5)
    assert results == []


def test_search_index_load_nonexistent():
    """Loading from nonexistent path returns False."""
    from app.ai.search_index import SearchIndex

    index = SearchIndex(dim=512)
    assert index.load("/nonexistent/path") is False


def test_search_index_search_returns_requested_k():
    """Search should return exactly k results when enough vectors exist."""
    from app.ai.search_index import SearchIndex

    np.random.seed(42)
    vectors = np.random.randn(30, 512).astype(np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / (norms + 1e-8)
    embeddings = [(i + 1, vectors[i].tobytes()) for i in range(30)]

    index = SearchIndex(dim=512)
    index.build(embeddings, nlist=4)
    index.nprobe = 4  # search all clusters

    query = np.random.randn(1, 512).astype(np.float32)
    results = index.search(query, k=10)
    assert len(results) == 10
