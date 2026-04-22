from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.streams import router
from routers.torrents import router as torrents_router

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
