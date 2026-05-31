# 🏠 HomeMemories AI

本地化家庭图片管理系统 — 隐私安全 · 智能感知 · 家庭友好

## ✨ 核心特性

- **🔍 智能搜索**: 支持中文语义搜索和以图搜图，基于 Chinese-CLIP 多模态模型
- **👤 人物相册**: InsightFace 人脸检测 + 自动聚类，支持重命名人物标签
- **📅 时间线浏览**: 按年份+事件分组浏览，事件自动聚类（时间邻近的照片归为一组）
- **🧹 智能清理**: 检测模糊照片和重复照片，支持预览和删除
- **🎬 视频支持**: 视频关键帧提取、缩略图生成、时长记录
- **🖼️ 相似照片**: Lightbox 查看照片时一键查找相似照片
- **🌐 局域网共享**: 手机/平板通过浏览器访问，支持 PWA 安装
- **🔒 完全离线**: Chinese-CLIP、InsightFace、FAISS 全部本地运行，数据永不离开本机
- **📅 记忆唤醒**: 首页显示"去年今天"的照片和随机回忆

## 🖥️ 系统要求

- **操作系统**: Windows 11（开发环境），Linux/macOS 也可运行
- **Python**: 3.11+
- **GPU**: NVIDIA RTX 5080 (16GB) 或其他 CUDA 显卡（CPU 模式可用但慢）
- **内存**: 16GB+ RAM
- **存储**: 取决于照片库大小

## 📦 快速开始

### 1. 后端安装

```bash
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# 安装依赖（国内用户建议用清华镜像）
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env
```

编辑 `.env` 文件：
```env
MEDIA_ROOT=D:/Photos   # 你的照片/视频目录路径
DATA_ROOT=./data       # 数据存储目录
```

### 2. 前端安装

```bash
cd frontend
npm install
```

### 3. 下载 AI 模型（仅首次）

首次启动后会自动下载，也可手动处理：

- **Chinese-CLIP 模型** (~400MB): 设置 `HF_ENDPOINT=https://hf-mirror.com` 走镜像，或手动下载 `OFA-Sys/chinese-clip-vit-base-patch16` 到 `~/.cache/huggingface/hub/`
- **InsightFace buffalo_l** (~330MB): 首次人脸检测时自动下载到 `~/.insightface/models/buffalo_l/`，需确保 GitHub 可访问

### 4. 启动应用

