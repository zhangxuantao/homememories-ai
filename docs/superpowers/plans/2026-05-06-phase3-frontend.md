# Phase 3 Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the React 18 + TypeScript + Tailwind CSS frontend for HomeMemories AI — 6 pages, responsive navigation, Sakura Mist theme, consuming FastAPI backend at :8501.

**Architecture:** SPA with react-router v6 lazy-loaded routes. Three-layer data flow: Page → Hook (SWR pattern) → API Client → FastAPI. Mobile bottom nav + desktop left rail. @tanstack/virtual for long lists. framer-motion for animations.

**Tech Stack:** React 18, TypeScript 5, Tailwind CSS 3, framer-motion 11, @tanstack/react-virtual 3, react-router-dom 6, Vite 6, vite-plugin-pwa 0.x

---

### Task 1: Project Scaffold + Mock Data Seed Script

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/index.css`
- Create: `frontend/src/vite-env.d.ts`
- Create: `frontend/public/favicon.svg`
- Create: `backend/scripts/seed_mock_data.py`

- [ ] **Step 1: Create frontend directory structure**

```bash
mkdir -p frontend/src/api frontend/src/hooks frontend/src/pages frontend/src/components/layout frontend/src/components/cards frontend/src/components/gallery frontend/src/components/timeline frontend/src/components/ui frontend/src/utils frontend/public
```

- [ ] **Step 2: Write package.json**

Write `frontend/package.json`:

```json
{
  "name": "homememories-frontend",
  "private": true,
  "version": "0.3.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.2",
    "framer-motion": "^11.5.6",
    "@tanstack/react-virtual": "^3.10.9"
  },
  "devDependencies": {
    "typescript": "^5.5.4",
    "vite": "^6.0.5",
    "@vitejs/plugin-react": "^4.3.2",
    "tailwindcss": "^3.4.13",
    "postcss": "^8.4.47",
    "autoprefixer": "^10.4.20",
    "@types/react": "^18.3.11",
    "@types/react-dom": "^18.3.1",
    "vite-plugin-pwa": "^0.20.5"
  }
}
```

- [ ] **Step 3: Install dependencies**

```bash
cd frontend && npm install
```
Expected: node_modules created, no errors.

- [ ] **Step 4: Write tsconfig.json**

Write `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"]
}
```

- [ ] **Step 5: Write tsconfig.node.json**

Write `frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 6: Write vite.config.ts**

Write `frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8501',
      '/media': 'http://localhost:8501',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

- [ ] **Step 7: Write Tailwind + PostCSS config**

Write `frontend/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#f0c6c6',
        misty: '#e8eef5',
        text: {
          DEFAULT: '#8b7e8a',
          light: '#c4a0a0',
        },
        subtle: '#f7e8e8',
      },
      fontFamily: {
        sans: [
          '"PingFang SC"',
          '"Microsoft YaHei"',
          '"Noto Sans SC"',
          'system-ui',
          '-apple-system',
          'sans-serif',
        ],
      },
      borderRadius: {
        card: '12px',
        btn: '8px',
        pill: '20px',
      },
    },
  },
  plugins: [],
};
```

Write `frontend/postcss.config.js`:

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 8: Write index.html**

Write `frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#f0c6c6" />
    <title>HomeMemories AI - 家庭回忆</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  </head>
  <body class="bg-white text-text font-sans">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 9: Write CSS with Sakura Mist theme**

Write `frontend/src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --color-primary: #f0c6c6;
  --color-misty: #e8eef5;
  --color-text: #8b7e8a;
  --color-text-light: #c4a0a0;
  --color-bg: #ffffff;
  --color-subtle: #f7e8e8;
}

body {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Glass card utility */
.glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(240, 198, 198, 0.3);
  box-shadow: 0 2px 12px rgba(139, 126, 138, 0.08);
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #e8eef5;
  border-radius: 3px;
}
```

- [ ] **Step 10: Write main.tsx and vite-env.d.ts**

Write `frontend/src/vite-env.d.ts`:

```typescript
/// <reference types="vite/client" />
```

Write `frontend/src/main.tsx`:

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

Write a placeholder `frontend/src/App.tsx`:

```typescript
export default function App() {
  return (
    <div className="min-h-screen flex items-center justify-center text-text-light">
      <p>HomeMemories AI</p>
    </div>
  );
}
```

- [ ] **Step 11: Write favicon**

Write `frontend/public/favicon.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#f0c6c6"/>
  <text x="16" y="23" text-anchor="middle" font-size="20">🌸</text>
</svg>
```

- [ ] **Step 12: Verify dev server starts**

```bash
cd frontend && npx vite --host 0.0.0.0
```
Expected: "Vite v6.x.x dev server running at http://localhost:5173"
Kill after verifying (Ctrl+C).

- [ ] **Step 13: Write mock data seed script**

Write `backend/scripts/seed_mock_data.py`:

```python
"""Seed mock data into SQLite for frontend development."""
import sqlite3
import os
import sys
import random
import hashlib
import struct
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.database import SCHEMA, get_connection
from app.config import settings

THUMB_DIR = settings.thumb_dir
DATA_DIR = settings.data_root

LOCATIONS = [
    ("杭州西湖", "杭州"),
    ("北京故宫", "北京"),
    ("上海外滩", "上海"),
    ("成都熊猫基地", "成都"),
    ("三亚亚龙湾", "三亚"),
    ("西安兵马俑", "西安"),
    ("丽江古城", "丽江"),
    ("厦门鼓浪屿", "厦门"),
]


def _gen_svg_thumb(filename: str, r: int, g: int, b: int) -> str:
    """Generate a colored SVG thumbnail and save to thumb dir."""
    os.makedirs(THUMB_DIR, exist_ok=True)
    path = os.path.join(THUMB_DIR, filename)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">'
        f'<rect width="300" height="300" fill="rgb({r},{g},{b})"/>'
        f'<text x="150" y="155" text-anchor="middle" font-size="48" fill="white">📷</text>'
        f'</svg>'
    )
    with open(path, "w") as f:
        f.write(svg)
    return filename


def seed(reset: bool = False):
    """Seed mock data."""
    conn = get_connection()
    if reset:
        conn.executescript("""
            DELETE FROM event_media;
            DELETE FROM events;
            DELETE FROM faces;
            DELETE FROM face_clusters;
            DELETE FROM embeddings;
            DELETE FROM search_cache;
            DELETE FROM media;
        """)
        conn.commit()
        # Re-init schema in case tables were dropped
        conn.executescript(SCHEMA)
        conn.commit()

    # Check if data already exists
    count = conn.execute("SELECT COUNT(*) FROM media").fetchone()[0]
    if count > 0:
        print(f"Already {count} media records. Use --reset to clear first.")
        conn.close()
        return

    base_date = datetime(2024, 1, 1)
    media_ids = []

    # Insert ~50 media records
    for i in range(50):
        days_offset = random.randint(0, 900)
        dt = base_date + timedelta(days=days_offset)
        date_taken = dt.strftime("%Y-%m-%dT%H:%M:%S")
        date_added = (dt + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%dT%H:%M:%S")
        w, h = random.choice([(4000, 3000), (3000, 4000), (1920, 1080), (3024, 4032)])
        loc = random.choice(LOCATIONS)

        r, g, b = random.randint(180, 240), random.randint(160, 220), random.randint(170, 230)
        thumb_filename = f"mock_{i:03d}.svg"
        _gen_svg_thumb(thumb_filename, r, g, b)

        filename = f"IMG_{20230101 + i:04d}.jpg"
        checksum = hashlib.sha256(f"mock_{i}".encode()).hexdigest()
        dhash = hashlib.md5(f"dhash_{i}".encode()).hexdigest()[:16]

        cursor = conn.execute(
            """INSERT INTO media (path, filename, media_type, width, height, file_size,
               date_taken, date_added, thumbnail_path, duration, is_blurry, blur_score,
               dhash, checksum)
               VALUES (?, ?, 'image', ?, ?, ?, ?, ?, ?, NULL, 0, NULL, ?, ?)""",
            (
                f"C:/Photos/Mock/{filename}",
                filename,
                w, h,
                random.randint(2_000_000, 15_000_000),
                date_taken,
                date_added,
                thumb_filename,
                dhash,
                checksum,
            ),
        )
        media_ids.append(cursor.lastrowid)

    # Insert 3 events
    events_data = [
        ("2024年3月 · 杭州西湖", "2024-03-15", "2024-03-16", "杭州西湖"),
        ("2024年8月 · 三亚亚龙湾", "2024-08-10", "2024-08-14", "三亚亚龙湾"),
        ("2025年1月 · 北京故宫", "2025-01-20", "2025-01-20", "北京故宫"),
    ]
    event_ids = []
    for title, start, end, loc in events_data:
        cursor = conn.execute(
            "INSERT INTO events (title, start_date, end_date, cover_media_id, media_count, location) VALUES (?, ?, ?, ?, 0, ?)",
            (title, start, end, media_ids[len(event_ids) % len(media_ids)], loc),
        )
        event_ids.append(cursor.lastrowid)

    # Link media to events
    for ei, eid in enumerate(event_ids):
        start_idx = ei * 4
        for mi in media_ids[start_idx : start_idx + random.randint(4, 8)]:
            conn.execute(
                "INSERT INTO event_media (event_id, media_id, sort_order) VALUES (?, ?, ?)",
                (eid, mi, 0),
            )
        conn.execute("UPDATE events SET media_count = (SELECT COUNT(*) FROM event_media WHERE event_id = ?) WHERE id = ?", (eid, eid))

    # Insert 3 face clusters
    face_cluster_ids = []
    for i in range(3):
        cursor = conn.execute(
            "INSERT INTO face_clusters (label, cover_face_id, photo_count) VALUES (?, NULL, 0)",
            (f"人物 {i + 1}",),
        )
        face_cluster_ids.append(cursor.lastrowid)

    # Insert 3-5 embeddings so search returns results
    for mi in media_ids[:5]:
        random_vector = struct.pack(f"{512}f", *[random.uniform(-1, 1) for _ in range(512)])
        conn.execute(
            "INSERT OR IGNORE INTO embeddings (media_id, vector, model_version, created_at) VALUES (?, ?, 'chinese-clip-vit-base', ?)",
            (mi, random_vector, datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
        )

    conn.commit()
    final_count = conn.execute("SELECT COUNT(*) FROM media").fetchone()[0]
    print(f"Seeded {final_count} media records, {len(event_ids)} events, {len(face_cluster_ids)} face clusters.")
    conn.close()


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    seed(reset=reset)
```

