from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from core.config import settings
from core.jinja_filters import register_filters

auth_router = APIRouter(prefix="/auth")
templates = Jinja2Templates(directory="templates")
register_filters(templates.env)


@auth_router.get("")
async def auth(request: Request) -> HTMLResponse:
    """Render the authentication page."""
    return templates.TemplateResponse(
        request, "auth.html", {"hanko_url": settings.hanko_url}
    )
