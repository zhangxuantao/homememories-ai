# HomeMemories AI — Phase 3 Frontend Design Specification

## Overview

Phase 3 builds the React frontend for HomeMemories AI, consuming the Phase 1-2 backend APIs (FastAPI at :8501). The frontend is a SPA with 6 pages, responsive navigation, and the Sakura Mist visual design defined in the original spec.

**Target**: Windows 11 desktop (primary) + mobile PWA (secondary). All APIs are local, no internet dependency after initial install.

## Technical Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | React | 18.x |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 3.x |
| Animation | framer-motion | 11.x |
| Virtual Scroll | @tanstack/react-virtual | 3.x |
| Routing | react-router-dom | 6.x |
| Build | Vite | 6.x |
| PWA | vite-plugin-pwa | 0.x |

No state management library — SWR-pattern custom hooks (see Data Layer section) are sufficient for this application's data fetching needs.

## Project Structure

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── public/
│   └── favicon.svg
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css                  (Tailwind directives + Sakura Mist custom properties)
    ├── api/
    │   └── client.ts              (fetch wrapper, base URL :8501, typed functions)
    ├── hooks/
    │   ├── useMedia.ts            (random, on-this-day, by-id, delete)
    │   ├── useTimeline.ts         (years, events, event-media)
    │   ├── useSearch.ts           (text search, image search)
    │   └── useAdmin.ts            (stats, jobs, scan, embeddings, cleanup, faces)
    ├── pages/
    │   ├── HomePage.tsx
    │   ├── TimelinePage.tsx
    │   ├── SearchPage.tsx
    │   ├── PeoplePage.tsx
    │   ├── PhotoDetail.tsx
    │   └── SettingsPage.tsx
    ├── components/
    │   ├── layout/
    │   │   ├── MobileNav.tsx      (bottom bar, 5 tabs)
    │   │   └── DesktopRail.tsx    (collapsible left icon rail)
    │   ├── cards/
    │   │   ├── MemoryCard.tsx     (frosted glass, sakura accent, fade-up)
    │   │   └── FaceCard.tsx       (round avatar, label, count badge)
    │   ├── gallery/
    │   │   ├── PhotoGrid.tsx      (responsive grid, 3-col mobile / 5-col desktop)
    │   │   └── Lightbox.tsx       (full-screen overlay, swipe/arrow nav)
    │   ├── timeline/
    │   │   ├── YearPills.tsx      (horizontal scrollable year selector)
    │   │   └── EventStrip.tsx     (horizontal thumbnail strip per event)
    │   └── ui/
    │       ├── SearchBar.tsx
    │       ├── ImageUploader.tsx  (drag-drop on desktop, tap on mobile)
    │       └── Skeleton.tsx       (shimmer loading placeholder)
    └── utils/
        └── format.ts              (date formatting, file size, etc.)
```

## Route Design

All routes lazy-loaded via `React.lazy()` for code splitting.

| Route | Page | Description |
|-------|------|-------------|
| `/` | HomePage | 卡片流：去年今天 + 随机回忆 + 最近添加 |
| `/timeline` | TimelinePage | 年份选择器 + 事件分组横向滑动 |
| `/search` | SearchPage | 文字搜索 + 图片搜索双模式 |
| `/people` | PeoplePage | 人脸簇网格（无数据时显示空状态） |
| `/photo/:id` | PhotoDetail | 全屏灯箱，左右滑动/键盘导航 |
| `/settings` | SettingsPage | 管理工具：扫描、AI处理、清理、系统信息 |

## Navigation

**Mobile** (width < 768px):
- Bottom bar, 5 tabs: 首页, 时间线, 搜索, 人物, 设置
- Active tab highlighted in primary pink (`#f0c6c6`)
- Frosted glass background (`backdrop-filter: blur(12px)`)
- Fixed position, 56px height

**Desktop** (width ≥ 768px):
- Left icon rail, collapsible
- Collapsed: 56px wide, icons only
- Expanded: 200px wide, icons + labels
- Active item highlighted in primary pink
- Content area fills remaining width

Navigation component detects viewport width via CSS media query + `useMediaQuery` hook. Both MobileNav and DesktopRail render in the DOM; visibility toggled by Tailwind `md:hidden` / `hidden md:flex`.

## Visual Design

### Color Palette — 樱花雾霭 (Sakura Mist)

Applied as CSS custom properties in `index.css`:

| Role | Hex | CSS Variable | Usage |
|------|-----|-------------|-------|
| Primary pink | `#f0c6c6` | `--color-primary` | Active states, accents, selected |
| Misty blue | `#e8eef5` | `--color-misty` | Cards, panels, secondary backgrounds |
| Warm gray | `#8b7e8a` | `--color-text` | Primary text, icons |
| Light text | `#c4a0a0` | `--color-text-light` | Secondary text, captions, dates |
| Pure white | `#ffffff` | `--color-bg` | Page backgrounds |
| Subtle pink | `#f7e8e8` | `--color-subtle` | Card hover, gradients |

