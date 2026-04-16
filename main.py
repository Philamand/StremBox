from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import lifespan
from routers import stremio, users

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stremio.router)
app.include_router(users.router)
