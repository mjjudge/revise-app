from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db.session import init_db
from app.db.seed import seed_users
from app.api.auth import router as auth_router
from app.api.pages import router as pages_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables + seed default users."""
    init_db()
    seed_users()
    yield


app = FastAPI(title="Revise App", version="0.1.0", lifespan=lifespan)

# --- Routers ---
app.include_router(auth_router)
app.include_router(pages_router)


@app.get("/health")
def health():
    return {"ok": True}