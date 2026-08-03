"""
HydroCore OS Backend — application entrypoint.

Responsible only for: creating the FastAPI app, wiring middleware,
registering routers, and startup/shutdown lifecycle. No business logic.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.core.config import get_settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    # Future: open DB pool, connect MQTT client here
    yield
    # Future: close DB pool, disconnect MQTT client here


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="HydroCore OS API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)

    return app


app = create_app()
