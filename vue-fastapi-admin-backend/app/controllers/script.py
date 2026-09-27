from typing import List
import os
from pathlib import Path

from app.core.crud import CRUDBase
from app.models.admin import ScriptCategory, Script
from app.schemas.scripts import ScriptCategoryCreate, ScriptCategoryUpdate, ScriptCreate, ScriptUpdate
from app.settings.config import settings
from loguru import logger


class ScriptCategoryController(CRUDBase[ScriptCategory, ScriptCategoryCreate, ScriptCategoryUpdate]):
    def __init__(self):
        super().__init__(model=ScriptCategory)

    async def get_tree(self) -> List[dict]:
        """获取分类树形结构"""
        all_categories = await self.model.filter(is_active=True).order_by("order")

        # 构建映射
        category_map = {}
        for cat in all_categories:
            cat_dict = await cat.to_dict()
            cat_dict["children"] = []
            category_map[cat.id] = cat_dict

        # 组装树形结构
        tree = []
        for cat in all_categories:
            if cat.parent_id == 0:
                tree.append(category_map[cat.id])
            elif cat.parent_id in category_map:
                category_map[cat.parent_id]["children"].append(category_map[cat.id])

        return tree

    async def _get_all_descendants(self, category_id: int) -> set:
        """递归获取所有子分类ID（包括间接子分类）"""
        descendants = set()
        children = await self.model.filter(parent_id=category_id)
        
        for child in children:
            descendants.add(child.id)
            # 递归获取子分类的子分类
            sub_descendants = await self._get_all_descendants(child.id)
            descendants.update(sub_descendants)
        
        return descendants

    async def validate_parent_change(self, category_id: int, new_parent_id: int) -> bool:
        """
        验证父分类变更是否合法
        
        Args:
            category_id: 要修改的分类ID
            new_parent_id: 新的父分类ID
            
        Returns:
            True 如果变更合法
            
        Raises:
            ValueError: 如果变更不合法
        """
        # 允许设置为根分类（parent_id=0）
        if new_parent_id == 0:
            return True
        
        # 不能将自己设为自己的父分类
        if category_id == new_parent_id:
            raise ValueError("不能将分类设为自己的父分类")
        
        # 检查新父分类是否存在
        parent_exists = await self.model.filter(id=new_parent_id).exists()
        if not parent_exists:
            raise ValueError("指定的父分类不存在")
        
        # 检查新父分类是否是当前分类的后代（防止循环引用）
        descendants = await self._get_all_descendants(category_id)
        if new_parent_id in descendants:
            raise ValueError("不能将分类移到其子分类下，会造成循环引用")
        
        return True

    async def update(self, id: int, obj_in) -> ScriptCategory:
        """更新分类（重写以添加验证）"""
        # 如果尝试修改 parent_id，进行验证
        if isinstance(obj_in, dict):
            new_parent_id = obj_in.get('parent_id')
        else:
            new_parent_id = getattr(obj_in, 'parent_id', None)
        
        if new_parent_id is not None:
            await self.validate_parent_change(id, new_parent_id)
        
        # 调用父类的 update 方法
        return await super().update(id, obj_in)

    async def remove(self, id: int) -> None:
        """删除分类（重写以添加验证）"""
        # 检查是否有子分类
        children_count = await self.model.filter(parent_id=id).count()
        if children_count > 0:
            raise ValueError("该分类下存在子分类，无法删除")
        
        # 检查是否有脚本
        scripts_count = await Script.filter(category_id=id).count()
        if scripts_count > 0:
            raise ValueError("该分类下存在脚本，请先删除脚本")
        
        obj = await self.get(id=id)
        await obj.delete()


class ScriptController(CRUDBase[Script, ScriptCreate, ScriptUpdate]):
    def __init__(self):
        super().__init__(model=Script)
        self.upload_base_dir = Path(settings.BASE_DIR) / "uploads"

    async def list_by_category(self, category_id: int, page: int, page_size: int) -> tuple:
        """按分类查询脚本列表"""
        query = self.model.filter(category_id=category_id, is_active=True)
        total = await query.count()
        # 使用 prefetch_related 预加载分类信息
        scripts = await query.offset((page - 1) * page_size).limit(page_size).order_by("order").prefetch_related("category")

        result = []
        for script in scripts:
            script_dict = await script.to_dict()
            # 加载分类信息
            if hasattr(script, 'category') and script.category:
                script_dict["category"] = await script.category.to_dict()
            result.append(script_dict)

        return total, result

    async def remove(self, id: int) -> None:
        """删除脚本时级联删除关联的上传文件"""
        obj = await self.get(id=id)
        
        # 删除关联的上传文件
        try:
            # 使用正确的关系名 'files'（在 UploadedFile 模型中定义）
            uploaded_files = await obj.files.all()
            for uploaded_file in uploaded_files:
                try:
                    file_path = uploaded_file.file_path
                    full_path = self.upload_base_dir / file_path
                    # 安全检查：确保文件在 uploads 目录内
                    if str(full_path).startswith(str(self.upload_base_dir)) and full_path.exists():
                        full_path.unlink()
                        logger.info(f"级联删除文件: {file_path}")
                except Exception as e:
                    logger.warning(f"删除关联文件失败 {uploaded_file.file_path}: {str(e)}")
        except Exception as e:
            logger.warning(f"查询关联文件失败: {str(e)}")
        
        # 删除脚本记录
        await obj.delete()
        logger.info(f"脚本删除成功: ID={id}, title={obj.title}")


script_category_controller = ScriptCategoryController()
script_controller = ScriptController()
