from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Vacancylane"
    # Local Docker Postgres (shyftos-postgres-local) mapped to host :5434.
    database_url: str = (
        "postgresql+psycopg://shyftos-rbac:shyftos@127.0.0.1:5434/vacancylane"
    )
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
    ]

    # Real Google organic results via Serper (https://serper.dev — 2,500 free
    # queries on signup). Without this, search falls back to DDGS metasearch.
    serper_api_key: str = ""

    # Optional official Google Programmable Search (Custom Search JSON API).
    # Free tier is 100 queries/day. Used when Serper is unset or returns nothing.
    google_api_key: str = ""
    google_search_engine_id: str = ""

    # Google Sign-In (OAuth 2.0 Web client ID from Google Cloud Console).
    google_oauth_client_id: str = ""

    # JWT for session cookies / Authorization bearer tokens after Google login.
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24 * 14


settings = Settings()

if settings.database_url.startswith("postgresql://"):
    settings.database_url = settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
elif settings.database_url.startswith("postgres://"):
    settings.database_url = settings.database_url.replace("postgres://", "postgresql+psycopg://", 1)

