from fastapi import APIRouter
from app.core.dependency import DependAuth

from .categories import router as categories_router
from .scripts import router as scripts_router
from .upload import router as upload_router

# 创建主路由，直接添加依赖
router = APIRouter(dependencies=[DependAuth])

# 注册分类路由（路径会是 /script/category/xxx）
router.include_router(categories_router, prefix="/category", tags=["脚本分类"])

# 注册脚本路由（路径会是 /script/xxx）
router.include_router(scripts_router, tags=["脚本管理"])

# 注册文件上传路由（路径会是 /script/upload/xxx）
router.include_router(upload_router, prefix="/upload", tags=["文件上传"])

__all__ = ["router"]
