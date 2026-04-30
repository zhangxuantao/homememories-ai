# backend/app/ai/search_index.py
import os
import json
import numpy as np
import faiss


class SearchIndex:
    """FAISS IVF+PQ index. Supports GPU build/search and disk persistence."""

    def __init__(self, dim: int = 512):
        self.dim = dim
        self.quantizer = faiss.IndexFlatIP(dim)
        self.index: faiss.Index | None = None
        self.id_map: list[int] = []
        self.nprobe = 64

    def build(self, embeddings: list[tuple[int, bytes]], nlist: int = 4096) -> None:
        if not embeddings:
            self.index = None
            self.id_map = []
            return

        self.id_map = [e[0] for e in embeddings]
        vectors = np.array([
            np.frombuffer(e[1], dtype=np.float32) for e in embeddings
        ])
        vectors = np.ascontiguousarray(vectors.astype(np.float32))

        d = self.dim
        n = len(vectors)

        # IVFPQ training requires at least 256 vectors (PQ nbits=8).
        # Fall back to flat index for small datasets.
        if n < 256:
            self.index = faiss.IndexFlatIP(d)
            self.index.add(vectors)
            return

        m = 64
        nlist = min(nlist, n)
        if nlist < 1:
            nlist = 1

        self.index = faiss.IndexIVFPQ(self.quantizer, d, nlist, m, 8)
        self.index.train(vectors)
        self.index.add(vectors)

        # Move to GPU if available
        try:
            res = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
        except Exception:
            pass  # stay on CPU if GPU not available

        self.index.nprobe = self.nprobe

    def search(self, query_vec: np.ndarray, k: int = 100) -> list[tuple[int, float]]:
        if self.index is None or len(self.id_map) == 0:
            return []

        query_vec = np.ascontiguousarray(query_vec.astype(np.float32))
        if query_vec.ndim == 1:
            query_vec = query_vec.reshape(1, -1)

        k = min(k, len(self.id_map))
        distances, indices = self.index.search(query_vec, k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.id_map):
                results.append((self.id_map[idx], float(distances[0][i])))
        return results

    def save(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        index_path = os.path.join(path, "index.faiss")
        map_path = os.path.join(path, "id_map.json")

        cpu_index = self.index
        try:
            if faiss.get_num_gpus() > 0:
                cpu_index = faiss.index_gpu_to_cpu(self.index)
        except Exception:
            pass

        faiss.write_index(cpu_index, index_path)
        with open(map_path, "w") as f:
            json.dump(self.id_map, f)

    def load(self, path: str) -> bool:
        index_path = os.path.join(path, "index.faiss")
        map_path = os.path.join(path, "id_map.json")

        if not os.path.exists(index_path) or not os.path.exists(map_path):
            return False

        cpu_index = faiss.read_index(index_path)
        if hasattr(cpu_index, "nprobe"):
            cpu_index.nprobe = self.nprobe

        # Move to GPU if available
        try:
            res = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
        except Exception:
            self.index = cpu_index

        with open(map_path, "r") as f:
            self.id_map = json.load(f)
        return True
