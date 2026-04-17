from fastapi import FastAPI

from routers.streams import router

app = FastAPI()

app.include_router(router, prefix="/streams")
