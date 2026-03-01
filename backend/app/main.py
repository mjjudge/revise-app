import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.session import init_db
from app.db.seed import seed_users
from app.api.auth import router as auth_router
from app.api.pages import router as pages_router
from app.api.quest import router as quest_router
from app.api.admin import router as admin_router
from app.api.tutor import router as tutor_router
from app.templates.feed_loader import load_and_validate

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: validate feeds, create tables, seed users."""
    # Validate question feeds (fail fast if YAML is broken)
    skills, templates = load_and_validate()
    logger.info("Loaded %d skills, %d templates", len(skills.skills), len(templates.templates))

    init_db()
    seed_users()
    yield


app = FastAPI(title="Revise App", version="0.1.0", lifespan=lifespan)

# --- Routers ---
app.include_router(auth_router)
app.include_router(pages_router)
app.include_router(quest_router)
app.include_router(admin_router)
app.include_router(tutor_router)


@app.get("/health")
def health():
    return {"ok": True}