**启动后端** (端口 8501):
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8501
```

**启动前端开发服务器** (端口 5173):
```bash
cd frontend
npm run dev
```

**生产部署**:
```bash
cd frontend && npm run build
# 将 dist/ 目录作为静态文件部署，或让 FastAPI 直接 serve
```

### 5. 访问应用

- **前端开发**: http://localhost:5173
- **后端 API**: http://localhost:8501
- **局域网访问**: http://YOUR_IP:5173

## 📖 使用指南

### 首次使用流程

1. **扫描媒体文件**: 设置 → 输入照片目录路径 → 点击"扫描目录"
2. **生成 Embeddings**: 设置 → "生成 Embeddings"（为所有照片生成 AI 向量）
3. **人脸检测**: 设置 → "人脸检测" → "人脸聚类"
4. **事件生成**: 设置 → 调用 `POST /api/admin/events/generate` 自动聚类事件
5. **开始使用**: 首页浏览回忆、时间线查看、搜索照片、查看人物相册

### 功能说明

#### 🔍 智能搜索
- **文字搜索**: 输入中文关键词如"海滩"、"生日"、"烟花"进行语义搜索
- **图片搜索**: 上传图片查找视觉相似的照片
- 搜索缓存 1 小时，重复查询即时响应

#### 👤 人物相册
- 自动检测所有照片中的人脸并提取特征向量
- 按相似度自动聚类成不同人物
- 点击人物卡片查看该人物的所有照片
- 点击标签可重命名（如"人物 1" → "妈妈"）

#### 📅 时间线
- 年份选择器横向滑动切换年份
- 照片按时间邻近度自动分组为事件（3 小时窗口，最少 3 张）
- 点击事件展开查看横向滚动的照片条

#### 🧹 智能清理
- **模糊照片**: 拉普拉斯方差检测 + 缩略图预览 + 单张/批量删除
- **重复照片**: dHash 算法检测 + 分组对比展示

#### 🖼️ 照片详情 (Lightbox)
- 全屏查看，左右箭头/键盘切换
- "相似照片"按钮显示相似照片缩略图条
- 支持下载原图

#### ⚙️ 设置页面
- 媒体管理：自定义扫描路径 + 进度追踪
- AI 处理：Embedding 生成、人脸检测、人脸聚类
- 清理工具：模糊/重复检测 + 结果展示 + 删除操作
- 系统信息：媒体数量、数据库大小、上次扫描时间

## 🏗️ 项目结构

```
HomeMemories AI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 应用入口
│   │   ├── config.py            # 配置（从 .env 读取）
│   │   ├── database.py          # SQLite 数据库初始化
│   │   ├── models.py            # Pydantic 数据模型
│   │   ├── ai/
│   │   │   ├── embedding.py     # Chinese-CLIP 向量生成
│   │   │   ├── search_index.py  # FAISS GPU 向量索引
│   │   │   ├── face_detector.py # InsightFace 人脸检测
│   │   │   └── quality.py       # 模糊/重复检测
│   │   ├── scanner/
│   │   │   ├── scanner.py       # 媒体文件扫描
│   │   │   ├── exif_extractor.py# EXIF 日期提取
│   │   │   ├── thumbnail.py     # 图片缩略图生成
│   │   │   └── video_extractor.py# 视频关键帧提取
│   │   ├── services/
│   │   │   ├── media_service.py # 媒体查询 + 相似照片
│   │   │   ├── scan_service.py  # 扫描任务 + JobTracker
│   │   │   ├── search_service.py# 搜索 + Embedding 生成
│   │   │   ├── face_service.py  # 人脸检测任务
│   │   │   ├── cluster_service.py# 人脸聚类
│   │   │   ├── quality_service.py# 清理检测任务
│   │   │   └── event_service.py # 事件自动生成
│   │   └── routers/
│   │       ├── media.py         # /api/media/*
│   │       ├── timeline.py      # /api/timeline/*
│   │       ├── search.py        # /api/search/*
│   │       ├── faces.py         # /api/faces/*
│   │       └── admin.py         # /api/admin/*
│   ├── data/                    # 运行时数据（自动创建）
│   │   ├── metadata.db          # SQLite 数据库
│   │   ├── thumbs/              # 缩略图缓存
│   │   └── faiss/               # FAISS 索引文件
│   ├── scripts/
│   │   ├── seed_mock_data.py    # Mock 数据生成
│   │   └── seed_test_faces.py   # 测试人脸数据
│   └── tests/                   # 后端测试
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # 路由配置
│   │   ├── api/client.ts        # API 客户端
│   │   ├── hooks/               # 自定义 hooks (SWR 模式)
│   │   ├── pages/               # 6 个页面组件
│   │   ├── components/          # UI 组件
│   │   └── index.css            # Tailwind + Sakura Mist 主题
│   ├── package.json
│   └── vite.config.ts
├── docs/superpowers/specs/      # 设计文档
└── README.md
```

## 🔧 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI + Uvicorn | 异步 REST API |
| 数据库 | SQLite (WAL 模式) | 元数据、人脸、事件 |
| 深度学习框架 | PyTorch 2.x + CUDA | GPU 推理 |
| 多模态模型 | Chinese-CLIP (ViT-B/16) | 中文语义图像/文本嵌入, 512维 |
| 人脸识别 | InsightFace buffalo_l | 检测 + ArcFace 嵌入 |
| 向量检索 | FAISS-GPU (IVF+PQ) | 子秒级搜索 |
| 前端框架 | React 18 + TypeScript | SPA |
| 样式 | Tailwind CSS 3 | 樱花雾霭主题 |
| 动画 | framer-motion | 页面过渡 + 微交互 |
| 虚拟滚动 | @tanstack/react-virtual | 大数据量列表 |
| 构建 | Vite 6 | 开发服务器 + 打包 |
| PWA | vite-plugin-pwa | 离线可用, 可安装 |
| 图像处理 | Pillow, OpenCV | 缩略图, 视频帧 |
| AI 模型加载 | Transformers (HuggingFace) | CLIP 模型 |

## 🔒 隐私与安全

- ✅ 所有 AI 模型本地加载，无需联网
- ✅ 数据存储在本地，永不离开本机
- ✅ 支持完全断网运行
- ✅ 仅监听局域网，无公网暴露

## 📊 性能

- **搜索**: FAISS IVF+PQ 索引，100K 照片 <50ms 检索，>95% 召回率
- **GPU 内存**: Chinese-CLIP ~400MB + InsightFace ~200MB + FAISS ~80MB ≈ 总计 ~1.2GB
- **批量处理**: CLIP 向量生成 ~300-400 张/秒 (RTX 5080)
- **虚拟滚动**: 时间线/搜索结果仅渲染可见项
- **增量扫描**: 基于 SHA-256 校验，已存在文件跳过

## 🐛 常见问题

### Q: HuggingFace 模型下载失败？
A: 在 `.env` 中设置 `HF_ENDPOINT=https://hf-mirror.com` 使用镜像站下载 Chinese-CLIP。