### Typography

Font stack: `"PingFang SC", "Microsoft YaHei", "Noto Sans SC", system-ui, -apple-system, sans-serif`

| Level | Size | Weight | Usage |
|-------|------|--------|-------|
| Page title | 24px | 700 | Page headings |
| Section title | 16px | 600 | Card titles, section headers |
| Body | 14px | 400 | Body text |
| Caption | 12px | 400 | Dates, secondary info |

### Design Tokens

- Card border-radius: 12px
- Button border-radius: 8px
- Pill border-radius: 20px
- Cards: frosted glass (`backdrop-filter: blur(16px)`, semi-transparent white bg, subtle shadow)
- Memory cards: 3px sakura-colored left border accent

### Animation

framer-motion for all animations:
- Page transitions: fade + slight slide-up (200ms)
- Card entrance: stagger children, fade-slide-up (150ms per card, 50ms stagger)
- Navigation transitions: spring animation on active indicator
- Loading skeletons: shimmer animation via Tailwind `animate-pulse`

## Page Designs

### 1. Home Page (`/`)

Three sections, vertical scroll:
1. **去年今天** (On This Day) — largest card at top. Hero image from same-date past years. Shows date + location if available. Swipe/click to cycle through years.
2. **随机回忆** (Random Memories) — 2-4 cards from different time periods. Each card: thumbnail area + date + photo count.
3. **最近添加** (Recently Added) — horizontal scrollable strip of small thumbnails (newest ~10 photos).

API calls: `GET /api/media/on-this-day`, `GET /api/media/random`, `GET /api/media/random` (with exclude).

Empty state: centered illustration + "还没有照片哦，去设置页扫描吧~" text.

### 2. Timeline Page (`/timeline`)

- **Header**: horizontal scrollable YearPills (rounded pill buttons for each year). Selected year highlighted in primary pink.
- **Body**: virtualized list of events for selected year. Each event group: title (e.g., "2025年5月 · 杭州西湖"), horizontal scrollable thumbnail strip (70×70px, rounded 8px), photo count badge.
- Clicking an event navigates to a detail view (inline or modal) showing all photos in a grid.

API calls: `GET /api/timeline/years`, `GET /api/timeline/events?year=`, `GET /api/timeline/event/{id}/media`.

Performance: `@tanstack/virtual` for the event list. Intersection Observer for thumbnail lazy loading (load when 200px from viewport).

### 3. Search Page (`/search`)

Two modes, toggled by tabs at top:

**文字搜索** (Text Search):
- Large SearchBar with magnifying glass icon
- Below: recent search pill tags (stored in localStorage)
- Results: PhotoGrid with infinite scroll, sorted by similarity
- Each result card: thumbnail + date overlay

**图片搜索** (Image Search):
- Upload zone: dashed border, "拖拽图片到此处或点击上传" text
- On file select: preview thumbnail, then POST to API
- Results: same PhotoGrid, ranked by similarity

API calls: `POST /api/search/text`, `POST /api/search/image` (multipart).

### 4. People Page (`/people`)

- Grid of FaceCard components (3 cols mobile, 5 cols desktop)
- Each card: round face thumbnail (64px), label ("人物 1"), photo count badge
- Clicking opens person detail: horizontal scrollable timeline of photos containing that face
- Empty state: "还没有检测到人物哦~" with illustration (face detection not yet run)

API calls: `GET /api/faces/clusters`, `GET /api/faces/cluster/{id}/media`.

### 5. Photo Detail — Lightbox (`/photo/:id`)

- Full-screen overlay with dark backdrop
- Main image: fills available space, object-contain
- Navigation: swipe left/right (touch) or arrow keys (keyboard)
- Bottom info bar: date, location, related faces (if available)
- Action buttons: download, close
- Preloads adjacent photos (id ± 1) for instant navigation

API calls: `GET /api/media/{id}`.

### 6. Settings Page (`/settings`)

Four sections in a vertical stack:

1. **媒体管理** (Media Management):
   - "扫描目录" button → triggers `POST /api/admin/scan`
   - Scan status display (polling `GET /api/admin/scan/status?job_id=`)
   - Last scan time from stats

2. **AI 处理** (AI Processing):
   - "生成 Embeddings" button → `POST /api/admin/embeddings/generate`
   - "人脸检测" button → `POST /api/admin/faces/detect`
   - Job progress indicators (polling `GET /api/admin/job/{id}/status`)

3. **清理工具** (Cleanup):
   - Blur detection: "检测模糊照片" → `POST /api/admin/cleanup/blurry/check`
   - Duplicate detection: "检测重复照片" → `POST /api/admin/cleanup/duplicates/check`
   - Results lists with thumbnails + delete actions

