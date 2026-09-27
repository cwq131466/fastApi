from fastapi import APIRouter, Query, Depends
from app.controllers.script import script_controller
from app.models.admin import ScriptCategory, UploadedFile, User
from app.schemas.base import Success, Fail
from app.schemas.scripts import ScriptCreate, ScriptUpdate
from app.core.dependency import AuthControl
from tortoise.expressions import Q
from loguru import logger

router = APIRouter()


@router.get("/list", summary="获取脚本列表")
async def list_scripts(
    category_id: int = Query(..., description="分类ID"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    current_user: User = Depends(AuthControl.is_authed),
):
    # 构建基础查询条件
    query = script_controller.model.filter(category_id=category_id, is_active=True)
    
    # 获取所有符合条件的脚本
    total = await query.count()
    all_scripts = await query.order_by("order").prefetch_related("category")
    
    # 权限过滤：非超级管理员和非管理员需要过滤
    if not current_user.is_superuser:
        roles = await current_user.roles
        role_ids = [role.id for role in roles]
        
        logger.info(f"[Script List] 当前用户 {current_user.username} (ID={current_user.id}) 的角色IDs: {role_ids}")
        
        # 检查是否有管理员角色
        has_admin_role = any(role.name == "管理员" for role in roles)
        
        if not has_admin_role:
            # 普通用户：在Python层面进行权限过滤
            filtered_scripts = []
            for script in all_scripts:
                viewer_roles = script.viewer_roles or []
                
                # viewer_roles 为空表示对所有角色可见
                if viewer_roles == []:
                    filtered_scripts.append(script)
                # 检查用户的角色是否在 viewer_roles 中
                elif role_ids and any(rid in viewer_roles for rid in role_ids):
                    filtered_scripts.append(script)
            
            all_scripts = filtered_scripts
            logger.info(f"[Script List] 权限过滤后剩余 {len(filtered_scripts)} 条记录")
    
    # 分页处理
    total = len(all_scripts)
    start = (page - 1) * page_size
    end = start + page_size
    scripts = all_scripts[start:end]

    result = []
    for script in scripts:
        script_dict = await script.to_dict()
        if hasattr(script, 'category') and script.category:
            script_dict["category"] = await script.category.to_dict()
        
        # 添加创建者信息
        if script.created_by:
            creator = await User.filter(id=script.created_by).first()
            if creator:
                script_dict["creator_info"] = {
                    "id": creator.id,
                    "username": creator.username,
                    "alias": creator.alias
                }
        
        result.append(script_dict)

    return Success(data=result, total=total, page=page, page_size=page_size)


@router.get("/get", summary="获取脚本详情")
async def get_script(script_id: int = Query(..., description="脚本ID")):
    script_obj = await script_controller.get(id=script_id)
    script_dict = await script_obj.to_dict()
    if script_obj.category:
        script_dict["category"] = await script_obj.category.to_dict()
    
    # 获取创建者信息
    if script_obj.created_by:
        creator = await User.filter(id=script_obj.created_by).first()
        if creator:
            script_dict["creator_info"] = {
                "id": creator.id,
                "username": creator.username,
                "alias": creator.alias
            }
    
    # 获取关联的文件列表（包含详细元数据）
    files = await UploadedFile.filter(script_id=script_id, is_active=True).all()
    script_dict["uploaded_files_detail"] = [
        {
            "id": f.id,
            "filename": f.filename,
            "original_filename": f.original_filename,
            "file_path": f.file_path,
            "file_size": f.file_size,
            "file_type": f.file_type,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in files
    ]
    
    return Success(data=script_dict)


@router.post("/create", summary="创建脚本")
async def create_script(
    script_in: ScriptCreate,
    current_user: User = Depends(AuthControl.is_authed),
):
    # 验证分类是否存在
    category = await ScriptCategory.filter(id=script_in.category_id).first()
    if not category:
        return Fail(msg="分类不存在")

    # 准备创建数据，自动设置 created_by
    create_data = script_in.dict(exclude_unset=True)
    create_data['created_by'] = current_user.id
    
    new_obj = await script_controller.create(obj_in=create_data)
    
    # 处理文件关联：将上传的文件关联到新创建的脚本
    if script_in.uploaded_files:
        for file_path in script_in.uploaded_files:
            try:
                uploaded_file = await UploadedFile.get(file_path=file_path)
                uploaded_file.script_id = new_obj.id
                await uploaded_file.save()
            except UploadedFile.DoesNotExist:
                pass  # 文件不存在，忽略
    
    return Success(data=await new_obj.to_dict(), msg="创建成功")


@router.post("/update", summary="更新脚本")
async def update_script(
    script_in: ScriptUpdate,
    current_user: User = Depends(AuthControl.is_authed),
):
    # 权限检查
    obj = await script_controller.get(id=script_in.id)
    
    # 非超级管理员且非管理员，只能编辑自己的脚本
    if not current_user.is_superuser:
        roles = await current_user.roles
        has_admin_role = any(role.name == "管理员" for role in roles)
        
        if not has_admin_role and obj.created_by != current_user.id:
            return Fail(msg="您没有权限编辑此脚本", code=403)
    
    # 执行更新
    update_data = script_in.dict(exclude_unset=True)
    updated_obj = await script_controller.update(id=script_in.id, obj_in=update_data)
    
    # 处理文件关联：更新文件的 script_id
    if script_in.uploaded_files is not None:
        # 先解除当前脚本的所有文件关联
        await UploadedFile.filter(script_id=script_in.id).update(script_id=None)
        
        # 再关联新的文件列表
        for file_path in script_in.uploaded_files:
            try:
                uploaded_file = await UploadedFile.get(file_path=file_path)
                uploaded_file.script_id = script_in.id
                await uploaded_file.save()
            except UploadedFile.DoesNotExist:
                pass  # 文件不存在，忽略
    
    return Success(data=await updated_obj.to_dict(), msg="更新成功")


@router.delete("/delete", summary="删除脚本")
async def delete_script(
    id: int = Query(..., description="脚本ID"),
    current_user: User = Depends(AuthControl.is_authed),
):
    # 权限检查
    obj = await script_controller.get(id=id)
    
    if not current_user.is_superuser:
        roles = await current_user.roles
        has_admin_role = any(role.name == "管理员" for role in roles)
        
        if not has_admin_role and obj.created_by != current_user.id:
            return Fail(msg="您没有权限删除此脚本", code=403)
    
    await script_controller.remove(id=id)
    return Success(msg="删除成功")