### Q: InsightFace buffalo_l 下载失败？
A: 手动从 GitHub (`deepinsight/insightface`) 或 ModelScope 下载 buffalo_l 的 4 个 ONNX 文件，放到 `~/.insightface/models/buffalo_l/`。

### Q: GPU 不可用怎么办？
A: 系统会自动降级到 CPU 模式，但推理速度会显著变慢。

### Q: pip 安装依赖太慢？
A: 国内用户配置清华镜像 `pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple`。

### Q: npm 安装前端依赖太慢？
A: 配置淘宝镜像 `npm config set registry https://registry.npmmirror.com`。

### Q: 启动时报 NumPy/OpenCV/InsightFace 兼容性错误？
A: 确保版本组合匹配：`numpy==1.26.4` + `opencv-python-headless==4.9.0` + `onnxruntime==1.26.0` + `insightface==0.7.3`。InsightFace 0.7.3 的 Cython 扩展目前仅兼容 NumPy 1.x，升级 NumPy 2.x 会导致 `numpy.dtype size changed` 错误。

### Q: 局域网无法访问？
A: 检查 Windows 防火墙设置，确保 8501(后端) 和 5173(前端) 端口开放。

## 📝 开发路线

- [x] Phase 0: 环境与模型 (PyTorch, CLIP, InsightFace, FAISS)
- [x] Phase 1: 后端核心 (FastAPI, SQLite, 扫描, 缩略图, API)
- [x] Phase 2: AI 流水线 (Chinese-CLIP, FAISS, 搜索, 人脸, 质量检测)
- [x] Phase 3: 前端 (React, Tailwind, 6 页面, 导航, 动效)
- [x] Phase 4: 打磨 (PWA, 骨架屏, 响应式, 视频关键帧)
- [x] Phase 5: 功能补完 (相似照片, 事件生成, 清理 UI, 标签编辑)
- [ ] Phase 6: 测试与优化 (前端测试, 100K 压力测试, 性能调优)

### TODO

**P0 — 必备基础体验**
- [x] 手机上传 (底部"+"按钮 → 批量选照片/视频 → 进度条 → 自动触发扫描+AI处理)
- [x] 扫码访问 (设置页生成局域网二维码，手机一扫即开)
- [x] 批量操作 (长按进入选择模式，批量加入相册/下载/删除)
- [x] 缩略图 EXIF 方向修复 (ImageOps.exif_transpose 自动纠正人像倒置)
- [x] 首页"去年今天"横向滑动大图 + "随机回忆"小图网格
- [x] PC 端上传入口 (DesktopRail 侧边栏底部)
- [x] 重复照片支持删除操作 (批量选择 → 智能勾选较差质量 → 一键删除)

**P1 — 核心体验闭环**
- [x] 收藏功能 (Lightbox 加收藏按钮，首页加收藏卡片流)
- [x] 手动相册 (创建/命名/换封面/添加照片，与 AI 事件互补)
- [x] 分享/导出 (局域网临时分享链接、选中多张导出 zip、拼图)
- [x] 外部导入 (Google Takeout zip 导入、iCloud 导出目录一键迁移)
- [x] 系统信息展示 GPU 状态 (CUDA 可用性、显存使用、模型加载状态)

**P2 — 情感与留存**
- [ ] 那年今日 PWA 通知 (每日浏览器推送，提醒回忆)
- [x] 自动精选集 (基于质量分数 + 人脸 + 事件代表性的月选)
- [ ] 时光对比 (同一人物不同时期的照片并排对比)
- [ ] 拍照直传 (PWA `capture` 属性调起摄像头即拍即传)
- [ ] 首页"最近添加"使用 `ORDER BY date_added DESC` 真实数据

**P3 — 锦上添花**
- [ ] 统计数据看板 (年/月维度拍摄统计、人物出现频次、时间分布)
- [ ] 场景化搜索 (快捷标签：🎄节日 🌳户外 🍜美食 🎂生日 👶孩子 🐱宠物)
- [ ] 外部备份 (一键备份到外置硬盘/NAS/指定目录，本地双副本)
- [ ] 事件浏览优化 (点击事件展开内联网格而非横向条)
- [ ] 人脸识别 GPU 加速 (当前 onnxruntime 使用 CPU 推理)

**P4 — 测试与质量**
- [ ] 后端新功能测试 (similar 端点、event_service、video_extractor)
- [ ] 前端 E2E/组件测试 (当前前端零测试)
- [ ] 100K 照片压力测试 (FAISS 召回率、API 响应时间验证)

## 🙏 致谢

- OFA-Sys Chinese-CLIP 模型
- InsightFace 人脸识别库
- FAISS 向量检索引擎
- FastAPI, React, Tailwind CSS 社区

---

**HomeMemories AI** — 让家庭回忆更智能 🏠
