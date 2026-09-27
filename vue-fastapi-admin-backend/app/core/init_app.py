import shutil
#Aerich 是 Tortoise-ORM 官方推荐的迁移工具，专门用来管理和同步数据库表结构
from aerich import Command
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from tortoise.expressions import Q

from app.api import api_router
from app.controllers.api import api_controller
from app.controllers.user import UserCreate, user_controller
from app.core.exceptions import (
    DoesNotExist,
    DoesNotExistHandle,
    HTTPException,
    HttpExcHandle,
    IntegrityError,
    IntegrityHandle,
    RequestValidationError,
    RequestValidationHandle,
    ResponseValidationError,
    ResponseValidationHandle,
)
from app.log import logger
from app.models.admin import Api, Menu, Role, ScriptCategory
from app.schemas.menus import MenuType
from app.settings.config import settings

from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware


def make_middlewares():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
        ),
        Middleware(BackGroundTaskMiddleware),
        Middleware(
            HttpAuditLogMiddleware,
            methods=["GET", "POST", "PUT", "DELETE"],
            exclude_paths=[
                "/api/v1/base/access_token",
                "/api/v1/auth/oauth2/login",  # OAuth2登录（重定向）
                "/api/v1/auth/oauth2/callback",  # OAuth2回调（重定向）
                "/docs",
                "/openapi.json",
            ],
        ),
        # Session中间件（用于OAuth2 state存储）
        Middleware(
            SessionMiddleware,
            secret_key=settings.SECRET_KEY,
            max_age=3600,  # session过期时间：1小时
            https_only=False,
        ),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    app.add_exception_handler(HTTPException, HttpExcHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)


def register_routers(app: FastAPI, prefix: str = "/api"):
    app.include_router(api_router, prefix=prefix)


async def init_superuser():
    user = await user_controller.model.exists()
    if not user:
        await user_controller.create_user(
            UserCreate(
                username="admin",
                email="admin@admin.com",
                password="123456",
                is_active=True,
                is_superuser=True,
            )
        )


async def init_menus():
    menus = await Menu.exists()
    if not menus:
        parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )
        children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="用户管理",
                path="user",
                order=1,
                parent_id=parent_menu.id,
                icon="material-symbols:person-outline-rounded",
                is_hidden=False,
                component="/system/user",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="角色管理",
                path="role",
                order=2,
                parent_id=parent_menu.id,
                icon="carbon:user-role",
                is_hidden=False,
                component="/system/role",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="菜单管理",
                path="menu",
                order=3,
                parent_id=parent_menu.id,
                icon="material-symbols:list-alt-outline",
                is_hidden=False,
                component="/system/menu",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="API管理",
                path="api",
                order=4,
                parent_id=parent_menu.id,
                icon="ant-design:api-outlined",
                is_hidden=False,
                component="/system/api",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="部门管理",
                path="dept",
                order=5,
                parent_id=parent_menu.id,
                icon="mingcute:department-line",
                is_hidden=False,
                component="/system/dept",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="审计日志",
                path="auditlog",
                order=6,
                parent_id=parent_menu.id,
                icon="ph:clipboard-text-bold",
                is_hidden=False,
                component="/system/auditlog",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(children_menu)
        await Menu.create(
            menu_type=MenuType.MENU,
            name="一级菜单",
            path="/top-menu",
            order=2,
            parent_id=0,
            icon="material-symbols:featured-play-list-outline",
            is_hidden=False,
            component="/top-menu",
            keepalive=False,
            redirect="",
        )


async def init_apis():
    apis = await api_controller.model.exists()
    if not apis:
        await api_controller.refresh_api()


