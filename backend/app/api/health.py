"""
Health check endpoint.

Used by Docker healthchecks, load balancers, and monitoring — must stay
dependency-free and fast (no DB/MQTT calls in v1; deep health checks
come once those modules exist).
"""
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "hydrocore-backend"}
