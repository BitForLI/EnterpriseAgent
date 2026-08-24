"""轻量配置：默认完全离线，可选 OpenAI。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    data_dir: Path = PROJECT_ROOT / "data"
    web_dir: Path = PROJECT_ROOT / "web"
    llm_provider: str = os.getenv("LLM_PROVIDER", "local").lower()
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ticket_db_path: Path = PROJECT_ROOT / os.getenv(
        "TICKET_DB_PATH", "data/runtime/support.db"
    )


settings = Settings()
