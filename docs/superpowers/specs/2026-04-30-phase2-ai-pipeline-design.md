# Phase 2: AI Pipeline — Design Specification

## Overview

Build the AI pipeline on top of the Phase 1 backend core. This phase adds CLIP embedding generation, FAISS GPU vector search, text/image search APIs, face detection with embeddings, and quality checking (blur + duplicate detection). All AI models run locally on the NVIDIA RTX 5080 GPU.

**Target:** 100K photos indexed for sub-second semantic search. Face data prepared for Phase 3 clustering.

---

## Hardware Target

- GPU: NVIDIA RTX 5080 16GB VRAM
- OS: Windows 11
- Python: 3.11, CUDA 12.x via PyTorch

---

## Architecture

```
backend/app/
├── ai/                          # NEW: AI model wrappers
│   ├── __init__.py
│   ├── embedding.py             # Chinese CLIP model + batch inference
│   ├── search_index.py          # FAISS IVF+PQ index builder/search
│   ├── face_detector.py         # InsightFace buffalo_l detection + embedding
│   └── quality.py               # Laplacian blur + dhash duplicate detection
├── services/
│   ├── __init__.py
│   ├── media_service.py         # (existing)
│   ├── scan_service.py          # (existing)
│   ├── search_service.py        # NEW: search orchestration
│   ├── face_service.py          # NEW: face detection job orchestration
│   └── quality_service.py       # NEW: blur/duplicate check orchestration
└── routers/
    ├── __init__.py
    ├── timeline.py              # (existing)
    ├── media.py                 # (existing)
    ├── admin.py                 # (extend: embeddings, face, cleanup endpoints)
    ├── search.py                # NEW: POST /api/search/text, /api/search/image
    └── faces.py                 # NEW: GET /api/faces/clusters (Phase 3 ready)
```

**Pattern:** Phase 1 three-layer structure preserved: `routers` → `services` → `ai` (model layer, analogous to `scanner/`).

---

## Technology Selection

| Capability | Library | Model | Why |
|------------|---------|-------|-----|
| Image/Text Embedding | transformers + torch (CUDA) | OFA-Sys/chinese-clip-vit-base-patch16 | Chinese-optimized CLIP, 512-dim, ~400MB VRAM |
| Vector Search | faiss-gpu | IVF4096 + PQ64 (IP) | 6.4MB per 100K vectors, <50ms search at 95%+ recall |
| Face Detection + Embedding | insightface | buffalo_l | Detect + 512-dim arcface embedding in one pass |
| Blur Detection | opencv-python | Laplacian variance | Simple, fast, no extra model |
| Duplicate Detection | stdlib | dhash + Hamming distance | dhash already stored in Phase 1 |

GPU memory budget (RTX 5080 16GB):
- Chinese CLIP: ~400MB
- FAISS IVF index: ~80MB (100K vectors, IVF+PQ)
- InsightFace buffalo_l: ~200MB
- Misc overhead: ~500MB
- **Total: ~1.2GB** — well within 16GB

---

## Module Designs

### 1. Embedding Pipeline (`ai/embedding.py`)

Global model singleton, loaded once at first use, stays resident on GPU.

```python
class EmbeddingPipeline:
    model: ChineseCLIPModel      # GPU-resident
    processor: ChineseCLIPProcessor
    dim: int = 512

    @classmethod
    def get_instance(cls) -> "EmbeddingPipeline":
        """Lazy singleton, loads model on first call."""

    def embed_images(self, image_paths: list[str], batch_size: int = 32) -> np.ndarray:
        """Batch image embedding. Returns (N, 512) float32 normalized vectors."""

    def embed_text(self, texts: list[str]) -> np.ndarray:
        """Text embedding for search queries. Returns (N, 512) float32 normalized."""
```

**Performance:** ~300-400 images/sec batch inference on RTX 5080. 100K images ≈ 5 minutes.

**Persistence:** Vectors stored as BLOB in `embeddings` table (Phase 1 schema), `model_version` field tracks which CLIP model was used.

**Resumability:** `generate_embeddings()` scans `media` for rows where `embedding_id IS NULL`, skips already-processed images.

### 2. FAISS Search Index (`ai/search_index.py`)

GPU-accelerated IVF+PQ index with disk persistence.

