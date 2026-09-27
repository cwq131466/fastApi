# -*- coding: utf-8 -*-
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from tortoise import Tortoise

from app.core.exceptions import SettingNotFound
from app.core.init_app import (
    init_data,
    make_middlewares,
    register_exceptions,
    register_routers,
)

try:
    from app.settings.config import settings
except ImportError:
    raise SettingNotFound("Can not import settings")


def ensure_upload_dirs():
    """确保上传目录存在"""
    # 使用项目根目录的 uploads（向上一级到项目根目录）
    upload_base = Path(settings.BASE_DIR).parent / "uploads"
    subdirs = [
        "code/shell", "code/python", "code/node",
        "soft/tar", "soft/run", "soft/rpm", "soft/deb", "soft/bin",
        "blog",  # 博客图片上传目录
        "avatar"  # 用户头像上传目录
    ]
    for subdir in subdirs:
        (upload_base / subdir).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_upload_dirs()
    await init_data()
    yield
    await Tortoise.close_connections()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.VERSION,
        openapi_url="/openapi.json",
        middleware=make_middlewares(),
        lifespan=lifespan,
    )
    register_exceptions(app)
    register_routers(app, prefix="/api")

    # 挂载静态文件服务，用于访问上传的图片
    # 使用项目根目录的 uploads（向上一级到项目根目录）
    uploads_dir = Path(settings.BASE_DIR).parent / "uploads"
    if uploads_dir.exists():
        app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

    return app


app = create_app()
