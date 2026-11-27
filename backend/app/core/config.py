"""
IdeaScope – Application settings.
Owner: Member 2 (Sufiyaan Imran)

Reads all configuration from environment variables / .env file.
No hard-coded secrets anywhere in this file.
Startup validation: missing DATABASE_URL or weak JWT_SECRET cause a
clear error message instead of a silent 500 later.
"""

import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    postgres_user: str = "ideascope"
    postgres_password: str = ""
    postgres_db: str = "ideascope"
    database_url: str = ""

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    # ── Bootstrap Main Admin ─────────────────────────────────────────────────
    main_admin_email: str = ""
    main_admin_password: str = ""

    # ── AI / LLM ──────────────────────────────────────────────────────────────
    llm_provider: str = "mock"
    anthropic_api_key: str = ""
    claude_model: str = "claude-opus-5-5"
    embedding_model: str = "BAAI/bge-m3"
    embedding_provider: str = "mock"

    # ── Application ──────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173"
    upload_dir: str = "/data/uploads"
    max_upload_mb: int = 10

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list (split on comma)."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


def _validate_settings(s: Settings) -> None:
    """Fail fast with a clear message if critical settings are missing."""
    errors = []

    if not s.database_url:
        errors.append(
            "DATABASE_URL is not set. "
            "Add it to .env, e.g.: "
            "DATABASE_URL=postgresql+psycopg://user:pass@db:5432/ideascope"
        )

    if not s.jwt_secret or len(s.jwt_secret) < 32:
        errors.append(
            "JWT_SECRET is missing or too short (minimum 32 characters). "
            'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
        )

    if errors:
        print("\n=== IdeaScope startup error ===", flush=True)
        for e in errors:
            print(f"  ERROR: {e}", flush=True)
        print("================================\n", flush=True)
        sys.exit(1)


settings = Settings()
_validate_settings(settings)
