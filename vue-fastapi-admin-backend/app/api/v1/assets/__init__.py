from fastapi import APIRouter
from .assets import router as assets_router

router = APIRouter(prefix="/assets", tags=["assets"])
router.include_router(assets_router)
