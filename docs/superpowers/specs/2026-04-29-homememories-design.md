# HomeMemories AI — Design Specification

## Overview

A private, local-first family photo management system designed for a single user (the owner's wife). The system runs completely offline on a Windows 11 machine with all AI models running locally. Photos and data never leave the device.

**Target scale**: 100K photos + videos with instant browsing and sub-second search.

**Motto**: 让家庭回忆更智能 🏠

---

## Visual Design

### Style Direction

简约高级 (minimalist elegance) × 甜美可爱 (sweet charm) fusion. Clean white space with soft pink accents — refined but warm, never saccharine.

### Color Palette — 樱花雾霭 (Sakura Mist)

| Role | Hex | Usage |
|------|-----|-------|
| Primary pink | `#f0c6c6` | Active states, accent elements, selected highlights |
| Misty blue | `#e8eef5` | Cards, panels, secondary backgrounds |
| Warm gray | `#8b7e8a` | Primary text, icons |
| Light text | `#c4a0a0` | Secondary text, captions, dates |
| Pure white | `#ffffff` | Page backgrounds |
| Subtle pink bg | `#f7e8e8` | Card hover, subtle gradients |

### Design Language

- Generous white space and breathing room
- Rounded corners (12px cards, 8px buttons, 20px pills)
- Frosted glass cards (`backdrop-filter: blur` + semi-transparent backgrounds)
- Subtle framer-motion animations: fade-in on scroll, spring transitions for cards, page transitions
- Custom illustrated empty states (not generic icons)
- Sakura petal motif as a subtle decorative element on the home page

### Typography

System font stack, optimized for Chinese: `"PingFang SC", "Microsoft YaHei", "Noto Sans SC", system-ui, -apple-system, sans-serif`

---

## Technical Architecture

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python FastAPI | REST API, async I/O |
| Database | SQLite | Metadata, face clusters, events |
| Vector Search | FAISS-GPU (IVF index) | Semantic image search |
| AI Models | CLIP ViT-B/32, InsightFace | Embeddings, face detection |
| Image Processing | Pillow, OpenCV | Thumbnails, video frames, quality checks |
| Frontend | React 18 + TypeScript | UI framework |
| Styling | Tailwind CSS 3 | Utility-first styling |
| Animation | framer-motion | Page transitions, micro-interactions |
| Virtual Scroll | @tanstack/virtual | Large list performance |
| Build | Vite | Fast dev server and bundling |
| PWA | vite-plugin-pwa | Installable, offline-ready |

### Architecture Diagram

```
┌──────────────────────────────────────────────────┐
│                   Browser (React)                 │
│  ┌──────┐ ┌────────┐ ┌──────┐ ┌──────┐ ┌──────┐ │
│  │ Home │ │Timeline│ │Search│ │People│ │Settings│ │
│  └──────┘ └────────┘ └──────┘ └──────┘ └──────┘ │
│         ▲ REST API (JSON) + Static Files         │
├─────────┴───────────────────────────────────────┤
│                FastAPI Server (:8501)             │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ /api/*   │ │ /media/* │ │ /static/thumbs/* │ │
│  │ REST     │ │ raw imgs │ │ pre-generated    │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Scanner  │ │ AI Pipeline│ │ Vector Index   │ │
│  │ EXIF     │ │ CLIP+Face │ │ FAISS IVF       │ │
│  └──────────┘ └──────────┘ └──────────────────┘ │
│         ▲                                        │
│    ┌────┴────┐                                   │
│    │ SQLite  │  metadata.db                      │
│    └─────────┘                                   │
└──────────────────────────────────────────────────┘
```

---

## Frontend Design

### Navigation

**Mobile (PWA)**:
- Bottom bar: 3 core tabs — 首页 (home), 时间线 (timeline), 搜索 (search)
- Hamburger/edge-swipe drawer for: 人物 (people), 设置 (settings)
- Fingerprint/gesture-friendly: tabs at bottom, drawer from right edge

**Desktop**:
- Collapsible left icon rail (icons only when collapsed, icons + labels when expanded)
- Same structure as mobile for consistency

### Page Designs

#### 1. Home Page — 卡片流 (Card Stream)

Vertical scroll of memory cards in order:
1. **去年今天** (On This Day Last Year) — largest card, hero image from the same date past years, swipe to see more years
2. **随机回忆** (Random Memories) — 2-4 random photo clusters from different time periods, each as a card with soft gradient placeholder
3. **最近添加** (Recently Added) — small horizontal strip of newest photos

Each card is a frosted glass panel with rounded corners, a subtle drop shadow, and a framer-motion fade-slide-up entrance animation. Cards have a sakura-colored left border accent.

Empty state: a gentle illustration of an empty photo frame with text "还没有照片哦，去设置页扫描吧~"

#### 2. Timeline — 事件分组横向滑动 (Event Groups)

Content structure:
- **Header**: horizontal year selector pills (2026, 2025, 2024...)
- **Body**: events grouped by date+location proximity, each event displayed as:
  - Event title (e.g., "2025年5月 · 杭州西湖")
  - Horizontal scrollable strip of thumbnails (70×70px, rounded-8px)
  - Tapping an event opens its detail grid view
- **Performance**: virtualized year list; events lazy-loaded; thumbnails lazy-loaded via Intersection Observer

Empty state: skeleton cards with shimmer animation during loading.

#### 3. Search Page

Two modes:
- **文字搜索**: large search bar at top, recent searches as pill tags below, results grid below
- **图片搜索**: upload zone (drag & drop on desktop, tap to select on mobile), results ranked by similarity

Results displayed as a responsive grid (3 cols mobile, 5 cols desktop) with infinite scroll. Each result card: thumbnail + date overlay.

#### 4. People Page

Grid of face cluster cards. Each card shows:
- Representative face thumbnail (centered, rounded)
- Auto-generated label (e.g., "人物 1", editable)
- Photo count badge

Clicking opens a person detail page: timeline of all photos containing that face.

#### 5. Photo Detail (Lightbox)

Full-screen photo viewer:
- Swipe left/right (mobile) or arrow keys (desktop) to navigate
- Bottom info bar: date, location (if available), related people
- Action buttons: download, favorite (future), view similar
- Video playback with basic controls

#### 6. Settings Page

Administrative tools organized in sections:
- **媒体管理**: scan directory, scan status/progress, last scan time
- **AI 处理**: generate embeddings, face detection, progress indicators
- **清理工具**: blur detection results, duplicate detection results (secondary priority)
- **系统信息**: database size, index size, GPU status

### Performance Strategy for 100K Photos

| Concern | Solution |
|---------|----------|
| Timeline grid rendering | @tanstack/virtual, render only ~50 visible items |
| Thumbnail loading | Pre-generated 300px thumbnails during scan, served as static files |
| Image lazy loading | Intersection Observer, load 200px above viewport |
| API pagination | Cursor-based, 100 items per page |
| Search results | FAISS IVF index, <50ms retrieval, paginated response |
| Bundle size | Route-based code splitting, lazy-load pages |
| PWA caching | Service worker caches thumbnails and static assets |

---

## Backend Design

### Database Schema (SQLite)

```sql
-- Core media table
CREATE TABLE media (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    media_type TEXT NOT NULL,  -- 'image' | 'video'
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    date_taken TEXT,           -- ISO 8601 from EXIF
    date_added TEXT NOT NULL,  -- scan timestamp
    thumbnail_path TEXT,       -- relative path to thumbnail
    duration REAL,             -- video duration in seconds
    is_blurry BOOLEAN DEFAULT 0,
    blur_score REAL,
    dhash TEXT,                -- perceptual hash for dedup
    checksum TEXT,             -- SHA-256 of file content
    embedding_id INTEGER       -- FK to embeddings table
);

-- CLIP embeddings
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY,
    media_id INTEGER UNIQUE,
    vector BLOB NOT NULL,
    model_version TEXT,
    created_at TEXT
);

-- Face detections
CREATE TABLE faces (
    id INTEGER PRIMARY KEY,
    media_id INTEGER,
    cluster_id INTEGER,
    bbox TEXT,                 -- JSON: [x,y,w,h]
    embedding BLOB,
    thumbnail_path TEXT
);

-- Face clusters
CREATE TABLE face_clusters (
    id INTEGER PRIMARY KEY,
    label TEXT,
    cover_face_id INTEGER,
    photo_count INTEGER DEFAULT 0
);

-- Events (auto-grouped by time+location)
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    title TEXT,
    start_date TEXT,
    end_date TEXT,
    cover_media_id INTEGER,
    media_count INTEGER DEFAULT 0,
    location TEXT
);

CREATE TABLE event_media (
    event_id INTEGER,
    media_id INTEGER,
    sort_order INTEGER
);

-- Search cache
CREATE TABLE search_cache (
    id INTEGER PRIMARY KEY,
    query_hash TEXT UNIQUE,
    query_text TEXT,
    result_ids TEXT,  -- JSON array of media IDs
    created_at TEXT
);

CREATE INDEX idx_media_date ON media(date_taken);
CREATE INDEX idx_media_type ON media(media_type);
CREATE INDEX idx_media_checksum ON media(checksum);
CREATE INDEX idx_media_dhash ON media(dhash);
CREATE INDEX idx_faces_cluster ON faces(cluster_id);
CREATE INDEX idx_faces_media ON faces(media_id);
CREATE INDEX idx_event_media_event ON event_media(event_id);
```

### API Endpoints

```
# Timeline
GET  /api/timeline/years                          → [2026, 2025, ...]
GET  /api/timeline/events?year=2025&month=5       → [{event}, ...]
GET  /api/timeline/event/:id/media?cursor=&limit= → {media[], next_cursor}

# Media
GET  /api/media/:id                               → {media detail}
GET  /api/media/:id/similar?limit=20              → [{similar media}, ...]
GET  /api/media/random?count=4&exclude=           → [{media}, ...]
GET  /api/media/on-this-day?month=4&day=29        → [{media by year}, ...]
DELETE /api/media/:id                             → delete (soft)

# Search
POST /api/search/text  {query, limit, cursor}     → {results[], next_cursor}
POST /api/search/image {image_file}               → {results[]}

# Faces
GET  /api/faces/clusters                          → [{cluster}, ...]
GET  /api/faces/cluster/:id/media?cursor=&limit=  → {media[], next_cursor}
PATCH /api/faces/cluster/:id  {label}             → update label

# Admin
POST /api/admin/scan                              → {job_id}
GET  /api/admin/scan/status                       → {progress, last_scan}
POST /api/admin/embeddings/generate               → {job_id}
POST /api/admin/faces/detect                      → {job_id}
POST /api/admin/faces/cluster                     → {job_id}
GET  /api/admin/job/:id/status                    → {status, progress}
GET  /api/admin/stats                             → {db_size, media_count, ...}
GET  /api/admin/cleanup/blurry?threshold=&limit=  → [{media}, ...]
GET  /api/admin/cleanup/duplicates                → [[media, media], ...]

# Static
GET  /media/thumbs/<path>                         → pre-generated thumbnail
GET  /media/original/<path>                       → full-resolution image
```

---

## PWA Configuration

- App name: "家庭记忆"
- Short name: "记忆"
- Icon: sakura-themed app icon (192px, 512px)
- Theme color: `#fafbfc`
- Background color: `#ffffff`
- Display: standalone
- Scope: `/`

---

## Development Phases

### Phase 1: Backend Core
- Project scaffolding (FastAPI + SQLite)
- Media scanner with EXIF extraction
- Thumbnail generation pipeline
- Basic REST API (timeline, media CRUD)
- Static file serving

### Phase 2: AI Pipeline
- CLIP embedding generation
- FAISS IVF index builder
- Text and image search API
- InsightFace detection + clustering
- Quality checker (blur + duplicate)

### Phase 3: Frontend
- React + Tailwind + Vite project setup
- Theme system (Sakura Mist tokens)
- Shared components (card, skeleton, lazy-image, virtual-grid)
- Home page (card stream)
- Timeline page (event groups + virtual scroll)
- Search page (text + image upload)
- People page (face clusters)
- Photo detail lightbox

### Phase 4: Polish
- framer-motion page transitions and micro-interactions
- PWA manifest and service worker
- Mobile responsive pass
- Empty states and error states
- Loading skeletons

### Phase 5: Settings & Admin
- Settings page with scan/index/face controls
- Progress indicators for long-running jobs
- Cleanup tools UI
- System stats dashboard
