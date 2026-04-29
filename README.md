# 🏠 HomeMemories AI

本地化家庭图片管理系统 - 隐私安全 · 智能感知 · 家庭友好

## ✨ 核心特性

- **🔍 智能搜索**: 支持文字搜索和以图搜图，基于 CLIP 多模态模型
- **👤 人物相册**: 自动检测和聚类人脸，无需手动标注
- **📅 日期浏览**: 按时间线浏览照片和视频
- **🧹 智能清理**: 自动检测模糊照片和重复照片
- **🎬 视频支持**: 视频关键帧提取和内容搜索
- **🌐 局域网共享**: 手机/平板通过浏览器访问
- **🔒 完全离线**: 所有模型本地运行，数据永不离开本机
- **📅 记忆唤醒**: 首页显示"去年今天"的照片

## 🖥️ 系统要求

- **操作系统**: Windows 11
- **Python**: 3.11.9
- **GPU**: NVIDIA RTX 5080 (16GB) 或其他支持 CUDA 的显卡
- **内存**: 64GB RAM
- **存储**: 2TB SSD

## 📦 快速开始

### 1. 安装依赖

双击运行 `install.bat` 或手动执行：

```bash
# 创建虚拟环境
python -m venv homememories_env
homememories_env\Scripts\activate

# 安装 PyTorch (CUDA 12.1)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 安装其他依赖
pip install -r requirements.txt
```

### 2. 配置环境

复制 `.env.example` 为 `.env` 并修改配置：

```bash
copy .env.example .env
```

编辑 `.env` 文件，设置您的照片目录：

```env
MEDIA_ROOT=D:/Photos  # 修改为您的照片目录
DATA_ROOT=./data      # 数据存储目录
MODELS_ROOT=./models  # 模型存储目录
```

### 3. 下载模型

首次使用需要下载 AI 模型（仅一次）：

```bash
python scripts/download_models.py
```

### 4. 测试系统（可选）

运行测试脚本验证系统是否正常：

```bash
test.bat
```

或手动执行：

```bash
python test_system.py
```

### 5. 启动应用

双击运行 `start.bat` 或执行：

```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

### 6. 访问应用

- **本机访问**: http://localhost:8501
- **局域网访问**: http://YOUR_IP:8501

## 📖 使用指南

### 首次使用流程

1. **扫描媒体文件**
   - 在"扫描"页面设置照片目录
   - 点击"开始扫描"导入照片和视频

2. **生成向量嵌入**
   - 在"向量化"页面点击"开始生成嵌入"
   - 为所有媒体文件生成 CLIP 向量

3. **人脸检测**
   - 在"人脸"页面点击"开始人脸检测"
   - 自动检测人脸并聚类

4. **开始使用**
   - 使用"搜索"功能查找照片
   - 在"人物"页面浏览人物相册
   - 在"清理"页面查看模糊和重复照片

### 功能说明

#### 🔍 智能搜索
- **文字搜索**: 输入关键词如"海滩"、"生日"、"烟花"
- **图片搜索**: 上传图片查找相似照片

#### 👤 人物相册
- 自动检测所有人脸
- 按相似度聚类成不同人物
- 点击人物卡片查看该人物的所有照片

#### 📅 日期浏览
- 按日期查看照片
- 支持按年、月、日筛选

#### 🧹 智能清理
- **模糊照片**: 基于拉普拉斯方差检测
- **重复照片**: 基于 dHash 算法检测

## 🏗️ 项目结构

```
HomeMemories AI/
├── app.py                 # Streamlit 主应用
├── config.py              # 配置文件
├── requirements.txt       # 依赖列表
├── .env.example          # 环境变量模板
├── start.bat             # 启动脚本
├── install.bat           # 安装脚本
├── src/
│   ├── __init__.py
│   ├── database.py       # SQLite 数据库
│   ├── scanner.py        # 媒体文件扫描
│   ├── exif_extractor.py # EXIF 日期提取
│   ├── video_extractor.py # 视频帧提取
│   ├── clip_embedder.py  # CLIP 向量嵌入
│   ├── face_clusterer.py # 人脸检测与聚类
│   ├── quality_checker.py # 质量检测
│   └── vector_index.py   # FAISS 向量索引
├── scripts/
│   ├── __init__.py
│   └── download_models.py # 模型下载脚本
├── data/                 # 数据目录（自动创建）
│   ├── metadata.db       # SQLite 数据库
│   └── vectors.index     # FAISS 索引
└── models/               # 模型目录（自动创建）
    └── clip/             # CLIP 模型
```

## 🔧 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 深度学习框架 | PyTorch | 2.2.0+cu121 |
| 多模态模型 | CLIP (ViT-B/32) | openai/clip-vit-base-patch32 |
| 人脸识别 | InsightFace | 0.7.3 |
| 向量检索 | FAISS-GPU | 1.8.0.post1 |
| 视频处理 | OpenCV | 4.9.0.80 |
| 图像处理 | Pillow, scikit-image | 10.2.0, 0.22.0 |
| 数据库 | SQLite | 内置 |
| Web UI | Streamlit | 1.32.0 |

## 🔒 隐私与安全

- ✅ 所有模型本地加载，无需联网
- ✅ 数据存储在本地，永不离开本机
- ✅ 支持完全断网运行
- ✅ 仅监听局域网，无公网暴露

## 📊 性能优化

- GPU 加速：CLIP、InsightFace、FAISS 均启用 CUDA
- 批量处理：支持批量向量生成和搜索
- 增量更新：仅处理新增文件
- 向量索引：FAISS 高效向量检索

## 🐛 常见问题

### Q: 模型下载失败怎么办？
A: 检查网络连接，或手动从 HuggingFace 下载模型到 `models/` 目录。

### Q: GPU 不可用怎么办？
A: 系统会自动降级到 CPU 模式，但速度会变慢。

### Q: 如何增加照片目录？
A: 编辑 `.env` 文件中的 `MEDIA_ROOT` 路径。

### Q: 局域网无法访问？
A: 检查 Windows 防火墙设置，确保 8501 端口开放。

## 📝 开发路线

- [x] Phase 0: 环境与模型
- [x] Phase 1: 基础媒体管理
- [x] Phase 2: AI 核心能力
- [x] Phase 3: 亮点功能集成
- [x] Phase 4: Web UI 与体验
- [ ] Phase 5: 测试与优化

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- OpenAI CLIP 模型
- InsightFace 人脸识别库
- FAISS 向量检索引擎
- Streamlit Web 框架

---

**HomeMemories AI** - 让家庭回忆更智能 🏠
