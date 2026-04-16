from fastapi import FastAPI

from routers import stremio

app = FastAPI()

app.include_router(stremio.router)