- [ ] **Step 14: Run mock data seed script**

```bash
cd backend && python scripts/seed_mock_data.py --reset
```
Expected: "Seeded 50 media records, 3 events, 3 face clusters."

- [ ] **Step 15: Verify backend serves data**

```bash
curl -s http://localhost:8501/api/timeline/years | head -c 200
```
Expected: JSON array of years like `[2025, 2024]`.

- [ ] **Step 16: Commit**

```bash
git add frontend/ backend/scripts/seed_mock_data.py
git commit -m "feat: scaffold frontend project and mock data seed script

- Vite + React + TypeScript + Tailwind CSS project setup
- Sakura Mist CSS custom properties and glass card utility
- Mock data seed script: 50 media, 3 events, 3 face clusters, 5 embeddings
- Dev server proxy to backend at :8501

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: Navigation + Layout Shell

**Files:**
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/components/layout/MobileNav.tsx`
- Create: `frontend/src/components/layout/DesktopRail.tsx`

- [ ] **Step 1: Write types file for shared types**

Write `frontend/src/api/client.ts` (types first, API functions in Task 3):

```typescript
// ── Types matching backend Pydantic models ──

export interface MediaItem {
  id: number;
  path: string;
  filename: string;
  media_type: 'image' | 'video';
  width: number | null;
  height: number | null;
  file_size: number | null;
  date_taken: string | null;
  date_added: string;
  thumbnail_path: string | null;
  duration: number | null;
  is_blurry: boolean;
}

export interface TimelineEvent {
  id: number;
  title: string;
  start_date: string;
  end_date: string;
  cover_media_id: number | null;
  media_count: number;
  location: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor: string | null;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  error: string | null;
}

export interface ScanStatus {
  job_id: string;
  status: string;
  progress: number;
  total: number;
  new: number;
  skipped: number;
  error: string | null;
}

export interface SystemStats {
  db_size_bytes: number;
  media_count: number;
  image_count: number;
  video_count: number;
  last_scan_time: string | null;
}

export interface SearchResponse {
  results: MediaItem[];
  next_cursor: string | null;
}

export interface FaceCluster {
  id: number;
  label: string | null;
  cover_face_id: number | null;
  photo_count: number;
}

// ── API Client ──

const BASE_URL = 'http://localhost:8501';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
    const url = new URL(path, this.baseUrl);
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
      });
    }
    const res = await fetch(url.toString());
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }
    return res.json();
  }

  async post<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }
    return res.json();
  }

  async upload<T>(path: string, file: File): Promise<T> {
    const formData = new FormData();
    formData.append('image_file', file);
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }
    return res.json();
  }

  async delete<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, { method: 'DELETE' });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }
    return res.json();
  }

  thumbUrl(thumbnailPath: string | null | undefined): string {
    if (!thumbnailPath) return '';
    return `${this.baseUrl}/media/thumbs/${thumbnailPath}`;
  }

  originalUrl(path: string): string {
    if (path.startsWith('http')) return path;
    return `${this.baseUrl}/media/original/${encodeURIComponent(path)}`;
  }
}

export const api = new ApiClient(BASE_URL);
```

- [ ] **Step 2: Write MobileNav component**

Write `frontend/src/components/layout/MobileNav.tsx`:

```typescript
import { NavLink } from 'react-router-dom';

const TABS = [
  { to: '/', label: '首页', icon: '🏠' },
  { to: '/timeline', label: '时间线', icon: '📅' },
  { to: '/search', label: '搜索', icon: '🔍' },
  { to: '/people', label: '人物', icon: '👤' },
  { to: '/settings', label: '设置', icon: '⚙️' },
];

export default function MobileNav() {
  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 flex justify-around items-center h-14 bg-white/90 backdrop-blur-xl border-t border-misty px-2 pb-1">
      {TABS.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          className={({ isActive }) =>
            `flex flex-col items-center gap-0.5 text-[10px] transition-colors ${
              isActive ? 'text-primary font-semibold' : 'text-text-light'
            }`
          }
        >
          <span className="text-lg">{tab.icon}</span>
          <span>{tab.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
```

- [ ] **Step 3: Write DesktopRail component**

Write `frontend/src/components/layout/DesktopRail.tsx`:

```typescript
import { useState } from 'react';
import { NavLink } from 'react-router-dom';

const TABS = [
  { to: '/', label: '首页', icon: '🏠' },
  { to: '/timeline', label: '时间线', icon: '📅' },
  { to: '/search', label: '搜索', icon: '🔍' },
  { to: '/people', label: '人物', icon: '👤' },
  { to: '/settings', label: '设置', icon: '⚙️' },
];

export default function DesktopRail() {
  const [expanded, setExpanded] = useState(false);

  return (
    <nav
      className={`hidden md:flex flex-col fixed left-0 top-0 h-full bg-[#faf7f7] border-r border-misty z-50 transition-all duration-200 ${
        expanded ? 'w-[200px]' : 'w-14'
      }`}
      onMouseEnter={() => setExpanded(true)}
      onMouseLeave={() => setExpanded(false)}
    >
      {/* Logo area */}
      <div className="flex items-center h-14 px-3 border-b border-misty">
        <span className="text-xl">🌸</span>
        {expanded && (
          <span className="ml-2 text-sm font-semibold text-text whitespace-nowrap overflow-hidden">
            HomeMemories
          </span>
        )}
      </div>

      {/* Nav items */}
      <div className="flex flex-col gap-1 p-2 flex-1">
        {TABS.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-btn transition-colors ${
                isActive
                  ? 'bg-primary/20 text-primary font-semibold'
                  : 'text-text-light hover:bg-misty/50'
              }`
            }
          >
            <span className="text-lg flex-shrink-0">{tab.icon}</span>
            {expanded && (
              <span className="text-sm whitespace-nowrap overflow-hidden">{tab.label}</span>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
```

- [ ] **Step 4: Write App.tsx with routes and layout**

Write `frontend/src/App.tsx`:

```typescript
import { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import MobileNav from './components/layout/MobileNav';
import DesktopRail from './components/layout/DesktopRail';

const HomePage = lazy(() => import('./pages/HomePage'));
const TimelinePage = lazy(() => import('./pages/TimelinePage'));
const SearchPage = lazy(() => import('./pages/SearchPage'));
const PeoplePage = lazy(() => import('./pages/PeoplePage'));
const PhotoDetail = lazy(() => import('./pages/PhotoDetail'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-white">
      <DesktopRail />
      <main className="md:ml-14 pb-14 md:pb-0">
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/timeline" element={<TimelinePage />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/people" element={<PeoplePage />} />
            <Route path="/photo/:id" element={<PhotoDetail />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </Suspense>
      </main>
      <MobileNav />
    </div>
  );
}
```

- [ ] **Step 5: Create stub page files**

Write stub files for all 6 pages so the app compiles. Each file:

`frontend/src/pages/HomePage.tsx`:
```typescript
export default function HomePage() {
  return <div className="p-6 pt-8"><h1 className="text-2xl font-bold text-text">首页</h1></div>;
}
```

`frontend/src/pages/TimelinePage.tsx`:
```typescript
export default function TimelinePage() {
  return <div className="p-6 pt-8"><h1 className="text-2xl font-bold text-text">时间线</h1></div>;
}
```

`frontend/src/pages/SearchPage.tsx`:
```typescript
export default function SearchPage() {
  return <div className="p-6 pt-8"><h1 className="text-2xl font-bold text-text">搜索</h1></div>;
}
```

`frontend/src/pages/PeoplePage.tsx`:
```typescript
export default function PeoplePage() {
  return <div className="p-6 pt-8"><h1 className="text-2xl font-bold text-text">人物</h1></div>;
}
```

`frontend/src/pages/PhotoDetail.tsx`:
```typescript
export default function PhotoDetail() {
  return <div className="p-6 pt-8"><h1 className="text-2xl font-bold text-text">照片详情</h1></div>;
}
```

`frontend/src/pages/SettingsPage.tsx`:
```typescript
export default function SettingsPage() {
  return <div className="p-6 pt-8"><h1 className="text-2xl font-bold text-text">设置</h1></div>;
}
```

- [ ] **Step 6: Verify compilation and routing**

```bash
cd frontend && npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 7: Start dev server and verify nav works**

```bash
cd frontend && npx vite --host 0.0.0.0
```
Open http://localhost:5173 in browser. Verify:
- Mobile bottom nav shows 5 tabs
- Desktop (widen window >768px) shows left icon rail
- Clicking tabs navigates between stubs
- Active tab is highlighted in pink

- [ ] **Step 8: Commit**

```bash
git add frontend/src/
git commit -m "feat: add navigation shell with mobile bottom bar and desktop rail

- React Router v6 with 6 lazy-loaded routes
- MobileNav: 5-tab bottom bar with active state
- DesktopRail: collapsible left icon rail with hover expand
- API client with typed interfaces for all backend models
- Stub pages for all 6 routes

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: Home Page — Card Stream

**Files:**
- Create: `frontend/src/hooks/useMedia.ts`
- Create: `frontend/src/components/cards/MemoryCard.tsx`
- Modify: `frontend/src/pages/HomePage.tsx`

- [ ] **Step 1: Write useMedia hook**

Write `frontend/src/hooks/useMedia.ts`:

```typescript
import { useState, useEffect, useCallback } from 'react';
import { api, MediaItem } from '../api/client';

interface UseApiState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

function useApi<T>(fetcher: () => Promise<T>, deps: unknown[] = []): UseApiState<T> & { mutate: () => void } {
  const [state, setState] = useState<UseApiState<T>>({ data: null, error: null, loading: true });

  const fetch = useCallback(() => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    fetcher()
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((err) => setState({ data: null, error: (err as Error).message, loading: false }));
  }, deps);

  useEffect(() => { fetch(); }, [fetch]);

  return { ...state, mutate: fetch };
}

export function useRandomMedia(count: number = 4) {
  return useApi(() => api.get<MediaItem[]>('/api/media/random', { count }), [count]);
}

export function useOnThisDay(month: number, day: number) {
  return useApi(() => api.get<MediaItem[]>('/api/media/on-this-day', { month, day }), [month, day]);
}

export function useMediaById(id: number | null) {
  return useApi(
    () => (id ? api.get<MediaItem>(`/api/media/${id}`) : Promise.reject(new Error('No id'))),
    [id]
  );
}
```

- [ ] **Step 2: Write MemoryCard component**

Write `frontend/src/components/cards/MemoryCard.tsx`:

```typescript
import { motion } from 'framer-motion';
import type { MediaItem } from '../../api/client';
import { api } from '../../api/client';

interface MemoryCardProps {
  item: MediaItem;
  title?: string;
  subtitle?: string;
  variant?: 'hero' | 'default';
  index?: number;
  onClick?: () => void;
}

export default function MemoryCard({ item, title, subtitle, variant = 'default', index = 0, onClick }: MemoryCardProps) {
  const thumbUrl = api.thumbUrl(item.thumbnail_path);

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.2 }}
      className={`glass-card rounded-card overflow-hidden cursor-pointer hover:shadow-lg transition-shadow ${
        variant === 'hero' ? 'col-span-full' : ''
      }`}
      style={{ borderLeft: variant === 'hero' ? '3px solid var(--color-primary)' : undefined }}
      onClick={onClick}
    >
      {/* Thumbnail area */}
      <div
        className={`w-full bg-gradient-to-br from-subtle to-misty flex items-center justify-center ${
          variant === 'hero' ? 'h-48 md:h-64' : 'h-40'
        }`}
      >
        {thumbUrl ? (
          <img
            src={thumbUrl}
            alt={item.filename}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <span className="text-4xl">🌸</span>
        )}
      </div>

      {/* Info */}
      <div className="p-3.5" style={{ borderLeft: variant === 'hero' ? 'none' : '3px solid var(--color-primary)' }}>
        {title && (
          <div className="text-[15px] font-semibold text-text mb-1">{title}</div>
        )}
        {subtitle && (
          <div className="text-xs text-text-light">{subtitle}</div>
        )}
        {!title && !subtitle && (
          <>
            <div className="text-sm font-medium text-text truncate">{item.filename}</div>
            <div className="text-xs text-text-light mt-0.5">{item.date_taken?.slice(0, 10)}</div>
          </>
        )}
      </div>
    </motion.div>
  );
}
```

- [ ] **Step 3: Write HomePage with all three sections**

Write `frontend/src/pages/HomePage.tsx`:

```typescript
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useOnThisDay, useRandomMedia } from '../hooks/useMedia';
import MemoryCard from '../components/cards/MemoryCard';
import { api } from '../api/client';

const today = new Date();

