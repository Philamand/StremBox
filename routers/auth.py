from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import HANKO_URL
from fastapi import APIRouter, Request
from utils.jinja_filters import register_filters

auth_router = APIRouter(prefix="/auth")
templates = Jinja2Templates(directory="templates")
register_filters(templates.env)


@auth_router.get("")
async def auth(request: Request) -> HTMLResponse:
    """Render the authentication page."""
    return templates.TemplateResponse(request, "auth.html", {"hanko_url": HANKO_URL})
