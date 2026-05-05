from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute

from fastapi import FastAPI
from routers.auth import auth_router
from routers.dashboard import dashboard_router
from routers.files import router as files_router
from routers.streams import router
from utils.auth import NotAuthenticatedException


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    """
    Sets the operation_id of each APIRoute to the route's name.
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name


app = FastAPI()


@app.exception_handler(NotAuthenticatedException)
async def auth_exception_handler(request, exc):
    return RedirectResponse(url="/auth", status_code=302)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(files_router)
app.include_router(dashboard_router)
app.include_router(auth_router)

use_route_names_as_operation_ids(app)
