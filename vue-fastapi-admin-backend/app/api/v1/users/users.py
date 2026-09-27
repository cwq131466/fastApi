import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Body, Query, File, UploadFile, HTTPException, Request
from tortoise.expressions import Q

from app.controllers.dept import dept_controller
from app.controllers.user import user_controller
from app.core.dependency import AuthControl
from app.core.ctx import CTX_USER_ID
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.users import *
from app.settings.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# 头像上传配置 - 使用项目根目录的 uploads/avatar
PROJECT_ROOT = Path(settings.BASE_DIR).parent
AVATAR_UPLOAD_DIR = PROJECT_ROOT / "uploads" / "avatar"
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB


@router.get("/list", summary="查看用户列表")
async def list_user(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    username: str = Query("", description="用户名称，用于搜索"),
    email: str = Query("", description="邮箱地址"),
    dept_id: int = Query(None, description="部门ID"),
):
    q = Q()
    if username:
        q &= Q(username__contains=username)
    if email:
        q &= Q(email__contains=email)
    if dept_id is not None:
        q &= Q(dept_id=dept_id)
    total, user_objs = await user_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict(m2m=True, exclude_fields=["password"]) for obj in user_objs]
    for item in data:
        dept_id = item.pop("dept_id", None)
        item["dept"] = await (await dept_controller.get(id=dept_id)).to_dict() if dept_id else {}

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看用户")
async def get_user(
    user_id: int = Query(..., description="用户ID"),
):
    user_obj = await user_controller.get(id=user_id)
    user_dict = await user_obj.to_dict(exclude_fields=["password"])
    return Success(data=user_dict)


@router.post("/create", summary="创建用户")
async def create_user(
    user_in: UserCreate,
):
    user = await user_controller.get_by_email(user_in.email)
    if user:
        return Fail(code=400, msg="The user with this email already exists in the system.")
    new_user = await user_controller.create_user(obj_in=user_in)
    await user_controller.update_roles(new_user, user_in.role_ids)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新用户")
async def update_user(
    user_in: UserUpdate,
):
    user = await user_controller.update(id=user_in.id, obj_in=user_in)
    await user_controller.update_roles(user, user_in.role_ids)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除用户")
async def delete_user(
    user_id: int = Query(..., description="用户ID"),
):
    await user_controller.remove(id=user_id)
    return Success(msg="Deleted Successfully")


@router.post("/reset_password", summary="重置密码")
async def reset_password(user_id: int = Body(..., description="用户ID", embed=True)):
    await user_controller.reset_password(user_id)
    return Success(msg="密码已重置为123456")


@router.post("/avatar", summary="上传用户头像")
async def upload_avatar(request: Request, file: UploadFile = File(...)):
    """
    上传用户头像
    
    - 支持格式: JPEG, PNG, GIF, WEBP
    - 文件大小限制: 2MB
    - 自动生成唯一文件名
    - 保存到 uploads/avatar/ 目录
    """
    try:
        # 身份验证
        token = request.headers.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="未提供认证令牌")
        
        await AuthControl.is_authed(token)
        
        # 获取当前用户 ID
        user_id = CTX_USER_ID.get()
        
        # 验证文件
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="未选择文件")
        
        # 验证文件类型（MIME type）
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {file.content_type}。仅支持 JPG/PNG/GIF/WEBP"
            )
        
        # 验证文件扩展名（双重保险）
        ext = Path(file.filename).suffix.lower()
        allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件扩展名: {ext}"
            )
        
        # 读取文件并检查大小
        content = await file.read()
        if len(content) > MAX_AVATAR_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制 (最大 {MAX_AVATAR_SIZE // (1024*1024)}MB)"
            )
        
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = AVATAR_UPLOAD_DIR / unique_filename
        
        # 确保目录存在
        AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 更新数据库中的用户头像
        avatar_url = f"/uploads/avatar/{unique_filename}"
        await user_controller.model.filter(id=user_id).update(avatar=avatar_url)
        
        logger.info(f"用户 {user_id} 上传头像成功: {avatar_url}")
        
        return Success(data={"url": avatar_url}, msg="头像上传成功")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"头像上传失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
