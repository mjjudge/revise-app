import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import init_db
from app.db.seed import seed_users
from app.api.auth import router as auth_router
from app.api.pages import router as pages_router
from app.api.quest import router as quest_router
from app.api.admin import router as admin_router
from app.api.tutor import router as tutor_router
from app.templates.feed_loader import load_and_validate

# Configure structured logging before anything else
setup_logging(env=settings.app_env)
logger = logging.getLogger(__name__)

_error_templates = Jinja2Templates(directory="app/templates/html")


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.monotonic()

        response = await call_next(request)

        duration_ms = round((time.monotonic() - start) * 1000, 1)
        logger.info(
            "%s %s → %s (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

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

# Static files (map images etc.)
app.mount("/images", StaticFiles(directory="app/images"), name="images")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Request logging
app.add_middleware(RequestLoggingMiddleware)


# ---------------------------------------------------------------------------
# Error handlers — themed error pages
# ---------------------------------------------------------------------------

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Themed 404 page."""
    return _error_templates.TemplateResponse(
        request, "error.html",
        {"status": 404, "title": "Page Not Found",
         "message": "The quest you seek does not exist in this realm.",
         "emoji": "🗺️"},
        status_code=404,
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Themed 500 page."""
    logger.error("Internal server error on %s %s", request.method, request.url.path, exc_info=exc)
    return _error_templates.TemplateResponse(
        request, "error.html",
        {"status": 500, "title": "Server Error",
         "message": "A dragon has disrupted the magical servers. Please try again!",
         "emoji": "🐉"},
        status_code=500,
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, exc):
    """Themed 403 page."""
    return _error_templates.TemplateResponse(
        request, "error.html",
        {"status": 403, "title": "Access Denied",
         "message": "You do not have the enchantment required to enter this area.",
         "emoji": "🔒"},
        status_code=403,
    )


# --- Routers ---
app.include_router(auth_router)
app.include_router(pages_router)
app.include_router(quest_router)
app.include_router(admin_router)
app.include_router(tutor_router)


@app.get("/health")
def health():
    return {"ok": True}