```python
class SearchIndex:
    dim: int = 512
    quantizer: faiss.IndexFlatIP     # inner product = cosine similarity on normalized vectors
    index: faiss.IndexIVFPQ | None
    id_map: list[int]                 # FAISS internal id → media_id

    def build(self, embeddings: list[tuple[int, bytes]], nlist: int = 4096) -> None:
        """Load vectors from DB, train IVF clusters, build GPU index."""

    def search(self, query_vec: np.ndarray, k: int = 100) -> list[tuple[int, float]]:
        """Search index. Returns [(media_id, similarity_score), ...] sorted descending."""

    def load(self, path: str) -> bool:
        """Restore index + id_map from disk."""

    def save(self, path: str) -> None:
        """Persist index + id_map to data/faiss/."""
```

**Index parameters:**
- nlist = 4096 (IVF clusters) — ~25 vectors per cluster at 100K scale
- M = 64 (PQ sub-vectors) — 512/64 = 8 bytes per sub-vector
- nbits = 8 — each sub-vector encoded as 1 byte
- Search: nprobe = 64 — probes 1.5% of clusters, recall >95%
- Storage: `data/faiss/index.faiss` (binary) + `data/faiss/id_map.json`

**Rebuild trigger:** Index rebuilt automatically after embedding generation completes. Manual rebuild via `POST /api/admin/embeddings/generate`.

### 3. Search Service + Router

**Service (`services/search_service.py`):**

```python
def search_by_text(query: str, limit: int = 20, cursor: int = 0) -> dict:
    """Text → CLIP text embedding → FAISS search → paginated results."""

def search_by_image(file_bytes: bytes, limit: int = 20) -> list[MediaItem]:
    """Uploaded image → CLIP image embedding → FAISS search → top results."""

def rebuild_index() -> str:
    """Rebuild FAISS index from all embeddings in DB. Returns job_id."""

def generate_embeddings() -> str:
    """Generate embeddings for all media without one. Returns job_id."""
```

**Router (`routers/search.py`):**

```
POST /api/search/text    { query, limit=20, cursor=0 }
  → { results: [MediaItem], next_cursor: int | null, total: int }

POST /api/search/image   multipart/form-data: image_file
  → { results: [MediaItem] }
```

**Search cache:** `search_cache` table (Phase 1 schema) used for text search caching. `query_hash = sha256(query.lower().strip())`, 1-hour TTL.

### 4. Quality Checker

**AI layer (`ai/quality.py`):**

```python
def detect_blur(image_path: str) -> tuple[bool, float]:
    """Grayscale → cv2.Laplacian → variance. is_blurry = variance < 100."""

def find_duplicates(db_path: str, hamming_threshold: int = 8) -> list[tuple[int, int]]:
    """Load all dhash values from media, XOR bit count, return duplicate pairs."""
```

**Service (`services/quality_service.py`):**

```python
def run_blur_check(threshold: float = 100.0) -> str:
    """Background job: scan all images, update is_blurry + blur_score. Returns job_id."""

def run_duplicate_check() -> str:
    """Background job: find duplicate pairs. Returns job_id with results."""

def get_blurry_media(threshold: float, limit: int) -> list[MediaItem]:
    """Query media WHERE is_blurry=1 OR blur_score < threshold."""

def get_duplicate_pairs() -> list[tuple[MediaItem, MediaItem]]:
    """Return cached duplicate pairs."""
```

**Extended admin endpoints (add to `routers/admin.py`):**

```
POST /api/admin/cleanup/blurry/check     → { job_id }   # Start blur scan
POST /api/admin/cleanup/duplicates/check  → { job_id }   # Start duplicate scan
GET  /api/admin/cleanup/blurry?threshold=&limit=  → [{MediaItem}, ...]
GET  /api/admin/cleanup/duplicates          → [[MediaItem, MediaItem], ...]
DELETE /api/admin/cleanup/blurry  { ids: [1,2,3] }   → soft delete
```

### 5. Face Detection + Embedding

**AI layer (`ai/face_detector.py`):**

```python
class FaceDetector:
    model: insightface.app.FaceAnalysis  # GPU-resident, buffalo_l

    @classmethod
    def get_instance(cls) -> "FaceDetector":
        """Lazy singleton. model.prepare(ctx_id=0) for GPU."""

    def detect(self, image_path: str) -> list[dict]:
        """Detect all faces in image. Returns [
            {
                "bbox": [x, y, w, h],
                "embedding": np.ndarray(512),
                "thumb_path": "data/thumbs/faces/{face_id}.jpg"
            },
            ...
        ]"""
```

**Service (`services/face_service.py`):**

```python
def start_face_detection() -> str:
    """Background job: scan all images, detect faces, save to faces table.
    Resumable: skips media that already have face records.
    Returns job_id."""

def get_face_clusters(db_path: str) -> list[dict]:
    """Placeholder for Phase 3. Returns empty list or raw face groups."""
```

