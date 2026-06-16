from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute

from core.config import settings
from files.route import router as files_router
from streams.route import router as streams_router
from torrents.route import api_router, dashboard_router
from users.dependencies import NotAuthenticatedException
from users.route import auth_router


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    """Simplify operation IDs so that generated API clients have simpler function names."""
    for route in app.routes:
        if isinstance(route, APIRoute) and route.name:
            route.operation_id = route.name


app = FastAPI(
    title="Bauxite",
    description="An open-source seedbox built with ease of use in mind.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.exception_handler(NotAuthenticatedException)
async def auth_exception_handler(
    request: Request, exc: NotAuthenticatedException
) -> RedirectResponse:
    return RedirectResponse(url="/auth", status_code=302)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.origin_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=86400,
)

app.include_router(auth_router)
app.include_router(files_router, tags=["files"])
app.include_router(streams_router, tags=["streams"])
app.include_router(api_router, tags=["torrents"])
app.include_router(dashboard_router, tags=["dashboard"])

use_route_names_as_operation_ids(app)
