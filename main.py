from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from routers.dashboard import dashboard_router
from routers.streams import router
from routers.torrents import router as torrents_router


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    """
    Sets the operation_id of each APIRoute to the route's name.
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/streams")
app.include_router(torrents_router, prefix="/torrents")
app.include_router(dashboard_router)

use_route_names_as_operation_ids(app)
