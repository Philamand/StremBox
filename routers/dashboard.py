from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from config import HANKO_URL
from utils.auth import get_user

dashboard_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@dashboard_router.get("/")
async def dashboard(request: Request, user: str = Depends(get_user)) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"hanko_url": HANKO_URL, "user": user},
    )
