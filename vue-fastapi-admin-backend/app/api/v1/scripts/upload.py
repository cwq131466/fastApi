"""
脚本文件上传接口
支持按文件类型分类存储，支持关联到具体脚本
"""
import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Body
from loguru import logger

from app.models.admin import Script, UploadedFile
from app.schemas.base import Success, Fail
from app.settings.config import settings

router = APIRouter()

# 文件扩展名映射到目标目录
FILE_TYPE_MAPPING = {
    # 代码文件 -> code 目录
    '.sh': 'code/shell',
    '.py': 'code/python',
    '.js': 'code/node',
    # 软件包 -> soft 目录
    '.tar': 'soft/tar',
    '.tar.gz': 'soft/tar',
    '.tgz': 'soft/tar',
    '.run': 'soft/run',
    '.rpm': 'soft/rpm',
    '.deb': 'soft/deb',
    '.bin': 'soft/bin',
}

# 获取项目根目录下的 uploads 文件夹（uploads 在 vue-fastapi-admin-main 根目录）
UPLOAD_BASE_DIR = Path(settings.BASE_DIR).parent / "uploads"


def get_target_directory(file_extension: str) -> Path:
    """
    根据文件扩展名获取目标目录
    
    Args:
        file_extension: 文件扩展名（如 .sh, .py）
        
    Returns:
        目标目录路径
    """
    ext = file_extension.lower()
    # 处理 .tar.gz 这种复合扩展名
    if ext == '.gz':
        ext = '.tar.gz'
    
    target_subdir = FILE_TYPE_MAPPING.get(ext)
    if not target_subdir:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}。支持的类型: {', '.join(FILE_TYPE_MAPPING.keys())}"
        )
    
    target_dir = UPLOAD_BASE_DIR / target_subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


@router.post("/upload", summary="上传脚本文件")
async def upload_script_file(
    file: UploadFile = File(..., description="要上传的文件"),
    custom_filename: str = Form("", description="自定义文件名（可选，为空则使用原文件名）"),
    display_name: str = Form("", description="显示名称/关联文件名（可选，为空则使用原文件名）"),
    script_id: Optional[int] = Form(None, description="关联的脚本ID（可选）"),
):
    """
    上传脚本文件，根据文件扩展名自动分类存储
    
    存储规则：
    - sh, py, js -> uploads/code/{shell,python,node}/
    - tar, run, rpm, deb, bin -> uploads/soft/{tar,run,rpm,deb,bin}/
    
    最大文件大小：500MB
    
    如果提供 script_id，文件将关联到该脚本，并在脚本记录中保存文件路径
    
    display_name 规则：
    - 如果 display_name 为空，则使用 original_filename 作为显示名称
    - 如果 display_name 有值，则使用该值作为显示名称
    """
    try:
        # 验证文件是否存在
        if not file.filename:
            raise HTTPException(status_code=400, detail="未选择文件")
        
        # 读取文件内容（支持大文件，最大500MB）
        content = await file.read()
        if len(content) > 500 * 1024 * 1024:  # 500MB
            raise HTTPException(status_code=413, detail="文件大小超过限制（500MB）")
        
        # 获取文件扩展名
        original_filename = file.filename
        
        # 处理复合扩展名（如 .tar.gz）
        if original_filename.lower().endswith('.tar.gz'):
            file_ext = '.tar.gz'
        else:
            file_ext = Path(original_filename).suffix.lower()
        
        # 获取目标目录
        target_dir = get_target_directory(file_ext)
        
        # 确定最终文件名（用于实际存储）
        if custom_filename and custom_filename.strip():
            # 使用自定义文件名，保留原扩展名
            final_filename = f"{custom_filename.strip()}{file_ext}"
        else:
            # 使用原文件名
            final_filename = original_filename
        
        # 构建完整文件路径
        file_path = target_dir / final_filename
        
        # 如果文件已存在，添加数字后缀
        counter = 1
        while file_path.exists():
            name_without_ext = Path(final_filename).stem
            file_path = target_dir / f"{name_without_ext}_{counter}{file_ext}"
            counter += 1
        
        # 保存文件（使用已读取的内容）
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # 计算相对路径（用于存储到数据库）
        relative_path = str(file_path.relative_to(UPLOAD_BASE_DIR))
        
        # 获取文件大小
        file_size = file_path.stat().st_size
        
        # 确定显示名称：如果 display_name 为空，则使用原文件名
        final_display_name = display_name.strip() if display_name and display_name.strip() else original_filename
        
        logger.info(f"文件上传成功: {original_filename} -> {relative_path}, display_name: {final_display_name}")
        
        # 创建文件元数据记录
        uploaded_file = await UploadedFile.create(
            filename=final_filename,
            original_filename=original_filename,
            display_name=final_display_name,
            file_path=relative_path,
            file_size=file_size,
            file_type=file_ext,
            script_id=script_id,
        )
        
        associated_script = None
        if script_id is not None:
            try:
                script_obj = await Script.get(id=script_id)
                associated_script = {
                    "script_id": script_id,
                    "script_title": script_obj.title
                }
                logger.info(f"文件已关联到脚本 ID={script_id}: {script_obj.title}")
            except Exception as e:
                logger.warning(f"无法关联文件到脚本 ID={script_id}: {str(e)}")
        
        return Success(
            data={
                "id": uploaded_file.id,
                "filename": final_filename,
                "original_filename": original_filename,
                "display_name": final_display_name,
                "file_path": relative_path,
                "full_path": str(file_path),
                "file_size": file_size,
                "file_type": file_ext,
                "script": associated_script,
                "created_at": uploaded_file.created_at.isoformat() if uploaded_file.created_at else None,
            },
            msg="文件上传成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/delete", summary="删除上传的文件")
