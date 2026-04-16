from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from dependencies import get_user_service
from schemas.users import UserFormData
from services.users import UserService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Display the index page."""
    return templates.TemplateResponse(request=request, name="index.html")


@router.post("/")
async def create_user(
    data: Annotated[UserFormData, Form()],
    service: UserService = Depends(get_user_service),
):
    """Create a new user."""
    user_id = await service.create_user(data)
    return {"user_id": user_id}
