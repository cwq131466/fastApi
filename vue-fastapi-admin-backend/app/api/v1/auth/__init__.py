from fastapi import APIRouter

from .oauth2 import router as oauth2_router

# OAuth2路由路径: /api/v1/auth/oauth2/login, /api/v1/auth/oauth2/callback
router = APIRouter()
router.include_router(oauth2_router)
