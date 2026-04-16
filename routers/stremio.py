from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from constants import MANIFEST
from schemas.users import UserFormData

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Display the index page."""
    return templates.TemplateResponse(request=request, name="index.html")


@router.post("/")
async def create_user(data: Annotated[UserFormData, Form()]):
    """Create a new user."""
    return data


@router.get("/manifest.json")
async def get_manifest():
    """Return the manifest.json file."""
    return MANIFEST
