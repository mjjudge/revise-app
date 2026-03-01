"""Page routes — serve HTML via Jinja2 templates."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from app.db.session import get_session
from app.services.auth import get_current_user, greeting
from app.models.user import Role

router = APIRouter(tags=["pages"])

templates = Jinja2Templates(directory="app/templates/html")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: int = 0):
    """Show the login / user-select page."""
    return templates.TemplateResponse(request, "login.html", {
        "error": bool(error),
    })


@router.get("/", response_class=HTMLResponse)
def home_page(request: Request, session: Session = Depends(get_session)):
    """Child's home page — quest launcher."""
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(request, "home.html", {
        "user": user,
        "greeting": greeting(),
    })


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, session: Session = Depends(get_session)):
    """Admin dashboard — progress + reward controls."""
    user = get_current_user(request, session)
    if not user or user.role != Role.admin:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(request, "admin.html", {
        "user": user,
    })
