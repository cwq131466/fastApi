from fastapi import APIRouter, Query, HTTPException, Depends
from app.controllers.script import script_category_controller, script_controller
from app.schemas.base import Success, Fail
from app.schemas.scripts import ScriptCategoryCreate, ScriptCategoryUpdate
from app.core.dependency import AuthControl
from app.models.admin import User

router = APIRouter()


async def check_category_admin_permission(current_user: User):
    """
    检查用户是否有管理分类的权限
    只有超级管理员或管理员角色可以操作
    """
    if current_user.is_superuser:
        return True
    
    roles = await current_user.roles
    has_admin_role = any(role.name == "管理员" for role in roles)
    
    if not has_admin_role:
        raise HTTPException(
            status_code=403, 
            detail="您没有权限执行此操作，需要管理员角色"
        )
    
    return True


@router.get("/tree", summary="获取分类树")
async def get_category_tree():
    """获取启用的分类树形结构"""
    tree = await script_category_controller.get_tree()
    return Success(data=tree)


@router.get("/list", summary="获取分类列表")
async def list_categories(
    page: int = Query(1, description="页码"),
    page_size: int = Query(100, description="每页数量"),
):
    """获取所有分类（含禁用的，用于管理）"""
    total, objs = await script_category_controller.list(page=page, page_size=page_size)
    data = [await obj.to_dict() for obj in objs]
    return Success(data=data, total=total, page=page, page_size=page_size)


@router.post("/create", summary="创建分类")
async def create_category(
    category_in: ScriptCategoryCreate,
    current_user: User = Depends(AuthControl.is_authed),
):
    # 权限检查
    await check_category_admin_permission(current_user)
    
    # 验证父分类是否存在（如果 parent_id != 0）
    if category_in.parent_id != 0:
        parent_exists = await script_category_controller.model.filter(id=category_in.parent_id).exists()
        if not parent_exists:
            return Fail(msg="指定的父分类不存在")
    
    new_obj = await script_category_controller.create(obj_in=category_in)
    return Success(data=await new_obj.to_dict(), msg="创建成功")


@router.post("/update", summary="更新分类")
async def update_category(
    category_in: ScriptCategoryUpdate,
    current_user: User = Depends(AuthControl.is_authed),
):
    # 权限检查
    await check_category_admin_permission(current_user)
    
    try:
        obj = await script_category_controller.update(id=category_in.id, obj_in=category_in)
        return Success(data=await obj.to_dict(), msg="更新成功")
    except ValueError as e:
        return Fail(msg=str(e))


@router.delete("/delete", summary="删除分类")
async def delete_category(
    category_id: int = Query(..., description="分类ID"),
    current_user: User = Depends(AuthControl.is_authed),
):
    # 权限检查
    await check_category_admin_permission(current_user)
    
    try:
        await script_category_controller.remove(id=category_id)
        return Success(msg="删除成功")
    except ValueError as e:
        return Fail(msg=str(e))
