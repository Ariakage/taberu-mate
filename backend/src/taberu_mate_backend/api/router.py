from fastapi import APIRouter

from taberu_mate_backend.api.routes import ai, health, menus, users

api_router = APIRouter()
api_router.include_router(ai.router)
api_router.include_router(health.router)
api_router.include_router(menus.router)
api_router.include_router(users.router)
