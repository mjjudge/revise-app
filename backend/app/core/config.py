"""Application configuration loaded from environment variables."""

import secrets
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central config — reads from env vars or .env file."""

    app_env: str = "dev"
    database_url: str = "sqlite:////data/app.sqlite3"
    openai_api_key: str = ""
    lan_subnet_allow: str = "192.168.1.0/24"

    # Auth
    secret_key: str = secrets.token_urlsafe(32)
    session_max_age: int = 60 * 60 * 24  # 24 hours
    kid_pin: str = "1234"      # default; override via env
    admin_pin: str = "9999"    # default; override via env

    # Gamification
    gold_to_pence: int = 2              # 1 Gold = 2p
    weekly_gold_cap: int = 100          # Max gold earnable per week (admin can change)

    # Child personalisation
    child_name: str = "Anna"
    child_nicknames: str = "Chibs,Chibby"  # comma-separated

    @property
    def sqlite_path(self) -> Path:
        """Extract the file path from the sqlite URL."""
        return Path(self.database_url.replace("sqlite:///", ""))

    @property
    def nickname_list(self) -> list[str]:
        return [n.strip() for n in self.child_nicknames.split(",") if n.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
