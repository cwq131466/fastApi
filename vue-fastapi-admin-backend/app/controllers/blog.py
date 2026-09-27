from typing import Optional, List, Tuple
import re
from datetime import datetime
from tortoise.expressions import Q

from app.core.crud import CRUDBase
from app.models.blog import Category, Tag, Article, ArticleTag, ArticleRevision, ArticleLike, ArticleFavorite
from app.schemas.blog import CategoryCreate, CategoryUpdate, TagCreate, TagUpdate, ArticleCreate, ArticleUpdate
from app.core.ctx import CTX_USER_ID
from app.models.admin import User
from app.utils.diff import compute_diff, generate_change_summary


def generate_slug(name: str) -> str:
    """根据名称生成 slug"""
    # 转小写，替换非字母数字字符为横线
    slug = name.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug or 'category'


class CategoryController(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    def __init__(self):
        super().__init__(model=Category)

    async def get_tree(self) -> List[dict]:
        """获取分类树形结构"""
        all_categories = await self.model.filter(is_active=True).order_by("order")

        category_map = {}
        for cat in all_categories:
            cat_dict = await cat.to_dict()
            cat_dict["children"] = []
            category_map[cat.id] = cat_dict

        tree = []
        for cat in all_categories:
            if cat.parent_id == 0:
                tree.append(category_map[cat.id])
            elif cat.parent_id in category_map:
                category_map[cat.parent_id]["children"].append(category_map[cat.id])

        return tree

    async def create(self, obj_in: CategoryCreate) -> Category:
        """创建分类，自动生成唯一 slug"""
        # 如果未提供 slug 或 slug 已存在，自动生成
        slug = obj_in.slug if obj_in.slug else generate_slug(obj_in.name)
        
        # 检查 slug 是否已存在，如果存在则添加后缀
        existing = await self.model.filter(slug=slug).first()
        if existing:
            counter = 1
            while await self.model.filter(slug=f"{slug}-{counter}").exists():
                counter += 1
            slug = f"{slug}-{counter}"
        
        # 创建对象时使用生成的 slug
        obj_dict = obj_in.model_dump()
        obj_dict["slug"] = slug
        return await super().create(obj_in=obj_dict)

    async def remove(self, id: int) -> None:
        """删除分类（验证是否有子分类或关联文章）"""
        children_count = await self.model.filter(parent_id=id).count()
        if children_count > 0:
            raise ValueError("该分类下存在子分类，无法删除")

        articles_count = await Article.filter(category_id=id).count()
        if articles_count > 0:
            raise ValueError("该分类下存在文章，请先删除或转移文章")

        obj = await self.get(id=id)
        await obj.delete()


class TagController(CRUDBase[Tag, TagCreate, TagUpdate]):
    def __init__(self):
        super().__init__(model=Tag)

    async def create(self, obj_in: TagCreate) -> Tag:
        """创建标签，自动生成唯一 slug"""
        slug = obj_in.slug if obj_in.slug else generate_slug(obj_in.name)
        
        existing = await self.model.filter(slug=slug).first()
        if existing:
            counter = 1
            while await self.model.filter(slug=f"{slug}-{counter}").exists():
                counter += 1
            slug = f"{slug}-{counter}"
        
        obj_dict = obj_in.model_dump()
        obj_dict["slug"] = slug
        return await super().create(obj_in=obj_dict)

    async def update_article_count(self, tag_id: int) -> None:
        """更新标签的文章数量"""
        count = await ArticleTag.filter(tag_id=tag_id).count()
        tag = await self.get(id=tag_id)
        tag.article_count = count
        await tag.save()

    async def remove(self, id: int) -> None:
        """删除标签时同时删除关联关系"""
        await ArticleTag.filter(tag_id=id).delete()
        await super().remove(id=id)


class ArticleController(CRUDBase[Article, ArticleCreate, ArticleUpdate]):
    def __init__(self):
        super().__init__(model=Article)

    async def list_articles(
        self,
        page: int,
        page_size: int,
        category_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        order: str = "-created_at"
    ) -> Tuple[int, List[Article]]:
        """查询文章列表（支持多条件筛选）"""
        query = Q()

        if category_id:
            query &= Q(category_id=category_id)
        if status:
            query &= Q(status=status)
        if keyword:
            query &= Q(title__contains=keyword) | Q(summary__contains=keyword)

        # 如果按标签筛选，需要先查关联表
        if tag_id:
            article_ids = await ArticleTag.filter(tag_id=tag_id).values_list("article_id", flat=True)
            query &= Q(id__in=article_ids)

        total = await self.model.filter(query).count()
        articles = await self.model.filter(query).offset((page - 1) * page_size).limit(page_size).order_by(order)

        return total, articles

    async def list_articles_with_permission(
        self,
        page: int,
        page_size: int,
        current_user_id: int,
        current_user_role_ids: list,
        is_superuser: bool = False,
        category_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        author_id: Optional[int] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        order: str = "-created_at"
    ) -> Tuple[int, List[Article]]:
        """根据权限过滤文章列表
        
        权限规则:
        - 超级管理员: 查看所有文章（包括已删除）
        - 普通用户: 
          1. 自己创建的文章（始终可见，包括已删除）
          2. view_roles 包含用户角色的非已删除文章（可查看）
        - author_id: 如果指定，只获取该作者的文章
        - status: 如果指定状态，则按指定状态筛选
        """
        query = Q()

        # 状态筛选：如果明确指定了状态，则按指定状态查询
        if status:
            query &= Q(status=status)

        if category_id:
            query &= Q(category_id=category_id)
        if keyword:
            query &= Q(title__contains=keyword) | Q(summary__contains=keyword)
        if author_id:
            query &= Q(author_id=author_id)

        # 如果按标签筛选，需要先查关联表
        if tag_id:
            article_ids = await ArticleTag.filter(tag_id=tag_id).values_list("article_id", flat=True)
            query &= Q(id__in=article_ids)

        total = await self.model.filter(query).count()
        # 排序：置顶文章优先（is_top DESC），然后按发布时间倒序（published_at DESC）
        articles = await self.model.filter(query).offset((page - 1) * page_size).limit(page_size).order_by("-is_top", "-published_at")

        # 在Python层面进行权限过滤
        if not is_superuser:
            filtered_articles = []
            for article in articles:
                # 作者本人可以查看自己的所有文章（包括已删除）
                if article.author_id == current_user_id:
                    filtered_articles.append(article)
                # 非本人文章：已删除的不可见
                elif article.status == "deleted":
                    continue
                # view_roles 为空列表表示公开（所有人可见）
                elif article.view_roles == []:
                    filtered_articles.append(article)
                # 检查用户的角色是否在 view_roles 中
                elif article.view_roles:
                    if any(role_id in article.view_roles for role_id in current_user_role_ids):
                        filtered_articles.append(article)
            articles = filtered_articles
            total = len(filtered_articles)

        return total, articles
    
    def check_view_permission(self, article: Article, current_user_id: int, current_user_role_ids: list, is_superuser: bool = False) -> bool:
        """检查查看权限
        
        返回 True 如果有查看权限
        
        权限规则:
        - 超级管理员: 始终有权限
        - 作者本人: 始终有权限
        - view_roles = []: 公开，所有人可查看
        - view_roles = [0]: 私有，仅作者可查看
        - view_roles = [1, 2, ...]: 指定角色可查看
        """
        # 超级管理员拥有所有权限
        if is_superuser:
            return True
        
        # 作者本人可以查看
        if article.author_id == current_user_id:
            return True
        
        # view_roles 为空列表表示公开（所有人可见）
        if article.view_roles == []:
            return True
        
        # 检查用户的角色是否在 view_roles 中
        if article.view_roles:
            if any(role_id in article.view_roles for role_id in current_user_role_ids):
                return True
        
        return False
    
    def check_edit_permission(self, article: Article, current_user_id: int, current_user_role_ids: list, is_superuser: bool = False) -> bool:
        """检查编辑权限
        
        返回 True 如果有编辑权限
        
        权限规则:
        - 超级管理员: 始终有权限
        - 作者本人: 始终有权限
        - edit_roles = []: 公开，所有角色可编辑
        - edit_roles = [0]: 私有，仅作者可编辑
        - edit_roles = [1, 2, ...]: 指定角色可编辑
        """
        # 超级管理员拥有所有权限
        if is_superuser:
            return True
        
        # 作者本人可以编辑
        if article.author_id == current_user_id:
            return True
        
        # edit_roles 为空列表表示公开（所有角色可编辑）
        if article.edit_roles == []:
            return True
        
        # 检查用户的角色是否在 edit_roles 中
        if article.edit_roles:
            if any(role_id in article.edit_roles for role_id in current_user_role_ids):
                return True
        
        return False

    async def create(self, obj_in: ArticleCreate) -> Article:
        """创建文章并处理标签关联"""
        obj_dict = obj_in.model_dump(exclude={"tag_ids"})
        obj_dict["author_id"] = CTX_USER_ID.get()

        if obj_dict.get("status") == "published":
            obj_dict["published_at"] = datetime.now()

        article = await super().create(obj_in=obj_dict)

        # 处理标签关联
        if obj_in.tag_ids:
            for tag_id in obj_in.tag_ids:
                await ArticleTag.create(article_id=article.id, tag_id=tag_id)
                # 更新标签文章计数
                await tag_controller.update_article_count(tag_id)

        return article

    async def update(self, id: int, obj_in: ArticleUpdate) -> Article:
        """更新文章并创建修订记录"""
        # 获取当前文章快照
        old_article = await self.get(id=id)
        old_data = {
            "title": old_article.title,
            "content": old_article.content,
            "summary": old_article.summary,
            "cover": old_article.cover,
            "category_id": old_article.category_id,
            "view_roles": old_article.view_roles or [],
            "edit_roles": old_article.edit_roles or [],
            "status": old_article.status,
            "is_top": old_article.is_top,
            "is_recommend": old_article.is_recommend,
        }
        
        # 执行更新
        obj_dict = obj_in.model_dump(exclude_unset=True, exclude={"id", "tag_ids"})

        if "status" in obj_dict and obj_dict["status"] == "published":
            if old_article.status != "published":
                obj_dict["published_at"] = datetime.now()

        article = await super().update(id=id, obj_in=obj_dict)
        
        # 获取新数据快照
        new_data = {
            "title": article.title,
            "content": article.content,
            "summary": article.summary,
            "cover": article.cover,
            "category_id": article.category_id,
            "view_roles": article.view_roles or [],
            "edit_roles": article.edit_roles or [],
            "status": article.status,
            "is_top": article.is_top,
            "is_recommend": article.is_recommend,
        }
        
        # 计算差异
        diff = compute_diff(old_data, new_data)
        
        # 如果有变更，创建修订记录
        if diff:
            current_user_id = CTX_USER_ID.get()
            user = await User.filter(id=current_user_id).first()
            editor_name = user.alias or user.username if user else "未知"
            
            change_summary = generate_change_summary(diff)
            
            await ArticleRevision.create(
                article_id=id,
                editor_id=current_user_id,
                editor_name=editor_name,
                title=article.title,
                content=article.content,
                summary=article.summary,
                cover=article.cover,
                category_id=article.category_id,
                view_roles=article.view_roles or [],
                edit_roles=article.edit_roles or [],
                tag_ids=obj_in.tag_ids or [],
                changes=diff,
                change_summary=change_summary,
            )

        # 处理标签关联更新
        if obj_in.tag_ids is not None:
            # 删除旧关联
            await ArticleTag.filter(article_id=id).delete()
            # 创建新关联
            for tag_id in obj_in.tag_ids:
                await ArticleTag.create(article_id=id, tag_id=tag_id)
                await tag_controller.update_article_count(tag_id)

        return article

    async def increment_view_count(self, id: int) -> None:
        """增加阅读次数"""
        article = await self.get(id=id)
        article.view_count += 1
        await article.save()

    async def soft_delete(self, id: int) -> None:
        """软删除文章（标记为已删除）"""
        article = await self.get(id=id)
        article.status = "deleted"
        await article.save()

    async def restore(self, id: int) -> Article:
        """恢复文章（从回收站恢复为草稿状态）"""
        article = await self.get(id=id)
        if article.status != "deleted":
            raise ValueError("只能恢复已删除的文章")
        article.status = "draft"
        await article.save()
        return article

    async def hard_delete(self, id: int) -> None:
        """彻底删除文章及其相关数据
        
        删除内容包括:
        - 文章本身
        - 文章的标签关联 (ArticleTag)
        - 文章的修订历史 (ArticleRevision)
        """
        # 删除标签关联
        await ArticleTag.filter(article_id=id).delete()
        
        # 删除修订历史
        await ArticleRevision.filter(article_id=id).delete()
        
        # 删除文章
        article = await self.get(id=id)
        await article.delete()

    async def rollback_to_revision(self, revision_id: int, current_user_id: int) -> Article:
        """退回到指定修订版本
        
        将指定修订版本的内容恢复为当前文章内容，并创建新的修订记录。
        
        Args:
            revision_id: 修订记录ID
            current_user_id: 当前操作用户ID
            
        Returns:
            更新后的文章对象
        """
        # 获取修订记录
        revision = await ArticleRevision.filter(id=revision_id).first()
        if not revision:
            raise ValueError("修订记录不存在")
        
        # 获取当前文章
        article = await self.get(id=revision.article_id)
        
        # 保存更新前的快照（用于创建修订记录）
        old_data = {
            "title": article.title,
            "content": article.content,
            "summary": article.summary,
            "cover": article.cover,
            "category_id": article.category_id,
            "view_roles": article.view_roles or [],
            "edit_roles": article.edit_roles or [],
            "status": article.status,
            "is_top": article.is_top,
            "is_recommend": article.is_recommend,
        }
        
        # 将修订版本的内容恢复到文章
        article.title = revision.title
        article.content = revision.content
        article.summary = revision.summary
        article.cover = revision.cover
        article.category_id = revision.category_id
        article.view_roles = revision.view_roles or []
        article.edit_roles = revision.edit_roles or []
        await article.save()
        
        # 恢复标签关联
        if revision.tag_ids:
            # 删除旧标签关联
            await ArticleTag.filter(article_id=article.id).delete()
            # 创建新标签关联
            for tag_id in revision.tag_ids:
                await ArticleTag.create(article_id=article.id, tag_id=tag_id)
                await tag_controller.update_article_count(tag_id)
        
        # 获取新数据快照
        new_data = {
            "title": article.title,
            "content": article.content,
            "summary": article.summary,
            "cover": article.cover,
            "category_id": article.category_id,
            "view_roles": article.view_roles or [],
            "edit_roles": article.edit_roles or [],
            "status": article.status,
            "is_top": article.is_top,
            "is_recommend": article.is_recommend,
        }
        
        # 计算差异
        diff = compute_diff(old_data, new_data)
        
        # 如果有变更，创建修订记录
        if diff:
            user = await User.filter(id=current_user_id).first()
            editor_name = user.alias or user.username if user else "未知"
            
            change_summary = generate_change_summary(diff)
            
            await ArticleRevision.create(
                article_id=article.id,
                editor_id=current_user_id,
                editor_name=editor_name,
                title=article.title,
                content=article.content,
                summary=article.summary,
                cover=article.cover,
                category_id=article.category_id,
                view_roles=article.view_roles or [],
                edit_roles=article.edit_roles or [],
                tag_ids=revision.tag_ids or [],
                changes=diff,
                change_summary=f"退回到版本: {change_summary}",
            )
        
        return article

    async def remove(self, id: int) -> None:
        """删除文章（软删除）"""
        await self.soft_delete(id)

    async def toggle_like(self, article_id: int, user_id: int) -> Tuple[bool, int]:
        """切换点赞状态
        
        Returns:
            (is_liked, like_count): 当前点赞状态和总点赞数
        """
        # 检查文章是否存在
        article = await self.get(id=article_id)
        
        # 检查是否已点赞
        existing_like = await ArticleLike.filter(
            article_id=article_id, 
            user_id=user_id
        ).first()
        
        if existing_like:
            # 取消点赞
            await existing_like.delete()
            # 更新点赞计数
            article.like_count = max(0, article.like_count - 1)
            await article.save()
            return False, article.like_count
        else:
            # 添加点赞
            await ArticleLike.create(article_id=article_id, user_id=user_id)
            article.like_count += 1
            await article.save()
            return True, article.like_count

    async def get_like_status(self, article_id: int, user_id: int) -> Tuple[bool, int]:
        """获取点赞状态
        
        Returns:
            (is_liked, like_count): 当前点赞状态和总点赞数
        """
        article = await self.get(id=article_id)
        is_liked = await ArticleLike.filter(
            article_id=article_id, 
            user_id=user_id
        ).exists()
        return is_liked, article.like_count

    async def toggle_favorite(self, article_id: int, user_id: int) -> bool:
        """切换收藏状态
        
        Returns:
            is_favorited: 当前收藏状态
        """
        # 检查文章是否存在
        await self.get(id=article_id)
        
        # 检查是否已收藏
        existing_favorite = await ArticleFavorite.filter(
            article_id=article_id, 
            user_id=user_id
        ).first()
        
        if existing_favorite:
            # 取消收藏
            await existing_favorite.delete()
            return False
        else:
            # 添加收藏
            await ArticleFavorite.create(article_id=article_id, user_id=user_id)
            return True

    async def get_favorite_status(self, article_id: int, user_id: int) -> bool:
        """获取收藏状态
        
        Returns:
            is_favorited: 是否已收藏
        """
        return await ArticleFavorite.filter(
            article_id=article_id, 
            user_id=user_id
        ).exists()

    async def get_user_favorites(
        self, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 10
    ) -> Tuple[int, List[dict]]:
        """获取用户收藏的文章列表
        
        Returns:
            (total, favorites): 总数和收藏文章列表
        """
        # 查询收藏记录，按收藏时间倒序
        total = await ArticleFavorite.filter(user_id=user_id).count()
        favorites = await ArticleFavorite.filter(user_id=user_id)\
            .order_by("-created_at")\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()
        
        result = []
        for fav in favorites:
            # 获取文章信息
            article = await Article.filter(id=fav.article_id).first()
            if article:
                article_dict = await article.to_dict()
                # 将datetime转换为ISO格式字符串
                article_dict["favorited_at"] = fav.created_at.isoformat() if fav.created_at else None
                
                # 加载分类信息
                if article.category_id:
                    category = await Category.filter(id=article.category_id).first()
                    if category:
                        article_dict["category"] = await category.to_dict()
                
                # 加载作者信息
                if article.author_id:
                    author = await User.filter(id=article.author_id).first()
                    if author:
                        article_dict["author"] = {
                            "id": author.id, 
                            "username": author.username, 
                            "alias": author.alias
                        }
                
                result.append(article_dict)
        
        return total, result


# 创建全局控制器实例
category_controller = CategoryController()
tag_controller = TagController()
article_controller = ArticleController()
