"""
HydroCore OS Backend — application entrypoint.

Responsible only for: creating the FastAPI app, wiring middleware,
registering routers, and startup/shutdown lifecycle. No business logic.
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.infrastructure.mqtt.bootstrap import start_mqtt_listener

# Configure logging at startup before module initialization
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start MQTT background consumer task on startup
    mqtt_task = asyncio.create_task(start_mqtt_listener())
    yield
    # Cancel MQTT consumer task on shutdown
    mqtt_task.cancel()
    try:
        await mqtt_task
    except asyncio.CancelledError:
        pass


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