"""Aggregates all v1 routers. Each business domain adds its router here."""

from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router)
