from fastapi import APIRouter

from .scriptlogs import public_router, auth_router

# 公开路由（接收日志，无需认证）
scriptlogs_public_router = APIRouter()
scriptlogs_public_router.include_router(public_router, tags=["脚本执行日志-公开"])

# 需要认证的路由（查询日志）
scriptlogs_auth_router = APIRouter()
scriptlogs_auth_router.include_router(auth_router, tags=["脚本执行日志-认证"])

__all__ = ["scriptlogs_public_router", "scriptlogs_auth_router"]
