import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    database: str
    user: str
    password: str = field(repr=False)
    raw_path: Path = ROOT / "data/raw"
    processed_path: Path = ROOT / "data/processed"

    @property
    def url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )

    @classmethod
    def from_env(cls):
        load_dotenv(ROOT / ".env", override=False)
        password = os.getenv("POSTGRES_PASSWORD", "")
        if not password or password == "change_me":
            raise ValueError("Configure POSTGRES_PASSWORD locally; never commit .env")
        port = int(os.getenv("POSTGRES_PORT", "5432"))
        if not 1 <= port <= 65535:
            raise ValueError("Invalid POSTGRES_PORT")
        return cls(
            host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
            port=port,
            database=os.getenv("POSTGRES_DB", "sales_profitability"),
            user=os.getenv("POSTGRES_USER", "sales_app"),
            password=password,
            raw_path=ROOT / os.getenv("DATA_RAW_PATH", "data/raw"),
            processed_path=ROOT / os.getenv("DATA_PROCESSED_PATH", "data/processed"),
        )
