from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from granian.utils.proxies import wrap_asgi_with_proxy_headers

from files.route import router as files_router
from streams.route import router
from torrents.route import api_router, dashboard_router
from users.dependencies import NotAuthenticatedException
from users.route import auth_router


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    """
    Sets the operation_id of each APIRoute to the route's name.
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name


app = FastAPI()

app = wrap_asgi_with_proxy_headers(app, trusted_hosts="caddy")


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
app.include_router(api_router)
app.include_router(dashboard_router)
app.include_router(auth_router)

use_route_names_as_operation_ids(app)
