# backend/app/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    media_root: str = os.getenv("MEDIA_ROOT", "./media")
    data_root: str = os.getenv("DATA_ROOT", "./data")
    thumbnail_size: int = int(os.getenv("THUMBNAIL_SIZE", "300"))
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8501"))

    @property
    def db_path(self) -> str:
        return os.path.join(self.data_root, "metadata.db")

    @property
    def thumb_dir(self) -> str:
        return os.path.join(self.data_root, "thumbs")


settings = Settings()
