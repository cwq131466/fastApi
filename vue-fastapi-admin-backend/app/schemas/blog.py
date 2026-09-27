from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# === 分类 Schema ===
class CategoryBase(BaseModel):
    id: int
    name: str
    slug: str
    parent_id: int = 0
    icon: Optional[str] = None
    description: Optional[str] = None
    order: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="分类名称")
    slug: str = Field(..., min_length=1, max_length=50, description="分类别名")
    parent_id: int = Field(0, description="父分类ID")
    icon: Optional[str] = Field(None, max_length=100, description="分类图标")
    description: Optional[str] = Field(None, max_length=500, description="分类描述")
    order: int = Field(0, ge=0, description="排序")


class CategoryUpdate(BaseModel):
    id: int
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    slug: Optional[str] = Field(None, min_length=1, max_length=50)
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None


# === 标签 Schema ===
class TagBase(BaseModel):
    id: int
    name: str
    slug: str
    color: Optional[str] = None
    article_count: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=30, description="标签名称")
    slug: Optional[str] = Field(None, max_length=30, description="标签别名（可选，不填则根据名称自动生成）")
    color: Optional[str] = Field(None, max_length=30, description="标签颜色")


class TagUpdate(BaseModel):
    id: int
    name: Optional[str] = Field(None, min_length=1, max_length=30)
    slug: Optional[str] = Field(None, min_length=1, max_length=30)
    color: Optional[str] = Field(None, max_length=30, description="标签颜色")
    is_active: Optional[bool] = None


# === 文章修订记录 Schema ===
class ArticleRevisionBase(BaseModel):
    id: int
    article_id: int
    editor_id: int
    editor_name: str
    title: str
    summary: Optional[str] = None
    cover: Optional[str] = None
    category_id: int
    view_roles: List[int] = []
    edit_roles: List[int] = []
    tag_ids: List[int] = []
    changes: dict = {}
    change_summary: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# === 文章 Schema ===
class ArticleBase(BaseModel):
    id: int
    title: str
    cover: Optional[str] = None
    summary: Optional[str] = None
    status: str
    category_id: int
    author_id: int
    view_roles: List[int] = []
    edit_roles: List[int] = []
    view_count: int = 0
    like_count: int = 0
    is_top: bool = False
    is_recommend: bool = False
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ArticleDetail(ArticleBase):
    content: str
    category: Optional[CategoryBase] = None
    tags: Optional[List[TagBase]] = []
    author_name: Optional[str] = None


class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="文章标题")
    cover: Optional[str] = Field(None, max_length=500, description="封面图片URL")
    summary: Optional[str] = Field(None, description="文章摘要")
    content: str = Field(..., description="文章内容(Markdown)")
    category_id: int = Field(..., description="分类ID")
    tag_ids: List[int] = Field(default=[], description="标签ID列表")
    status: str = Field("draft", description="文章状态: draft/published")
    view_roles: List[int] = Field(default=[], description="可查看的角色ID列表")
    edit_roles: List[int] = Field(default=[], description="可编辑的角色ID列表")
    is_top: bool = Field(False, description="是否置顶")
    is_recommend: bool = Field(False, description="是否推荐")


class ArticleUpdate(BaseModel):
    id: int
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    cover: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None
    status: Optional[str] = None
    view_roles: Optional[List[int]] = None
    edit_roles: Optional[List[int]] = None
    is_top: Optional[bool] = None
    is_recommend: Optional[bool] = None


# === 点赞 Schema ===
class ArticleLikeResponse(BaseModel):
    """点赞响应"""
    is_liked: bool = Field(..., description="是否已点赞")
    like_count: int = Field(..., description="点赞总数")

    class Config:
        from_attributes = True


# === 收藏 Schema ===
class ArticleFavoriteResponse(BaseModel):
    """收藏响应"""
    is_favorited: bool = Field(..., description="是否已收藏")

    class Config:
        from_attributes = True


class FavoriteArticleItem(BaseModel):
    """收藏列表中的文章项"""
    id: int
    title: str
    cover: Optional[str] = None
    summary: Optional[str] = None
    category_id: int
    author_id: int
    view_count: int = 0
    like_count: int = 0
    is_top: bool = False
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    favorited_at: Optional[datetime] = Field(None, description="收藏时间")

    class Config:
        from_attributes = True
