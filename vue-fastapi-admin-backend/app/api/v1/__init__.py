from fastapi import APIRouter

from app.core.dependency import DependPermission, DependAuth

from .apis import apis_router
from .assets import router as assets_router
from .auditlog import auditlog_router
from .auth import router as auth_router
from .base import base_router
from .depts import depts_router
from .menus import menus_router
from .roles import roles_router
from .users import users_router
from .scripts import router as scripts_router
from .scriptlogs import scriptlogs_public_router, scriptlogs_auth_router
from .blog import blog_router
from .blog.upload import router as blog_upload_router

v1_router = APIRouter()

# 注册OAuth2认证路由（无需认证依赖）
# 最终路径: /api/v1/auth/oauth2/login, /api/v1/auth/oauth2/callback
v1_router.include_router(auth_router, prefix="/auth")

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(users_router, prefix="/user", dependencies=[DependPermission])
v1_router.include_router(roles_router, prefix="/role", dependencies=[DependPermission])
v1_router.include_router(menus_router, prefix="/menu", dependencies=[DependPermission])
v1_router.include_router(apis_router, prefix="/api", dependencies=[DependPermission])
v1_router.include_router(depts_router, prefix="/dept", dependencies=[DependPermission])
v1_router.include_router(auditlog_router, prefix="/auditlog", dependencies=[DependPermission])

# 运维脚本路由（仅需登录认证）
v1_router.include_router(scripts_router, prefix="/script", dependencies=[DependAuth])

# 脚本执行日志路由 - 接收日志（需要 token 认证，依赖已在路由中配置）
v1_router.include_router(scriptlogs_public_router, prefix="/scriptlog", dependencies=[DependAuth])

# 脚本执行日志路由 - 查询日志（需要登录认证，依赖已在路由中配置）
v1_router.include_router(scriptlogs_auth_router, prefix="/scriptlog", dependencies=[DependPermission])

# 交换机资产管理路由（需要权限控制）
v1_router.include_router(assets_router)

# Blog模块路由（需要登录认证）
v1_router.include_router(blog_router, prefix="/blog", dependencies=[DependAuth])

# Blog图片上传路由（不使用认证依赖，在路由内部手动验证）
v1_router.include_router(blog_upload_router, prefix="/blog/upload")