async def init_db():
    # 临时禁用 aerich 自动迁移，因为手动完成了数据库迁移
    # 1. 创建 Aerich 命令对象，使用配置文件中的 Tortoise ORM 配置
    command = Command(tortoise_config=settings.TORTOISE_ORM)

    # 2. 尝试初始化数据库（创建数据库和基础表）
    try:
        await command.init_db(safe=True)
    except FileExistsError:
        # 数据库已存在，忽略错误继续
        pass

    # 3. 初始化 Aerich（设置迁移环境）
    await command.init()

    # 4. 跳过自动生成迁移和执行迁移，因为已经手动完成
    # try:
    #     await command.migrate()
    # except AttributeError:
    #     logger.warning("无法从数据库获取模型历史，将从头创建迁移历史")
    #     shutil.rmtree("migrations")
    #     await command.init_db(safe=True)

    # 5. 跳过执行迁移
    # await command.upgrade(run_in_transaction=True)
    logger.info("Skipping aerich migrations (manually migrated)")


async def migrate_script_permissions():
    """为脚本表添加权限字段"""
    from tortoise import Tortoise
    
    try:
        db = Tortoise.get_connection("default")
        
        # 检查当前表结构
        table_info = await db.execute_query_dict("PRAGMA table_info(script)")
        existing_columns = [col['name'] for col in table_info]
        
        # 检查并添加 created_by 字段
        if 'created_by' not in existing_columns:
            try:
                await db.execute_query("ALTER TABLE script ADD COLUMN created_by INTEGER")
                logger.info("✅ 添加 created_by 字段成功")
            except Exception as e:
                logger.warning(f"添加 created_by 字段失败: {e}")
        else:
            logger.info("created_by 字段已存在")
        
        # 检查并添加 viewer_roles 字段
        if 'viewer_roles' not in existing_columns:
            try:
                # SQLite中JSON类型实际存储为TEXT
                await db.execute_query("ALTER TABLE script ADD COLUMN viewer_roles TEXT DEFAULT '[]'")
                logger.info("✅ 添加 viewer_roles 字段成功")
            except Exception as e:
                logger.warning(f"添加 viewer_roles 字段失败: {e}")
        else:
            logger.info("viewer_roles 字段已存在")
                
    except Exception as e:
        logger.warning(f"⚠️ 脚本权限字段迁移跳过: {e}")


async def init_roles():
    roles = await Role.exists()
    if not roles:
        admin_role = await Role.create(
            name="管理员",
            desc="管理员角色",
        )
        user_role = await Role.create(
            name="普通用户",
            desc="普通用户角色",
        )

        # 分配所有API给管理员角色
        all_apis = await Api.all()
        await admin_role.apis.add(*all_apis)
        # 分配所有菜单给管理员和普通用户
        all_menus = await Menu.all()
        await admin_role.menus.add(*all_menus)
        await user_role.menus.add(*all_menus)

        # 为普通用户分配基本API
        basic_apis = await Api.filter(Q(method__in=["GET"]) | Q(tags="基础模块"))
        await user_role.apis.add(*basic_apis)


async def init_script_categories():
    """初始化运维脚本分类"""
    try:
        # 先检查表是否存在
        from tortoise import Tortoise
        
        # 获取数据库连接
        conn = Tortoise.get_connection("default")
        
        # 检查表是否存在
        tables = await conn.execute_query_dict("SELECT name FROM sqlite_master WHERE type='table' AND name='script_category';")
        
        if not tables:
            logger.warning("⚠️ script_category 表不存在，跳过初始化")
            return
            
        count = await ScriptCategory.all().count()
        if count > 0:
            return

        categories = [
            {"name": "环境配置", "parent_id": 0, "order": 1},
            {"name": "日常运维", "parent_id": 0, "order": 2},
            {"name": "PKG软件包", "parent_id": 0, "order": 3},
            {"name": "shell脚本", "parent_id": 0, "order": 4},
            {"name": "Python脚本", "parent_id": 0, "order": 5},
            {"name": "docker应用", "parent_id": 0, "order": 6},
        ]

        for cat_data in categories:
            await ScriptCategory.create(**cat_data)

        logger.info("✅ 运维脚本分类初始化完成")
    except Exception as e:
        logger.warning(f"⚠️ 脚本分类初始化跳过（表可能尚未创建）: {e}")


async def init_data():
    await init_db()
    await migrate_script_permissions()
    await init_superuser()
    await init_menus()
    await init_apis()
    await init_roles()
    await init_script_categories()
