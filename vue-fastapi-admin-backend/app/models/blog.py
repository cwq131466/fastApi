from tortoise import fields

from .base import BaseModel, TimestampMixin


class Category(BaseModel, TimestampMixin):
    """文章分类 - 支持树形结构"""
    name = fields.CharField(max_length=50, description="分类名称", index=True)
    slug = fields.CharField(max_length=50, unique=True, description="分类别名", index=True)
    parent_id = fields.IntField(default=0, description="父分类ID", index=True)
    icon = fields.CharField(max_length=100, null=True, description="分类图标")
    description = fields.CharField(max_length=500, null=True, description="分类描述")
    order = fields.IntField(default=0, description="排序", index=True)
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:
        table = "blog_category"
        table_description = "博客分类表"


class Tag(BaseModel, TimestampMixin):
    """文章标签"""
    name = fields.CharField(max_length=30, unique=True, description="标签名称", index=True)
    slug = fields.CharField(max_length=30, unique=True, description="标签别名", index=True)
    color = fields.CharField(max_length=30, null=True, description="标签颜色")
    article_count = fields.IntField(default=0, description="文章数量")
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:
        table = "blog_tag"
        table_description = "博客标签表"


class Article(BaseModel, TimestampMixin):
    """文章模型"""
    title = fields.CharField(max_length=200, description="文章标题", index=True)
    cover = fields.CharField(max_length=500, null=True, description="封面图片URL")
    summary = fields.TextField(null=True, description="文章摘要")
    content = fields.TextField(description="文章内容(Markdown格式)")

    # 状态: draft(草稿), published(已发布), deleted(已删除)
    status = fields.CharField(max_length=20, default="draft", description="文章状态", index=True)

    # 关联字段
    category_id = fields.IntField(description="分类ID", index=True)
    author_id = fields.IntField(description="作者ID", index=True)

    # 基于角色的权限控制
    # 可以查看文章的角色ID列表（默认包含"普通用户"角色）
    view_roles = fields.JSONField(description="可查看的角色ID列表", default=list)
    # 可以编辑文章的角色ID列表（默认为空，只有作者可编辑）
    edit_roles = fields.JSONField(description="可编辑的角色ID列表", default=list)

    # 统计字段
    view_count = fields.IntField(default=0, description="阅读次数", index=True)
    like_count = fields.IntField(default=0, description="点赞数")

    is_top = fields.BooleanField(default=False, description="是否置顶", index=True)
    is_recommend = fields.BooleanField(default=False, description="是否推荐", index=True)

    published_at = fields.DatetimeField(null=True, description="发布时间", index=True)

    class Meta:
        table = "blog_article"
        table_description = "博客文章表"


class ArticleRevision(BaseModel, TimestampMixin):
    """文章编辑记录"""
    article_id = fields.IntField(description="文章ID", index=True)
    editor_id = fields.IntField(description="编辑人ID", index=True)
    editor_name = fields.CharField(max_length=50, description="编辑人姓名")
    
    # 快照数据
    title = fields.CharField(max_length=200, description="标题快照")
    content = fields.TextField(description="内容快照")
    summary = fields.TextField(null=True, description="摘要快照")
    cover = fields.CharField(max_length=500, null=True, description="封面快照")
    category_id = fields.IntField(description="分类ID快照")
    view_roles = fields.JSONField(description="可查看角色快照", default=list)
    edit_roles = fields.JSONField(description="可编辑角色快照", default=list)
    tag_ids = fields.JSONField(description="标签ID快照", default=list)
    
    # 差异记录
    changes = fields.JSONField(description="变更内容", default=dict)
    change_summary = fields.CharField(max_length=500, null=True, description="变更摘要")

    class Meta:
        table = "blog_article_revision"
        table_description = "文章编辑记录表"
        ordering = ["-created_at"]


class ArticleTag(BaseModel, TimestampMixin):
    """文章标签关联表"""
    article_id = fields.IntField(description="文章ID", index=True)
    tag_id = fields.IntField(description="标签ID", index=True)

    class Meta:
        table = "blog_article_tag"
        table_description = "文章标签关联表"
        unique_together = (("article_id", "tag_id"),)


class ArticleLike(BaseModel, TimestampMixin):
    """文章点赞记录"""
    article_id = fields.IntField(description="文章ID", index=True)
    user_id = fields.IntField(description="用户ID", index=True)

    class Meta:
        table = "blog_article_like"
        table_description = "文章点赞记录表"
        unique_together = (("article_id", "user_id"),)


class ArticleFavorite(BaseModel, TimestampMixin):
    """文章收藏记录"""
    article_id = fields.IntField(description="文章ID", index=True)
    user_id = fields.IntField(description="用户ID", index=True)

    class Meta:
        table = "blog_article_favorite"
        table_description = "文章收藏记录表"
        unique_together = (("article_id", "user_id"),)
