from fastapi import FastAPI

from db.database import lifespan
from routers import stremio

app = FastAPI(lifespan=lifespan)

app.include_router(stremio.router)