async def delete_script_file(
    file_path: str = Body(..., embed=True, description="文件相对路径"),
    script_id: Optional[int] = Body(None, embed=True, description="关联的脚本ID（可选）"),
):
    """
    删除已上传的文件
    
    Args:
        file_path: 文件的相对路径（相对于 uploads 目录）
        script_id: 关联的脚本ID（可选）
    """
    try:
        full_path = UPLOAD_BASE_DIR / file_path
        
        # 安全检查：确保文件在 uploads 目录内
        if not str(full_path).startswith(str(UPLOAD_BASE_DIR)):
            raise HTTPException(status_code=400, detail="非法的文件路径")
        
        if not full_path.exists():
            return Fail(msg="文件不存在")
        
        # 删除数据库记录
        try:
            uploaded_file = await UploadedFile.get(file_path=file_path)
            await uploaded_file.delete()
            logger.info(f"已删除文件元数据记录: {file_path}")
        except UploadedFile.DoesNotExist:
            logger.warning(f"未找到文件元数据记录: {file_path}")
        
        # 删除物理文件
        full_path.unlink()
        logger.info(f"文件删除成功: {file_path}")
        
        return Success(msg="文件删除成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件删除失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件删除失败: {str(e)}")


@router.post("/update-display-name", summary="更新文件显示名称")
async def update_file_display_name(
    file_id: int = Body(..., embed=True, description="文件ID"),
    display_name: str = Body(..., embed=True, description="新的显示名称"),
):
    """
    更新文件的显示名称（关联文件名）
    
    Args:
        file_id: 文件ID
        display_name: 新的显示名称
    """
    try:
        uploaded_file = await UploadedFile.get(id=file_id)
        uploaded_file.display_name = display_name.strip() if display_name.strip() else uploaded_file.original_filename
        await uploaded_file.save()
        
        logger.info(f"文件显示名称已更新: ID={file_id}, display_name={uploaded_file.display_name}")
        
        return Success(data={"display_name": uploaded_file.display_name}, msg="更新成功")
        
    except UploadedFile.DoesNotExist:
        return Fail(msg="文件不存在")
    except Exception as e:
        logger.error(f"更新显示名称失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.get("/list", summary="列出指定目录下的文件")
async def list_uploaded_files(
    category: str = Form("code", description="文件类别: code 或 soft"),
    subcategory: str = Form("", description="子类别: shell/python/node 或 tar/run/rpm/deb/bin"),
):
    """
    列出指定目录下的已上传文件
    """
    try:
        if category == "code":
            valid_subcats = ["shell", "python", "node"]
        elif category == "soft":
            valid_subcats = ["tar", "run", "rpm", "deb", "bin"]
        else:
            raise HTTPException(status_code=400, detail="无效的类别")
        
        if subcategory and subcategory not in valid_subcats:
            raise HTTPException(status_code=400, detail=f"无效的子类别: {subcategory}")
        
        target_dir = UPLOAD_BASE_DIR / category
        if subcategory:
            target_dir = target_dir / subcategory
        
        if not target_dir.exists():
            return Success(data=[], msg="目录为空")
        
        files = []
        for file_path in target_dir.iterdir():
            if file_path.is_file():
                files.append({
                    "filename": file_path.name,
                    "file_path": str(file_path.relative_to(UPLOAD_BASE_DIR)),
                    "file_size": file_path.stat().st_size,
                    "file_ext": file_path.suffix,
                })
        
        return Success(data=files)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"列出文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"列出文件失败: {str(e)}")


@router.get("/script-files", summary="获取脚本关联的文件列表")
async def get_script_files(script_id: int):
    """
    获取指定脚本关联的所有文件（包含详细元数据）
    
    Args:
        script_id: 脚本ID
    """
    try:
        # 验证脚本是否存在
        script = await Script.get(id=script_id)
        
        # 查询关联的文件
        files = await UploadedFile.filter(script_id=script_id, is_active=True).all()
        
        result = []
        for f in files:
            result.append({
                "id": f.id,
                "filename": f.filename,
                "original_filename": f.original_filename,
                "display_name": f.display_name or f.original_filename,
                "file_path": f.file_path,
                "file_size": f.file_size,
                "file_type": f.file_type,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            })
        
        return Success(data=result)
        
    except Script.DoesNotExist:
        return Fail(msg="脚本不存在")
    except Exception as e:
        logger.error(f"获取脚本文件列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")
