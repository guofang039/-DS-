import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_PORT: int = 21114
    JWT_SECRET: str = os.getenv("JWT_SECRET", "xiaoxiang-ds-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24 * 7
    
    HBBS_DB_PATH: str = os.getenv(
        "HBBS_DB_PATH", 
        "/home/guofang/Documents/trae_projects/rust/hbbs-data/db_v2.sqlite3"
    )
    ADMIN_DB_PATH: str = os.getenv(
        "ADMIN_DB_PATH",
        "/home/guofang/Documents/trae_projects/rust/rustdesk-admin/data/admin.db"
    )
    
    HBBS_HOST: str = os.getenv("HBBS_HOST", "127.0.0.1")
    HBBS_PORT: int = 21116
    HBBR_PORT: int = 21117
    
    CORS_ORIGINS: list = ["*"]

settings = Settings()
