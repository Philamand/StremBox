from fastapi import FastAPI

from routers.streams import router
from routers.torrents import router as torrents_router

app = FastAPI()

app.include_router(router, prefix="/streams")
app.include_router(torrents_router, prefix="/torrents")
