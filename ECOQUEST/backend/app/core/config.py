import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")


class Settings:
    def __init__(self) -> None:
        default_database = f"sqlite:///{(BACKEND_DIR / 'ecoquest.db').as_posix()}"
        self.database_url = os.getenv("DATABASE_URL", default_database)
        self.secret_key = os.getenv("SECRET_KEY", "")
        self.algorithm = os.getenv("ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        self.is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"


settings = Settings()