4. **系统信息** (System Info):
   - Database size, index size, GPU status
   - `GET /api/admin/stats`

Job status polling: `useAdmin` hook provides `useJobStatus(jobId, pollInterval=2000)` that polls until job completes.

## Data Layer

### API Client (`api/client.ts`)

Singleton `ApiClient` class:
- `baseUrl`: `http://localhost:8501` (configurable via env var in Vite)
- `get<T>(path, params?)`: typed GET with query string
- `post<T>(path, body?)`: typed POST with JSON body
- `upload<T>(path, file)`: multipart file upload

Error handling: throws typed errors on non-2xx responses. Hooks catch and expose via `error` state.

### Custom Hooks (SWR Pattern)

Each hook returns `{ data, error, loading, mutate }`:

```typescript
// useMedia.ts
useRandomMedia(count: number)
useOnThisDay(month: number, day: number)
useMediaById(id: number)

// useTimeline.ts
useTimelineYears()
useEvents(year: number, month?: number)
useEventMedia(eventId: number, cursor?: string)

// useSearch.ts
useTextSearch(query: string, cursor?: string)
useImageSearch(file: File | null)

// useAdmin.ts
useAdminStats()
useJobStatus(jobId: string, pollInterval?: number)
// + mutation functions: startScan, generateEmbeddings, startFaceDetection,
//   startBlurCheck, startDuplicateCheck, deleteBlurryMedia
```

Hooks use `useEffect` + `useState` internally — no external dependency. Cursor pagination: hooks accumulate pages in an internal array, exposing `fetchMore()` for infinite scroll.

## Performance Strategy

| Concern | Solution |
|---------|----------|
| Large lists (timeline, search) | `@tanstack/virtual` — only ~50 DOM nodes |
| Thumbnail loading | Intersection Observer, load 200px before visible |
| Image display | Backend pre-generated 300px thumbnails at `/media/thumbs/*` |
| Pagination | Cursor-based, 100 items per page |
| Bundle size | Route-based code splitting (`React.lazy()`) |
| Re-renders | React.memo on card components, useMemo for derived data |
| PWA caching | Service worker caches thumbnails + static assets |

## Mock Data Seed Script

`backend/scripts/seed_mock_data.py`:
- Inserts ~50 media records with varied dates (2023-2026), random dimensions, fake EXIF
- Creates 2-3 events grouping photos by date+location proximity
- Creates 3-5 face clusters with placeholder faces
- Generates simple colored SVG files as thumbnail placeholders in `data/thumbs/`
- Inserts some embeddings (random byte vectors) so search returns results
- Idempotent: `--reset` flag clears all data before seeding
- Run: `python scripts/seed_mock_data.py --reset`

## Implementation Plan

8 sequential tasks (each depends on previous):

| # | Task | Key Files | Output |
|---|------|-----------|--------|
| 1 | Project Scaffold + Mock Data | package.json, vite.config.ts, tailwind, seed script | Dev server running, mock data in DB |
| 2 | Navigation + Layout Shell | App.tsx, MobileNav, DesktopRail | Navigable app shell with 6 routes |
| 3 | Home Page | HomePage, MemoryCard, useMedia hook | 卡片流 with real API data |
| 4 | Timeline + Search Pages | TimelinePage, SearchPage, YearPills, EventStrip, SearchBar, ImageUploader, PhotoGrid | Timeline browse + text/image search |
| 5 | People + Photo Detail | PeoplePage, FaceCard, PhotoDetail, Lightbox | Face grid + full-screen viewer |
| 6 | Settings Page | SettingsPage, useAdmin hook | All admin tools functional |
| 7 | Animations + Polish | framer-motion wrappers, Skeleton | Page transitions, loading states |
| 8 | PWA + Integration | vite-plugin-pwa config, manifest | Installable, offline-ready |

### Task Dependencies

```
Task 1 (Scaffold) ──> Task 2 (Nav) ──> Task 3 (Home) ──> Task 4 (Timeline+Search)
                                                                    │
                                                                    v
                                          Task 6 (Settings) <── Task 5 (People+Lightbox)
                                                                    │
                                                                    v
                                          Task 7 (Polish) ────> Task 8 (PWA)
```

Task 4 and Task 5 can run in parallel after Task 3 if using subagents.

## Dependencies

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "framer-motion": "^11.5.0",
    "@tanstack/react-virtual": "^3.10.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "vite": "^6.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "vite-plugin-pwa": "^0.20.0"
  }
}
```

## Out of Scope

- Face clustering UI (backend stubs return empty — Phase 4)
- Video playback controls (basic `<video>` tag only)
- User authentication (single-user local app)
- Internationalization (Chinese-only for v1)
- Mobile PWA install testing (desktop-first development)