**Face thumbnails:** Cropped from original image using bbox, resized to 160x160, stored at `data/thumbs/faces/{face_id}.jpg`.

**Router (`routers/faces.py`):**

```
GET  /api/faces/clusters              → []   # Phase 3 implements clustering
GET  /api/faces/cluster/:id/media     → { items, next_cursor }  # Phase 3
PATCH /api/faces/cluster/:id { label } → Phase 3
```

**Admin endpoints (add to `routers/admin.py`):**

```
POST /api/admin/faces/detect           → { job_id }
```

### 6. Job Tracking

Reuse Phase 1 `ScanJobTracker` pattern for AI jobs. Each AI job (embeddings, blur check, duplicate check, face detection) gets a UUID, status updates, and progress tracking.

Extend `ScanJobTracker` → rename to `JobTracker` and move to shared utility, or create an AI-specific tracker following the same singleton+dict pattern.

---

## Data Flow

### Embedding Generation → Search
```
POST /api/admin/embeddings/generate
  → service: generate_embeddings()
    → JobTracker.create() → job_id
    → Thread: for each media WHERE embedding_id IS NULL:
        → PIL open image
        → EmbeddingPipeline.embed_images(batch)
        → INSERT INTO embeddings (media_id, vector, model_version, created_at)
        → UPDATE media SET embedding_id = embeddings.id
    → service: rebuild_index()
      → SELECT * FROM embeddings JOIN media
      → numpy array from BLOBs
      → SearchIndex.build(vectors)
      → SearchIndex.save("data/faiss/")
    → JobTracker.update(job_id, status="completed")
```

### Text Search
```
POST /api/search/text { query: "沙滩日落" }
  → hash(query) lookup in search_cache
  → (miss) EmbeddingPipeline.embed_text(["沙滩日落"])
  → SearchIndex.search(query_vec, k=100)
  → map FAISS ids → media_ids via id_map
  → SELECT * FROM media WHERE id IN (...)
  → cache result, return paginated
```

### Image Search
```
POST /api/search/image { file }
  → PIL open uploaded bytes
  → EmbeddingPipeline.embed_images([temp_path])
  → SearchIndex.search(query_vec, k=50)
  → return top results
```

### Face Detection
```
POST /api/admin/faces/detect
  → service: start_face_detection()
    → JobTracker.create() → job_id
    → Thread: for each image WHERE media_type='image':
        → skip if faces exist for this media_id
        → FaceDetector.detect(image_path)
        → for each detected face:
            → crop + save thumb to data/thumbs/faces/
            → INSERT INTO faces (media_id, bbox, embedding, thumbnail_path)
    → JobTracker.update(job_id, status="completed")
```

---

## Dependencies (added to requirements.txt)

```
# AI Pipeline (Phase 2)
torch>=2.5.0
transformers>=4.46.0
faiss-gpu>=1.9.0
insightface>=0.7.3
opencv-python>=4.10.0
onnxruntime-gpu>=1.19.0
```

---

## Build Order

1. **CLIP Embedding Pipeline** — model loading, batch inference, embedding generation job
2. **FAISS Index** — IVF build, GPU search, disk persistence
3. **Search API** — text search, image search, search cache, router
4. **Quality Checker** — blur detection, duplicate detection, admin endpoints
5. **Face Detection** — InsightFace integration, face detection job, faces router stub

---

## API Summary

| Method | Path | Phase | Description |
|--------|------|-------|-------------|
| POST | /api/search/text | 2 | Semantic text search |
| POST | /api/search/image | 2 | Reverse image search |
| POST | /api/admin/embeddings/generate | 2 | Generate CLIP embeddings |
| POST | /api/admin/cleanup/blurry/check | 2 | Run blur detection |
| POST | /api/admin/cleanup/duplicates/check | 2 | Run duplicate detection |
| GET | /api/admin/cleanup/blurry | 2 | List blurry media |
| GET | /api/admin/cleanup/duplicates | 2 | List duplicate pairs |
| DELETE | /api/admin/cleanup/blurry | 2 | Delete blurry media |
| POST | /api/admin/faces/detect | 2 | Run face detection |
| GET | /api/faces/clusters | 3 | List face clusters (stub) |
| GET | /api/faces/cluster/:id/media | 3 | Cluster media (stub) |
| PATCH | /api/faces/cluster/:id | 3 | Update cluster label (stub) |
