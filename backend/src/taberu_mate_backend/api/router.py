from fastapi import APIRouter

from taberu_mate_backend.api.routes import health, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(users.router)
