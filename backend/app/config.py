# backend/app/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    @property
    def media_root(self) -> str:
        return os.getenv("MEDIA_ROOT", "./media")

    @property
    def data_root(self) -> str:
        return os.getenv("DATA_ROOT", "./data")

    @property
    def thumbnail_size(self) -> int:
        return int(os.getenv("THUMBNAIL_SIZE", "300"))

    @property
    def host(self) -> str:
        return os.getenv("HOST", "0.0.0.0")

    @property
    def port(self) -> int:
        return int(os.getenv("PORT", "8501"))

    @property
    def db_path(self) -> str:
        return os.path.join(self.data_root, "metadata.db")

    @property
    def thumb_dir(self) -> str:
        return os.path.join(self.data_root, "thumbs")


settings = Settings()
