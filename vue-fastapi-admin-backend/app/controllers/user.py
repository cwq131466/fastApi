from datetime import datetime
from typing import List, Optional

from fastapi.exceptions import HTTPException
from loguru import logger

from app.core.crud import CRUDBase
from app.models.admin import User, Role
from app.schemas.login import CredentialsSchema
from app.schemas.users import UserCreate, UserUpdate
from app.utils.password import get_password_hash, verify_password

from .role import role_controller


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(model=User)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.model.filter(email=email).first()

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.model.filter(username=username).first()

    async def create_user(self, obj_in: UserCreate) -> User:
        obj_in.password = get_password_hash(password=obj_in.password)
        obj = await self.create(obj_in)
        return obj

    async def update_last_login(self, id: int) -> None:
        user = await self.model.get(id=id)
        user.last_login = datetime.now()
        await user.save(update_fields=["last_login"])

    async def authenticate(self, credentials: CredentialsSchema) -> Optional["User"]:
        user = await self.model.filter(username=credentials.username).first()
        if not user:
            raise HTTPException(status_code=400, detail="无效的用户名")
        verified = verify_password(credentials.password, user.password)
        if not verified:
            raise HTTPException(status_code=400, detail="密码错误!")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="用户已被禁用")
        return user

    async def update_roles(self, user: User, role_ids: List[int]) -> None:
        await user.roles.clear()
        for role_id in role_ids:
            role_obj = await role_controller.get(id=role_id)
            await user.roles.add(role_obj)

    async def reset_password(self, user_id: int):
        user_obj = await self.get(id=user_id)
        if user_obj.is_superuser:
            raise HTTPException(status_code=403, detail="不允许重置超级管理员密码")
        user_obj.password = get_password_hash(password="123456")
        await user_obj.save()

    async def get_or_create_oauth_user(self, oauth_user_info: dict, oauth_access_token: str = None) -> User:
        """
        获取或创建OAuth用户
        
        Args:
            oauth_user_info: OAuth用户信息字典，包含username, alias, email, phone等
            oauth_access_token: OAuth access token，用于后续登出时回收
            
        Returns:
            User对象
        """
        username = oauth_user_info.get('username')
        if not username:
            raise HTTPException(status_code=400, detail="OAuth用户信息中缺少用户名")
        
        # 先尝试通过username查找用户
        user = await self.get_by_username(username)
        
        if user:
            # 用户已存在，更新可变字段
            logger.info(f"OAuth用户已存在: {username}")
            update_fields = {
                'alias': oauth_user_info.get('alias', user.alias),
                'email': oauth_user_info.get('email', user.email),
                'phone': oauth_user_info.get('phone', user.phone),
            }
            # 更新 OAuth access_token
            if oauth_access_token:
                update_fields['oauth_access_token'] = oauth_access_token
            
            # 使用 update_from_dict 避免部分模型保存问题
            user = user.update_from_dict(update_fields)
            await user.save(update_fields=list(update_fields.keys()))
            await self.update_last_login(user.id)
            return user
        
        # 用户不存在，创建新用户
        logger.info(f"创建新的OAuth用户: {username}")
        
        # 生成随机密码（OAuth用户不需要密码登录，但字段可能需要）
        import secrets
        random_password = secrets.token_urlsafe(16)
        
        # 确保邮箱唯一性，如果邮箱已存在则使用默认值
        email = oauth_user_info.get('email', '')
        if email:
            existing_user = await self.get_by_email(email)
            if existing_user:
                logger.warning(f"邮箱 {email} 已被使用，使用默认邮箱")
                email = f"{username}@oauth.local"
        else:
            email = f"{username}@oauth.local"
        
        # 创建用户
        user_create = UserCreate(
            username=username,
            alias=oauth_user_info.get('alias', username),
            email=email,
            phone=oauth_user_info.get('phone'),
            password=random_password,
            is_active=True,
            is_superuser=False,
        )
        
        user = await self.create_user(user_create)
        
        # 保存 OAuth access_token
        if oauth_access_token:
            await self.model.filter(id=user.id).update(oauth_access_token=oauth_access_token)
            # 重新获取用户对象以刷新内存中的状态
            user = await self.get(id=user.id)
            logger.info(f"已保存用户 {username} 的 OAuth access_token")
        
        # 分配"普通用户"角色
        try:
            user_role = await Role.filter(name="普通用户").first()
            if user_role:
                await user.roles.add(user_role)
                logger.info(f"为用户 {username} 分配角色: 普通用户")
            else:
                logger.warning("未找到'普通用户'角色，跳过角色分配")
        except Exception as e:
            logger.error(f"分配角色失败: {str(e)}")
            # 角色分配失败不影响用户创建
        
        await self.update_last_login(user.id)
        return user
    
    async def clear_oauth_token(self, user_id: int) -> None:
        """
        清除用户的 OAuth access_token（登出时调用）
        
        Args:
            user_id: 用户ID
        """
        await self.model.filter(id=user_id).update(oauth_access_token=None)
        logger.info(f"已清除用户 ID={user_id} 的 OAuth access_token")


user_controller = UserController()
