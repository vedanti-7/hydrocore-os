"""
Shared API test fixtures.

The client drives the ASGI app in-process via httpx's ASGITransport — no
network, no uvicorn. ASGITransport deliberately does not run the app's
lifespan, which keeps the MQTT background consumer out of the test run while
still exercising the real routers, dependencies, repositories and Postgres.
"""
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.infrastructure.database.session import engine
from app.main import create_app


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_between_tests():
    """
    Drop the connection pool after every test.

    The engine is a module-level singleton created at import time, which is
    right for a server process (one process, one event loop, one pool). But
    pytest-asyncio runs each test in a NEW event loop, and an asyncpg
    connection is bound to the loop that opened it. Without this, test 2
    checks out test 1's connections and asyncpg raises
    "another operation is in progress".
    """
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
