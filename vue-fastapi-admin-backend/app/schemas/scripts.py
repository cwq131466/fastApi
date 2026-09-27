from typing import Optional, List, Dict, Union, Any
from pydantic import BaseModel, Field


# === 分类 Schema ===
class BaseScriptCategory(BaseModel):
    id: int
    name: str
    parent_id: int = 0
    order: int = 0
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ScriptCategoryCreate(BaseModel):
    name: str = Field(..., description="分类名称")
    parent_id: int = Field(0, description="父分类ID")
    order: int = Field(0, description="排序")


class ScriptCategoryUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    parent_id: Optional[int] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


# === 脚本 Schema ===
class BaseScriptCategorySimple(BaseModel):
    id: int
    name: str
    parent_id: int = 0


# 步骤值可以是字符串或包含 value 和 add_name 的对象
StepValue = Union[str, Dict[str, Any]]


class BaseScript(BaseModel):
    id: int
    title: str
    category_id: int
    requirements: Optional[List[str]] = []
    steps: Dict[str, StepValue] = {}
    features: Optional[str] = ""
    reference_links: Optional[List[Dict[str, str]]] = []
    order: int = 0
    is_active: bool = True
    uploaded_files: Optional[List[str]] = []
    created_by: Optional[int] = None
    viewer_roles: Optional[List[int]] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    category: Optional[BaseScriptCategorySimple] = None


class ScriptCreate(BaseModel):
    title: str = Field(..., description="脚本标题")
    category_id: int = Field(..., description="分类ID")
    requirements: Optional[List[str]] = Field([], description="安装要求")
    steps: Dict[str, StepValue] = Field({}, description="安装步骤")
    features: Optional[str] = Field("", description="主要功能")
    reference_links: Optional[List[Dict[str, str]]] = Field([], description="参考资料")
    order: int = Field(0, description="排序")
    uploaded_files: Optional[List[str]] = Field([], description="上传的文件路径列表")
    viewer_roles: Optional[List[int]] = Field([], description="可查看的角色ID列表")


class ScriptUpdate(BaseModel):
    id: int
    title: Optional[str] = None
    category_id: Optional[int] = None
    requirements: Optional[List[str]] = None
    steps: Optional[Dict[str, StepValue]] = None
    features: Optional[str] = None
    reference_links: Optional[List[Dict[str, str]]] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None
    uploaded_files: Optional[List[str]] = None
    viewer_roles: Optional[List[int]] = None
