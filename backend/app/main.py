from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import applications, auth, bulk, collections, history, queries, search, templates
from app.seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI):
    import traceback
    import sys
    try:
        init_db()
        seed()
    except Exception as e:
        print("CRITICAL: Application startup failed!", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(3)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(applications.router)
app.include_router(history.router)
app.include_router(search.router)
app.include_router(queries.router)
app.include_router(collections.router)
app.include_router(templates.router)
app.include_router(bulk.router)


@app.get("/health")
def health():
    from app.services.auth import google_login_configured
    from app.services.google_search import google_providers_configured

    return {
        "status": "ok",
        "app": settings.app_name,
        "google_providers": google_providers_configured(),
        "google_login": google_login_configured(),
        "database": "postgres" if "postgresql" in settings.database_url else "sqlite",
    }


@app.get("/categories")
def categories():
    from app.schemas import CATEGORIES

    return CATEGORIES