export default function HomePage() {
  const navigate = useNavigate();
  const onThisDay = useOnThisDay(today.getMonth() + 1, today.getDate());
  const randomFirst = useRandomMedia(4);
  const randomSecond = useRandomMedia(4);

  const randomItems = useMemo(() => {
    const ids = new Set<number>();
    const combined = [...(randomFirst.data || []), ...(randomSecond.data || [])];
    return combined.filter((item) => {
      if (ids.has(item.id)) return false;
      ids.add(item.id);
      return true;
    }).slice(0, 4);
  }, [randomFirst.data, randomSecond.data]);

  // Empty state
  const hasOnThisDay = onThisDay.data && onThisDay.data.length > 0;
  const hasRandom = randomItems.length > 0;
  const isEmpty = !hasOnThisDay && !hasRandom && !onThisDay.loading && !randomFirst.loading;

  if (isEmpty) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] px-6 text-center">
        <span className="text-6xl mb-4">🖼️</span>
        <p className="text-lg text-text font-semibold mb-2">还没有照片哦</p>
        <p className="text-sm text-text-light mb-6">去设置页扫描吧~</p>
        <button
          onClick={() => navigate('/settings')}
          className="px-6 py-2.5 bg-primary text-white rounded-btn font-medium hover:opacity-90 transition-opacity"
        >
          去设置
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 md:py-8">
      <motion.h1
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-2xl font-bold text-text mb-6"
      >
        家庭回忆
      </motion.h1>

      {/* Section 1: 去年今天 */}
      {hasOnThisDay && (
        <section className="mb-8">
          <h2 className="text-base font-semibold text-text mb-3">去年今天</h2>
          {onThisDay.data!.slice(0, 3).map((item, i) => (
            <MemoryCard
              key={item.id}
              item={item}
              variant="hero"
              index={i}
              title={item.date_taken?.slice(0, 10)}
              subtitle={`${item.filename}`}
              onClick={() => navigate(`/photo/${item.id}`)}
            />
          ))}
        </section>
      )}

      {/* Section 2: 随机回忆 */}
      {hasRandom && (
        <section className="mb-8">
          <h2 className="text-base font-semibold text-text mb-3">随机回忆</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {randomItems.map((item, i) => (
              <MemoryCard
                key={item.id}
                item={item}
                index={i}
                title={item.date_taken?.slice(0, 10)}
                subtitle={item.filename}
                onClick={() => navigate(`/photo/${item.id}`)}
              />
            ))}
          </div>
        </section>
      )}

      {/* Section 3: 最近添加 — recent from random pool */}
      {hasRandom && (
        <section>
          <h2 className="text-base font-semibold text-text mb-3">最近添加</h2>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {[...randomItems].reverse().slice(0, 10).map((item) => (
              <div
                key={item.id}
                className="flex-shrink-0 w-20 h-20 rounded-card overflow-hidden bg-misty cursor-pointer hover:opacity-80 transition-opacity"
                onClick={() => navigate(`/photo/${item.id}`)}
              >
                {item.thumbnail_path ? (
                  <img
                    src={api.thumbUrl(item.thumbnail_path)}
                    alt={item.filename}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-2xl">📷</div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Loading state */}
      {(onThisDay.loading || randomFirst.loading) && (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 5: Start dev server and verify home page**

```bash
cd frontend && npx vite --host 0.0.0.0
```
Open http://localhost:5173 in browser. Verify:
- Home page shows "去年今天", "随机回忆", "最近添加" sections
- Cards have frosted glass appearance and fade-in animation
- Loading spinner shows while fetching
- Clicking card navigates to /photo/:id

- [ ] **Step 6: Commit**

```bash
git add frontend/src/hooks/useMedia.ts frontend/src/components/cards/MemoryCard.tsx frontend/src/pages/HomePage.tsx
git commit -m "feat: add home page with card stream sections

- useMedia hook with SWR pattern (random, on-this-day, by-id)
- MemoryCard component with frosted glass + sakura border accent
- Home page: 去年今天 hero, 随机回忆 grid, 最近添加 strip
- Empty state with navigation to settings

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: Timeline + Search Pages

**Files:**
- Create: `frontend/src/hooks/useTimeline.ts`
- Create: `frontend/src/hooks/useSearch.ts`
- Create: `frontend/src/components/timeline/YearPills.tsx`
- Create: `frontend/src/components/timeline/EventStrip.tsx`
- Create: `frontend/src/components/ui/SearchBar.tsx`
- Create: `frontend/src/components/ui/ImageUploader.tsx`
- Create: `frontend/src/components/gallery/PhotoGrid.tsx`
- Modify: `frontend/src/pages/TimelinePage.tsx`
- Modify: `frontend/src/pages/SearchPage.tsx`

- [ ] **Step 1: Write useTimeline hook**

Write `frontend/src/hooks/useTimeline.ts`:

```typescript
import { useState, useEffect, useCallback } from 'react';
import { api, TimelineEvent, PaginatedResponse, MediaItem } from '../api/client';

export function useTimelineYears() {
  const [years, setYears] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<number[]>('/api/timeline/years')
      .then(setYears)
      .catch(() => setYears([]))
      .finally(() => setLoading(false));
  }, []);

  return { years, loading };
}

export function useEvents(year: number | null) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (year === null) return;
    setLoading(true);
    api.get<TimelineEvent[]>('/api/timeline/events', { year })
      .then(setEvents)
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, [year]);

  return { events, loading };
}

export function useEventMedia(eventId: number | null) {
  const [items, setItems] = useState<MediaItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const fetchMore = useCallback(() => {
    if (!eventId || loading || !hasMore) return;
    setLoading(true);
    api.get<PaginatedResponse<MediaItem>>(`/api/timeline/event/${eventId}/media`, {
      cursor: nextCursor ?? undefined,
      limit: 100,
    })
      .then((res) => {
        setItems((prev) => [...prev, ...res.items]);
        setNextCursor(res.next_cursor);
        setHasMore(!!res.next_cursor);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [eventId, nextCursor, loading, hasMore]);

  useEffect(() => {
    setItems([]);
    setNextCursor(null);
    setHasMore(true);
  }, [eventId]);

  useEffect(() => { fetchMore(); }, [eventId]);

  return { items, loading, hasMore, fetchMore };
}
```

- [ ] **Step 2: Write YearPills component**

Write `frontend/src/components/timeline/YearPills.tsx`:

```typescript
import { useRef } from 'react';

interface YearPillsProps {
  years: number[];
  selectedYear: number | null;
  onSelect: (year: number) => void;
}

export default function YearPills({ years, selectedYear, onSelect }: YearPillsProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  return (
    <div
      ref={scrollRef}
      className="flex gap-2 overflow-x-auto pb-2 px-4 scrollbar-hide"
      style={{ scrollbarWidth: 'none' }}
    >
      {years.map((year) => (
        <button
          key={year}
          onClick={() => onSelect(year)}
          className={`flex-shrink-0 px-4 py-1.5 rounded-pill text-sm font-medium transition-colors ${
            selectedYear === year
              ? 'bg-primary text-white'
              : 'bg-misty text-text hover:bg-subtle'
          }`}
        >
          {year}
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Write EventStrip component**

Write `frontend/src/components/timeline/EventStrip.tsx`:

```typescript
import type { TimelineEvent, MediaItem } from '../../api/client';
import { api } from '../../api/client';

interface EventStripProps {
  event: TimelineEvent;
  media: MediaItem[];
  onClick: () => void;
}

export default function EventStrip({ event, media, onClick }: EventStripProps) {
  return (
    <div className="glass-card rounded-card p-3.5 cursor-pointer hover:shadow-md transition-shadow" onClick={onClick}>
      <div className="flex items-center justify-between mb-2.5">
        <div>
          <h3 className="text-sm font-semibold text-text">{event.title}</h3>
          <p className="text-xs text-text-light mt-0.5">{event.media_count} 张照片</p>
        </div>
        <span className="text-text-light text-xs">→</span>
      </div>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {media.slice(0, 15).map((m) => (
          <div key={m.id} className="flex-shrink-0 w-[70px] h-[70px] rounded-lg overflow-hidden bg-misty">
            {m.thumbnail_path ? (
              <img src={api.thumbUrl(m.thumbnail_path)} alt="" className="w-full h-full object-cover" loading="lazy" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-xl">📷</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Write TimelinePage**

Write `frontend/src/pages/TimelinePage.tsx`:

```typescript
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTimelineYears, useEvents, useEventMedia } from '../hooks/useTimeline';
import YearPills from '../components/timeline/YearPills';
import EventStrip from '../components/timeline/EventStrip';

export default function TimelinePage() {
  const navigate = useNavigate();
  const { years, loading: yearsLoading } = useTimelineYears();
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const { events, loading: eventsLoading } = useEvents(selectedYear);

  useEffect(() => {
    if (years.length > 0 && selectedYear === null) setSelectedYear(years[0]);
  }, [years, selectedYear]);

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 md:py-8">
      <h1 className="text-2xl font-bold text-text mb-4">时间线</h1>

      {yearsLoading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          <YearPills years={years} selectedYear={selectedYear} onSelect={setSelectedYear} />

          {eventsLoading ? (
            <div className="flex justify-center py-12">
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          ) : events.length === 0 ? (
            <p className="text-center text-text-light py-12">这一年还没有照片哦</p>
          ) : (
            <div className="mt-4 space-y-3">
              {events.map((event) => (
                <EventItem key={event.id} event={event} navigate={navigate} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function EventItem({ event, navigate }: { event: TimelineEvent; navigate: ReturnType<typeof useNavigate> }) {
  const [expanded, setExpanded] = useState(false);
  const { items, loading } = useEventMedia(expanded ? event.id : null);

  const handleClick = () => {
    if (!expanded) {
      setExpanded(true);
    } else {
      // Navigate to a detail view — for now just show the first photo
      if (items.length > 0) navigate(`/photo/${items[0].id}`);
    }
  };

  return (
    <EventStrip event={event} media={expanded ? items : []} onClick={handleClick} />
  );
}
```

Wait — there's a bug in this code. `useEffect` is used but not imported. Let me fix that in the plan step.

Actually, let me rewrite this more carefully. The `useEffect` import is missing. Let me fix the TimelinePage code.

- [ ] **Step 4 (corrected): Write TimelinePage**

Write `frontend/src/pages/TimelinePage.tsx`:

```typescript
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTimelineYears, useEvents, useEventMedia } from '../hooks/useTimeline';
import type { TimelineEvent } from '../api/client';
import YearPills from '../components/timeline/YearPills';
import EventStrip from '../components/timeline/EventStrip';

export default function TimelinePage() {
  const navigate = useNavigate();
  const { years, loading: yearsLoading } = useTimelineYears();
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const { events, loading: eventsLoading } = useEvents(selectedYear);

  useEffect(() => {
    if (years.length > 0 && selectedYear === null) setSelectedYear(years[0]);
  }, [years, selectedYear]);

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 md:py-8">
      <h1 className="text-2xl font-bold text-text mb-4">时间线</h1>

      {yearsLoading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          <YearPills years={years} selectedYear={selectedYear} onSelect={setSelectedYear} />

          {eventsLoading ? (
            <div className="flex justify-center py-12">
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          ) : events.length === 0 ? (
            <p className="text-center text-text-light py-12">这一年还没有照片哦</p>
          ) : (
            <div className="mt-4 space-y-3">
              {events.map((event) => (
                <EventItem key={event.id} event={event} navigate={navigate} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function EventItem({ event, navigate }: { event: TimelineEvent; navigate: ReturnType<typeof useNavigate> }) {
  const [expanded, setExpanded] = useState(false);
  const { items } = useEventMedia(expanded ? event.id : null);

  const handleClick = () => {
    if (!expanded) {
      setExpanded(true);
    } else if (items.length > 0) {
      navigate(`/photo/${items[0].id}`);
    }
  };

  return <EventStrip event={event} media={items} onClick={handleClick} />;
}
```

- [ ] **Step 5: Write SearchBar component**

Write `frontend/src/components/ui/SearchBar.tsx`:

```typescript
import { useState, useRef, useEffect } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  loading?: boolean;
}

export default function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed) {
      onSearch(trimmed);
      // Save to recent searches
      const recent = JSON.parse(localStorage.getItem('recentSearches') || '[]');
      const updated = [trimmed, ...recent.filter((s: string) => s !== trimmed)].slice(0, 8);
      localStorage.setItem('recentSearches', JSON.stringify(updated));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-light">🔍</span>
      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="搜索你的回忆..."
        className="w-full pl-10 pr-16 py-3 rounded-card border border-misty bg-white text-text placeholder-text-light text-sm focus:outline-none focus:border-primary transition-colors"
      />
      <button
        type="submit"
        disabled={loading || !query.trim()}
        className="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1 bg-primary text-white text-xs rounded-btn disabled:opacity-50"
      >
        {loading ? '搜索中...' : '搜索'}
      </button>
    </form>
  );
}
```

- [ ] **Step 6: Write ImageUploader component**

Write `frontend/src/components/ui/ImageUploader.tsx`:

```typescript
import { useState, useRef, type DragEvent } from 'react';

interface ImageUploaderProps {
  onUpload: (file: File) => void;
  loading?: boolean;
}

export default function ImageUploader({ onUpload, loading }: ImageUploaderProps) {
  const [dragging, setDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    if (!file.type.startsWith('image/')) return;
    setPreview(URL.createObjectURL(file));
    onUpload(file);
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => setDragging(false);

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div
      className={`border-2 border-dashed rounded-card p-8 text-center transition-colors cursor-pointer ${
        dragging ? 'border-primary bg-subtle' : 'border-misty hover:border-primary/50'
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => fileRef.current?.click()}
    >
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />
      {preview ? (
        <img src={preview} alt="Preview" className="max-h-48 mx-auto rounded-card object-contain" />
      ) : (
        <>
          <span className="text-4xl block mb-3">🖼️</span>
          <p className="text-sm text-text">拖拽图片到此处或点击上传</p>
          <p className="text-xs text-text-light mt-1">支持 JPG, PNG, WebP</p>
        </>
      )}
      {loading && (
        <div className="mt-3 flex justify-center">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 7: Write PhotoGrid component**

Write `frontend/src/components/gallery/PhotoGrid.tsx`:

```typescript
import type { MediaItem } from '../../api/client';
import { api } from '../../api/client';

interface PhotoGridProps {
  items: MediaItem[];
  onItemClick: (id: number) => void;
}

export default function PhotoGrid({ items, onItemClick }: PhotoGridProps) {
  if (items.length === 0) {
    return <p className="text-center text-text-light py-8">暂无结果</p>;
  }

  return (
    <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
      {items.map((item) => (
        <div
          key={item.id}
          className="aspect-square rounded-card overflow-hidden bg-misty cursor-pointer relative group hover:opacity-90 transition-opacity"
          onClick={() => onItemClick(item.id)}
        >
          {item.thumbnail_path ? (
            <img
              src={api.thumbUrl(item.thumbnail_path)}
              alt={item.filename}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-2xl">📷</div>
          )}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/50 to-transparent p-2">
            <span className="text-white text-[10px]">{item.date_taken?.slice(0, 10)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 8: Write useSearch hook**

Write `frontend/src/hooks/useSearch.ts`:

```typescript
import { useState, useCallback } from 'react';
import { api, SearchResponse } from '../api/client';

export function useTextSearch() {
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (query: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post<SearchResponse>('/api/search/text', { query, limit: 50 });
      setResults(res);
    } catch (err) {
      setError((err as Error).message);
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return { results, loading, error, search };
}

export function useImageSearch() {
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.upload<SearchResponse>('/api/search/image', file);
      setResults(res);
    } catch (err) {
      setError((err as Error).message);
      setResults(null);
    } finally {
      setLoading(false);
    }
  }, []);

  return { results, loading, error, search };
}
```

- [ ] **Step 9: Write SearchPage**

Write `frontend/src/pages/SearchPage.tsx`:

```typescript
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTextSearch, useImageSearch } from '../hooks/useSearch';
import SearchBar from '../components/ui/SearchBar';
import ImageUploader from '../components/ui/ImageUploader';
import PhotoGrid from '../components/gallery/PhotoGrid';

type SearchMode = 'text' | 'image';

export default function SearchPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<SearchMode>('text');
  const textSearch = useTextSearch();
  const imageSearch = useImageSearch();

  const recentSearches: string[] = JSON.parse(localStorage.getItem('recentSearches') || '[]');

  const currentResults = mode === 'text' ? textSearch.results : imageSearch.results;
  const currentLoading = mode === 'text' ? textSearch.loading : imageSearch.loading;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 md:py-8">
      <h1 className="text-2xl font-bold text-text mb-4">搜索</h1>

      {/* Mode tabs */}
      <div className="flex gap-2 mb-4">
        {(['text', 'image'] as SearchMode[]).map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`px-4 py-1.5 rounded-pill text-sm font-medium transition-colors ${
              mode === m ? 'bg-primary text-white' : 'bg-misty text-text'
            }`}
          >
            {m === 'text' ? '文字搜索' : '图片搜索'}
          </button>
        ))}
      </div>

      {/* Search input */}
      {mode === 'text' ? (
        <>
          <SearchBar onSearch={textSearch.search} loading={textSearch.loading} />
          {recentSearches.length > 0 && !currentResults && (
            <div className="mt-4">
              <p className="text-xs text-text-light mb-2">最近搜索</p>
              <div className="flex flex-wrap gap-2">
                {recentSearches.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => textSearch.search(s)}
                    className="px-3 py-1 rounded-pill bg-misty text-text text-xs hover:bg-primary/20 transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <ImageUploader onUpload={imageSearch.search} loading={imageSearch.loading} />
      )}

      {/* Error */}
      {(textSearch.error || imageSearch.error) && (
        <p className="text-red-400 text-sm mt-4 text-center">
          {mode === 'text' ? textSearch.error : imageSearch.error}
        </p>
      )}

      {/* Results */}
      {currentResults && (
        <div className="mt-6">
          <p className="text-sm text-text-light mb-3">
            找到 {currentResults.results.length} 个结果
          </p>
          <PhotoGrid
            items={currentResults.results}
            onItemClick={(id) => navigate(`/photo/${id}`)}
          />
        </div>
      )}

      {/* Loading */}
      {currentLoading && (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 10: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 11: Start dev server and test Timeline + Search**

```bash
cd frontend && npx vite --host 0.0.0.0
```
Verify:
- Timeline: year pills load, clicking year shows event strips
- Search text: typing query + Enter shows results grid
- Search image: drag/drop shows preview, uploads to API
- PhotoGrid: clicking photo navigates to /photo/:id

- [ ] **Step 12: Commit**

```bash
git add frontend/src/hooks/useTimeline.ts frontend/src/hooks/useSearch.ts frontend/src/components/timeline/ frontend/src/components/ui/ frontend/src/components/gallery/PhotoGrid.tsx frontend/src/pages/TimelinePage.tsx frontend/src/pages/SearchPage.tsx
git commit -m "feat: add timeline and search pages

- Timeline: YearPills + EventStrip with expandable media
- Search: text mode with SearchBar + recent searches, image mode with drag-drop uploader
- PhotoGrid: responsive 3→5 column grid with date overlays
- useTimeline, useSearch hooks with SWR pattern

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 5: People Page + Photo Detail Lightbox

**Files:**
- Create: `frontend/src/components/cards/FaceCard.tsx`
- Create: `frontend/src/components/gallery/Lightbox.tsx`
- Modify: `frontend/src/pages/PeoplePage.tsx`
- Modify: `frontend/src/pages/PhotoDetail.tsx`

- [ ] **Step 1: Write FaceCard component**

Write `frontend/src/components/cards/FaceCard.tsx`:

```typescript
import { motion } from 'framer-motion';
import type { FaceCluster } from '../../api/client';

interface FaceCardProps {
  cluster: FaceCluster;
  index: number;
  onClick: () => void;
}

export default function FaceCard({ cluster, index, onClick }: FaceCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.2 }}
      className="glass-card rounded-card p-5 text-center cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
    >
      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-misty mx-auto mb-3 flex items-center justify-center">
        <span className="text-2xl">👤</span>
      </div>
      <h3 className="text-sm font-semibold text-text">{cluster.label || `人物 ${cluster.id}`}</h3>
      <span className="inline-block mt-1.5 px-3 py-0.5 rounded-pill bg-misty text-text-light text-xs">
        {cluster.photo_count} 张
      </span>
    </motion.div>
  );
}
```

- [ ] **Step 2: Write PeoplePage**

Write `frontend/src/pages/PeoplePage.tsx`:

```typescript
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, FaceCluster, MediaItem, PaginatedResponse } from '../api/client';
import FaceCard from '../components/cards/FaceCard';
import PhotoGrid from '../components/gallery/PhotoGrid';

export default function PeoplePage() {
  const navigate = useNavigate();
  const [clusters, setClusters] = useState<FaceCluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCluster, setSelectedCluster] = useState<FaceCluster | null>(null);
  const [clusterMedia, setClusterMedia] = useState<MediaItem[]>([]);

  useEffect(() => {
    api.get<FaceCluster[]>('/api/faces/clusters')
      .then(setClusters)
      .catch(() => setClusters([]))
      .finally(() => setLoading(false));
  }, []);

  const handleClusterClick = async (cluster: FaceCluster) => {
    setSelectedCluster(cluster);
    try {
      const res = await api.get<PaginatedResponse<MediaItem>>(`/api/faces/cluster/${cluster.id}/media`, { limit: 100 });
      setClusterMedia(res.items);
    } catch {
      setClusterMedia([]);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 md:py-8">
      <h1 className="text-2xl font-bold text-text mb-4">人物</h1>

      {selectedCluster ? (
        <div>
          <button
            onClick={() => setSelectedCluster(null)}
            className="text-sm text-primary mb-4 flex items-center gap-1"
          >
            ← 返回人物列表
          </button>
          <h2 className="text-lg font-semibold text-text mb-3">
            {selectedCluster.label || `人物 ${selectedCluster.id}`}
          </h2>
          {clusterMedia.length > 0 ? (
            <PhotoGrid items={clusterMedia} onItemClick={(id) => navigate(`/photo/${id}`)} />
          ) : (
            <p className="text-text-light text-center py-8">暂无照片</p>
          )}
        </div>
      ) : clusters.length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
          <span className="text-6xl mb-4">👤</span>
          <p className="text-text font-medium mb-1">还没有检测到人物哦</p>
          <p className="text-text-light text-sm">先去设置页面运行人脸检测吧~</p>
        </div>
      ) : (
        <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
          {clusters.map((c, i) => (
            <FaceCard key={c.id} cluster={c} index={i} onClick={() => handleClusterClick(c)} />
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Write Lightbox component**

Write `frontend/src/components/gallery/Lightbox.tsx`:

```typescript
import { useEffect, useCallback, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { MediaItem } from '../../api/client';
import { api } from '../../api/client';

interface LightboxProps {
  item: MediaItem;
  onClose: () => void;
  onPrev: (() => void) | null;
  onNext: (() => void) | null;
}

export default function Lightbox({ item, onClose, onPrev, onNext }: LightboxProps) {
  const [preloaded, setPreloaded] = useState<Record<string, HTMLImageElement>>({});

  // Preload adjacent image
  const preload = useCallback((url: string) => {
    if (preloaded[url]) return;
    const img = new Image();
    img.src = url;
    setPreloaded((p) => ({ ...p, [url]: img }));
  }, [preloaded]);

  // Keyboard navigation
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowLeft' && onPrev) onPrev();
      if (e.key === 'ArrowRight' && onNext) onNext();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose, onPrev, onNext]);

  // Prevent body scroll
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  const imageUrl = api.originalUrl(item.path);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[100] bg-black/90 flex flex-col"
        onClick={onClose}
      >
        {/* Top bar */}
        <div className="flex items-center justify-between px-4 py-3 text-white text-sm">
          <button onClick={onClose} className="hover:text-primary transition-colors">✕ 关闭</button>
          <a
            href={imageUrl}
            download={item.filename}
            className="hover:text-primary transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            下载
          </a>
        </div>

        {/* Image area */}
        <div className="flex-1 flex items-center justify-center" onClick={(e) => e.stopPropagation()}>
          {/* Prev button */}
          {onPrev && (
            <button
              onClick={onPrev}
              className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/10 text-white text-xl hover:bg-white/20 transition-colors flex items-center justify-center"
            >
              ‹
            </button>
          )}

          <img
            src={imageUrl}
            alt={item.filename}
            className="max-w-full max-h-[80vh] object-contain select-none"
            draggable={false}
          />

          {/* Next button */}
          {onNext && (
            <button
              onClick={onNext}
              className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/10 text-white text-xl hover:bg-white/20 transition-colors flex items-center justify-center"
            >
              ›
            </button>
          )}
        </div>

        {/* Bottom info bar */}
        <div className="px-4 py-3 text-white text-sm bg-gradient-to-t from-black/60 to-transparent">
          {item.date_taken && (
            <p className="text-white/80">{item.date_taken.slice(0, 10)}</p>
          )}
          <p className="text-white/50 text-xs mt-0.5">
            {item.width}×{item.height} · {item.filename}
          </p>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
```

- [ ] **Step 4: Write PhotoDetail page**

Write `frontend/src/pages/PhotoDetail.tsx`:

```typescript
import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { api, MediaItem } from '../api/client';
import { useMediaById } from '../hooks/useMedia';
import Lightbox from '../components/gallery/Lightbox';

export default function PhotoDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const mediaId = Number(id);
  const { data: item, loading } = useMediaById(mediaId);

  // Try to preload adjacent items to check if they exist
  const [hasPrev, setHasPrev] = useState(false);
  const [hasNext, setHasNext] = useState(false);

  useEffect(() => {
    if (!mediaId) return;
    api.get<MediaItem>(`/api/media/${mediaId - 1}`)
      .then(() => setHasPrev(true))
      .catch(() => setHasPrev(false));
    api.get<MediaItem>(`/api/media/${mediaId + 1}`)
      .then(() => setHasNext(true))
      .catch(() => setHasNext(false));
  }, [mediaId]);

  if (loading || !item) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <Lightbox
      item={item}
      onClose={() => navigate(-1)}
      onPrev={hasPrev ? () => navigate(`/photo/${mediaId - 1}`, { replace: true }) : null}
      onNext={hasNext ? () => navigate(`/photo/${mediaId + 1}`, { replace: true }) : null}
    />
  );
}
```

- [ ] **Step 5: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 6: Start dev server and test People + Lightbox**

```bash
cd frontend && npx vite --host 0.0.0.0
```
Verify:
- People page: shows face cluster grid (or empty state if no faces)
- Clicking face card navigates to cluster detail
- Photo detail: shows full-screen lightbox with image
- Arrow keys navigate, Escape closes
- URL changes to /photo/:id

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/cards/FaceCard.tsx frontend/src/components/gallery/Lightbox.tsx frontend/src/pages/PeoplePage.tsx frontend/src/pages/PhotoDetail.tsx
git commit -m "feat: add people page and photo detail lightbox

- PeoplePage: face cluster grid with cluster detail drill-down
- FaceCard: round avatar, label, photo count badge
- Lightbox: full-screen overlay with keyboard nav, download button
- PhotoDetail: adjacent photo preloading for instant navigation

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 6: Settings Page

**Files:**
- Create: `frontend/src/hooks/useAdmin.ts`
- Modify: `frontend/src/pages/SettingsPage.tsx`

- [ ] **Step 1: Write useAdmin hook**

Write `frontend/src/hooks/useAdmin.ts`:

```typescript
import { useState, useEffect, useCallback } from 'react';
import { api, SystemStats, JobStatus, ScanStatus, MediaItem } from '../api/client';

export function useAdminStats() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(() => {
    setLoading(true);
    api.get<SystemStats>('/api/admin/stats')
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  return { stats, loading, refresh: fetch };
}

export function useJobStatus(jobId: string | null, pollInterval: number = 2000) {
  const [status, setStatus] = useState<JobStatus | ScanStatus | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!jobId) return;
    setLoading(true);

    const poll = () => {
      api.get<JobStatus>(`/api/admin/job/${jobId}/status`)
        .then((s) => {
          setStatus(s);
          setLoading(false);
          if (s.status === 'completed' || s.status === 'failed') return;
        })
        .catch(() => setLoading(false));
    };

    poll();
    const interval = setInterval(poll, pollInterval);
    return () => clearInterval(interval);
  }, [jobId, pollInterval]);

  return { status, loading };
}

export function useAdminActions() {
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const startScan = useCallback(async () => {
    const res = await api.post<{ job_id: string }>('/api/admin/scan');
    setCurrentJobId(res.job_id);
    return res.job_id;
  }, []);

  const generateEmbeddings = useCallback(async () => {
    const res = await api.post<{ job_id: string }>('/api/admin/embeddings/generate');
    setCurrentJobId(res.job_id);
    return res.job_id;
  }, []);

  const startFaceDetection = useCallback(async () => {
    const res = await api.post<{ job_id: string }>('/api/admin/faces/detect');
    setCurrentJobId(res.job_id);
    return res.job_id;
  }, []);

  const startBlurCheck = useCallback(async () => {
    const res = await api.post<{ job_id: string }>('/api/admin/cleanup/blurry/check');
    setCurrentJobId(res.job_id);
    return res.job_id;
  }, []);

  const startDuplicateCheck = useCallback(async () => {
    const res = await api.post<{ job_id: string }>('/api/admin/cleanup/duplicates/check');
    setCurrentJobId(res.job_id);
    return res.job_id;
  }, []);

  return { currentJobId, startScan, generateEmbeddings, startFaceDetection, startBlurCheck, startDuplicateCheck };
}
```

- [ ] **Step 2: Write SettingsPage**

Write `frontend/src/pages/SettingsPage.tsx`:

```typescript
import { useState } from 'react';
import { useAdminStats, useJobStatus, useAdminActions } from '../hooks/useAdmin';

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-6">
      <h2 className="text-base font-semibold text-text mb-3">{title}</h2>
      {children}
    </section>
  );
}

function ActionButton({ label, onClick, disabled }: { label: string; onClick: () => void; disabled?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="w-full px-4 py-2.5 rounded-btn bg-primary text-white text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-opacity"
    >
      {label}
    </button>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-misty last:border-0">
      <span className="text-sm text-text">{label}</span>
      <span className="text-sm font-medium text-text">{value}</span>
    </div>
  );
}

export default function SettingsPage() {
  const { stats, loading: statsLoading, refresh: refreshStats } = useAdminStats();
  const { currentJobId, startScan, generateEmbeddings, startFaceDetection, startBlurCheck, startDuplicateCheck } = useAdminActions();
  const { status: jobStatus } = useJobStatus(currentJobId);

  const formatBytes = (bytes: number) => {
    if (bytes > 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
    if (bytes > 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${bytes} B`;
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 md:py-8">
      <h1 className="text-2xl font-bold text-text mb-6">设置</h1>

      {/* 媒体管理 */}
      <Section title="媒体管理">
        <div className="space-y-2">
          <ActionButton label="扫描目录" onClick={startScan} />
          {jobStatus && (
            <div className="glass-card rounded-card p-3 text-sm">
              <div className="flex justify-between text-text-light mb-1">
                <span>{jobStatus.status === 'running' ? '扫描中...' : jobStatus.status}</span>
                <span>{jobStatus.progress.toFixed(0)}%</span>
              </div>
              <div className="w-full h-1.5 bg-misty rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-500"
                  style={{ width: `${jobStatus.progress}%` }}
                />
              </div>
              {jobStatus.status === 'completed' && (
                <p className="text-xs text-text-light mt-1">
                  完成 — 点击"系统信息"下的刷新查看统计
                </p>
              )}
            </div>
          )}
        </div>
      </Section>

      {/* AI 处理 */}
      <Section title="AI 处理">
        <div className="space-y-2">
          <ActionButton label="生成 Embeddings" onClick={generateEmbeddings} />
          <ActionButton label="人脸检测" onClick={startFaceDetection} />
        </div>
      </Section>

      {/* 清理工具 */}
      <Section title="清理工具">
        <div className="space-y-2">
          <ActionButton label="检测模糊照片" onClick={startBlurCheck} />
          <ActionButton label="检测重复照片" onClick={startDuplicateCheck} />
        </div>
      </Section>

      {/* 系统信息 */}
      <Section title="系统信息">
        {statsLoading ? (
          <div className="flex justify-center py-6">
            <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : stats ? (
          <div className="glass-card rounded-card p-3">
            <StatRow label="总媒体数" value={String(stats.media_count)} />
            <StatRow label="图片" value={String(stats.image_count)} />
            <StatRow label="视频" value={String(stats.video_count)} />
            <StatRow label="数据库大小" value={formatBytes(stats.db_size_bytes)} />
            <StatRow label="上次扫描" value={stats.last_scan_time?.slice(0, 10) || '从未'} />
          </div>
        ) : (
          <p className="text-text-light text-sm">无法加载系统信息</p>
        )}
        <button
          onClick={refreshStats}
          className="mt-2 text-sm text-primary hover:underline"
        >
          刷新统计
        </button>
      </Section>
    </div>
  );
}
```

- [ ] **Step 3: Verify TypeScript compilation**

```bash
cd frontend && npx tsc --noEmit
```
Expected: No errors.

- [ ] **Step 4: Start dev server and test Settings page**

```bash
cd frontend && npx vite --host 0.0.0.0
```
Verify:
- Settings page shows 4 sections
- Buttons trigger backend actions (POST requests)
- Job progress bar shows when running
- System stats display correctly
- Refresh button reloads stats

- [ ] **Step 5: Commit**

```bash
git add frontend/src/hooks/useAdmin.ts frontend/src/pages/SettingsPage.tsx
git commit -m "feat: add settings page with admin controls

- useAdmin hook: stats, job polling, action mutations
- Settings page: media scan, AI processing, cleanup, system info
- Job progress bar with polling
- Stats display with refresh

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 7: Animations + Polish

**Files:**
- Create: `frontend/src/components/ui/Skeleton.tsx`
- Modify: `frontend/src/pages/HomePage.tsx`
- Modify: `frontend/src/pages/TimelinePage.tsx`
- Modify: `frontend/src/pages/SearchPage.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Write Skeleton component**

Write `frontend/src/components/ui/Skeleton.tsx`:

```typescript
interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div className={`animate-pulse bg-misty rounded-card ${className}`} />
  );
}

export function SkeletonCard() {
  return (
    <div className="glass-card rounded-card overflow-hidden">
      <Skeleton className="h-40 w-full !rounded-none" />
      <div className="p-3.5 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  );
}

export function SkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className="aspect-square" />
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Add page transitions to App.tsx**

Write `frontend/src/App.tsx` (replace existing):

```typescript
import { Suspense, lazy } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import MobileNav from './components/layout/MobileNav';
import DesktopRail from './components/layout/DesktopRail';

const HomePage = lazy(() => import('./pages/HomePage'));
const TimelinePage = lazy(() => import('./pages/TimelinePage'));
const SearchPage = lazy(() => import('./pages/SearchPage'));
const PeoplePage = lazy(() => import('./pages/PeoplePage'));
const PhotoDetail = lazy(() => import('./pages/PhotoDetail'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -12 },
};

function AnimatedPage({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{ duration: 0.2 }}
    >
      {children}
    </motion.div>
  );
}

export default function App() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-white">
      <DesktopRail />
      <main className="md:ml-14 pb-14 md:pb-0">
        <AnimatePresence mode="wait">
          <Suspense fallback={<PageLoader />}>
            <Routes location={location} key={location.pathname}>
              <Route path="/" element={<AnimatedPage><HomePage /></AnimatedPage>} />
              <Route path="/timeline" element={<AnimatedPage><TimelinePage /></AnimatedPage>} />
              <Route path="/search" element={<AnimatedPage><SearchPage /></AnimatedPage>} />
              <Route path="/people" element={<AnimatedPage><PeoplePage /></AnimatedPage>} />
              <Route path="/photo/:id" element={<PhotoDetail />} />
              <Route path="/settings" element={<AnimatedPage><SettingsPage /></AnimatedPage>} />
            </Routes>
          </Suspense>
        </AnimatePresence>
      </main>
      <MobileNav />
    </div>
  );
}
```

- [ ] **Step 3: Add Skeleton loading states to TimelinePage**

Update `frontend/src/pages/TimelinePage.tsx` — in the events loading section, replace the spinner:

```typescript
// Replace the spinner div in the eventsLoading section with:
<>
  <SkeletonCard />
  <SkeletonCard />
  <SkeletonCard />
</>
```

Add `import { SkeletonCard } from '../components/ui/Skeleton';` at the top.

- [ ] **Step 4: Add a format utility**

Write `frontend/src/utils/format.ts`:

```typescript
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
  } catch {
    return dateStr.slice(0, 10);
  }
}

export function formatFileSize(bytes: number | null | undefined): string {
  if (bytes == null) return '';
  if (bytes > 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  if (bytes > 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${bytes} B`;
}
```

- [ ] **Step 5: Verify TypeScript compilation and visual check**

```bash
cd frontend && npx tsc --noEmit
```
Expected: No errors.

```bash
cd frontend && npx vite --host 0.0.0.0
```
Verify:
- Page transitions: fade + slide between pages (except PhotoDetail)
- Loading skeletons show shimmer animation
- Cards have staggered entrance animations
- Navigation has spring transitions

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/ui/Skeleton.tsx frontend/src/App.tsx frontend/src/pages/TimelinePage.tsx frontend/src/utils/format.ts
git commit -m "feat: add animations, skeletons, and visual polish

- Page transitions: AnimatePresence fade+slide between routes
- Skeleton components: shimmer loading for cards and grids
- format utility: Chinese date formatting and file size
- Loading states on timeline page

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 8: PWA Configuration + Integration Test

**Files:**
- Modify: `frontend/vite.config.ts`
- Create: `frontend/public/manifest.json`

- [ ] **Step 1: Update vite.config.ts with PWA plugin**

Write `frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'HomeMemories AI - 家庭回忆',
        short_name: 'HomeMemories',
        description: '私人家庭照片管理系统',
        theme_color: '#f0c6c6',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
        icons: [
          {
            src: 'favicon.svg',
            sizes: 'any',
            type: 'image/svg+xml',
          },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,jpg,webp}'],
        runtimeCaching: [
          {
            urlPattern: /^https?:\/\/localhost:8501\/media\/thumbs\/.*/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'thumbnails',
              expiration: { maxEntries: 500, maxAgeSeconds: 30 * 24 * 60 * 60 },
            },
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8501',
      '/media': 'http://localhost:8501',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

- [ ] **Step 2: Write web app manifest**

Write `frontend/public/manifest.json`:

```json
{
  "name": "HomeMemories AI - 家庭回忆",
  "short_name": "HomeMemories",
  "description": "私人家庭照片管理系统 — 让家庭回忆更智能",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#f0c6c6",
  "orientation": "any",
  "lang": "zh-CN",
  "icons": [
    {
      "src": "/favicon.svg",
      "sizes": "any",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    }
  ]
}
```

- [ ] **Step 3: End-to-end smoke test**

```bash
cd frontend && npx vite build
```
Expected: Build succeeds, output in `frontend/dist/`.

```bash
cd frontend && npx vite preview --host 0.0.0.0 --port 4173
```

Manual test checklist:
1. Open http://localhost:4173
2. Navigate to each page (/, /timeline, /search, /people, /settings)
3. Home: cards appear with animation, empty state shows if no data
4. Timeline: year pills load, click year shows events
5. Search: text search returns results, image upload works
6. People: face grid or empty state shows
7. Settings: stats load, buttons trigger jobs
8. Photo detail: lightbox opens, arrow keys navigate, Escape closes
9. Desktop: left rail shows, hover expands
10. Mobile view (<768px): bottom nav shows

- [ ] **Step 4: Final commit**

```bash
git add frontend/vite.config.ts frontend/public/manifest.json
git commit -m "feat: add PWA support and finalize frontend

- VitePWA plugin with auto-update + workbox runtime caching
- Thumbnail cache-first strategy (max 500 entries, 30 days)
- Web app manifest for installable PWA
- Production build verified

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## Post-Implementation Verification

After all tasks complete, run the full verification:

```bash
# 1. Type check
cd frontend && npx tsc --noEmit

# 2. Production build
cd frontend && npx vite build

# 3. Verify backend is serving
curl -s http://localhost:8501/api/admin/stats

# 4. Verify mock data exists
curl -s http://localhost:8501/api/timeline/years

# 5. Start preview and manually test all pages
cd frontend && npx vite preview --host 0.0.0.0 --port 4173
```
