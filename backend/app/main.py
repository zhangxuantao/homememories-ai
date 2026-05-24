# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.data_root, exist_ok=True)
    os.makedirs(settings.media_root, exist_ok=True)
    os.makedirs(settings.thumb_dir, exist_ok=True)
    os.makedirs(settings.faiss_dir, exist_ok=True)
    os.makedirs(os.path.join(settings.data_root, "thumbs", "faces"), exist_ok=True)
    os.makedirs(os.path.join(settings.data_root, "faces"), exist_ok=True)
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="HomeMemories AI",
        version="0.2.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.routers.timeline import router as timeline_router
    from app.routers.media import router as media_router
    from app.routers.admin import router as admin_router
    from app.routers.search import router as search_router
    from app.routers.faces import router as faces_router
    from app.routers.upload import router as upload_router
    from app.routers.albums import router as albums_router

    app.include_router(timeline_router)
    app.include_router(media_router)
    app.include_router(admin_router)
    app.include_router(search_router)
    app.include_router(faces_router)
    app.include_router(upload_router)
    app.include_router(albums_router)

    # Ensure directories exist before mounting static files
    os.makedirs(settings.media_root, exist_ok=True)
    os.makedirs(settings.thumb_dir, exist_ok=True)
    os.makedirs(os.path.join(settings.data_root, "thumbs", "faces"), exist_ok=True)

    # Static file serving
    app.mount(
        "/media/thumbs",
        StaticFiles(directory=settings.thumb_dir),
        name="thumbs",
    )
    app.mount(
        "/media/original",
        StaticFiles(directory=settings.media_root),
        name="original",
    )
    faces_dir = os.path.join(settings.data_root, "thumbs", "faces")
    app.mount(
        "/media/faces",
        StaticFiles(directory=faces_dir),
        name="faces",
    )

    return app


app = create_app()
