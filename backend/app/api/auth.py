"""Auth API routes — login / logout."""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.db.session import get_session
from app.services.auth import authenticate, create_session_cookie, clear_session_cookie

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    request: Request,
    display_name: str = Form(...),
    pin: str = Form(...),
    session: Session = Depends(get_session),
):
    """Verify PIN and set session cookie, then redirect."""
    user = authenticate(session, display_name, pin)
    if not user:
        # Redirect back to login with error flag
        return RedirectResponse(url="/login?error=1", status_code=303)

    # Redirect based on role
    target = "/admin" if user.role.value == "admin" else "/"
    response = RedirectResponse(url=target, status_code=303)
    create_session_cookie(response, user)
    return response


@router.get("/logout")
def logout():
    """Clear session and redirect to login."""
    response = RedirectResponse(url="/login", status_code=303)
    clear_session_cookie(response)
    return response
