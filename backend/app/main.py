from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.api_router import api_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="RainScope API",
        version="0.2.0",
        description="ECMWF IFS/AIFS precipitation forecast API",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:4200"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix="/api")
    return application


app = create_app()
