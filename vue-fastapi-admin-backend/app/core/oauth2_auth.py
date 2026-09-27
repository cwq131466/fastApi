"""
OAuth2 统一认证核心模块
提供与外部统一认证服务交互的所有功能
"""
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import HTTPException
from loguru import logger

from app.settings.config import settings
from app.utils.jwt_utils import create_access_token
from app.schemas.login import JWTPayload


def get_authorization_url(state: str = None) -> str:
    """
    生成OAuth2授权URL
    
    Args:
        state: CSRF保护状态字符串，如果未提供则自动生成
        
    Returns:
        完整的授权URL
    """
    if not state:
        state = secrets.token_urlsafe(32)
    
    params = {
        'response_type': 'code',
        'client_id': settings.OAUTH_CLIENT_ID,
        'redirect_uri': settings.OAUTH_REDIRECT_URI,
        'state': state,
    }
    
    auth_url = f"{settings.OAUTH_SERVER_BASE_URL}{settings.OAUTH_AUTHORIZE_ENDPOINT}?{urllib.parse.urlencode(params)}"
    logger.info(f"生成OAuth2授权URL: {auth_url}")
    return auth_url, state


async def exchange_code_for_token(code: str) -> dict:
    """
    使用授权码换取access token
    
    Args:
        code: OAuth2授权码
        
    Returns:
        包含access_token的字典
        
    Raises:
        HTTPException: 当token交换失败时
    """
    try:
        async with httpx.AsyncClient(verify=settings.VERIFY_SSL, timeout=30.0) as client:
            response = await client.post(
                f"{settings.OAUTH_SERVER_BASE_URL}{settings.OAUTH_TOKEN_ENDPOINT}",
                data={
                    'grant_type': 'authorization_code',
                    'client_id': settings.OAUTH_CLIENT_ID,
                    'client_secret': settings.OAUTH_CLIENT_SECRET,
                    'code': code,
                    'redirect_uri': settings.OAUTH_REDIRECT_URI,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code != 200:
                logger.error(f"Token交换失败: {response.status_code} - {response.text}")
                raise HTTPException(status_code=401, detail="获取访问令牌失败")
            
            result = response.json()
            # 参考项目返回格式: {"code": 200, "msg": "ok", "data": {...}}
            if result.get('code') == 200:
                token_data = result.get('data', {})
            else:
                # 标准OAuth2响应直接包含access_token
                token_data = result
            
            access_token = token_data.get('access_token')
            if not access_token:
                logger.error(f"Token响应中缺少access_token: {result}")
                raise HTTPException(status_code=401, detail="无效的令牌响应")
            
            logger.info("成功换取OAuth2 access token")
            return token_data
            
    except httpx.HTTPError as e:
        logger.error(f"Token交换HTTP错误: {str(e)}")
        raise HTTPException(status_code=503, detail="认证服务暂时不可用")
    except Exception as e:
        logger.error(f"Token交换异常: {str(e)}")
        raise HTTPException(status_code=500, detail="认证过程发生错误")


async def get_user_info_from_oauth(access_token: str) -> dict:
    """
    从OAuth2服务获取用户信息
    
    Args:
        access_token: OAuth2 access token
        
    Returns:
        映射后的用户信息字典
        
    Raises:
        HTTPException: 当获取用户信息失败时
    """
    try:
        async with httpx.AsyncClient(verify=settings.VERIFY_SSL, timeout=30.0) as client:
            response = await client.get(
                f"{settings.OAUTH_SERVER_BASE_URL}{settings.OAUTH_USERINFO_ENDPOINT}",
                params={'access_token': access_token}
            )
            
            if response.status_code != 200:
                logger.error(f"获取用户信息失败: {response.status_code} - {response.text}")
                raise HTTPException(status_code=401, detail="获取用户信息失败")
            
            result = response.json()
            
            # 处理返回格式: {"code": 200, "msg": "ok", "data": {...}}
            if result.get('code') == 200:
                user_data = result.get('data', {})
            else:
                user_data = result
            
            if not user_data:
                logger.error("用户信息为空")
                raise HTTPException(status_code=401, detail="无效的用户信息")
            
            # 字段映射
            mapped_user = {
                'oauth_user_id': user_data.get('userId'),
                'username': user_data.get('userName'),
                'alias': user_data.get('nickName'),
                'email': user_data.get('email', ''),
                'phone': user_data.get('phonenumber'),
                'dept_id': user_data.get('deptId'),
                'dept_name': user_data.get('dept', {}).get('deptName') if user_data.get('dept') else None,
                'raw_data': user_data,  # 保留原始数据供后续使用
            }
            
            logger.info(f"成功获取用户信息: {mapped_user['username']}")
            return mapped_user
            
    except httpx.HTTPError as e:
        logger.error(f"获取用户信息HTTP错误: {str(e)}")
        raise HTTPException(status_code=503, detail="认证服务暂时不可用")
    except Exception as e:
        logger.error(f"获取用户信息异常: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户信息失败")


async def check_token_valid(access_token: str) -> bool:
    """
    验证OAuth2 token是否有效
    
    Args:
        access_token: OAuth2 access token
        
    Returns:
        token是否有效
    """
    try:
        async with httpx.AsyncClient(verify=settings.VERIFY_SSL, timeout=10.0) as client:
            response = await client.post(
                f"{settings.OAUTH_SERVER_BASE_URL}{settings.OAUTH_CHECKLOGIN_ENDPOINT}",
                data={
                    'client_id': settings.OAUTH_CLIENT_ID,
                    'client_secret': settings.OAUTH_CLIENT_SECRET,
                    'access_token': access_token,
                }
            )
            
            result = response.json()
            is_valid = result.get('code') == 200
            logger.info(f"Token验证结果: {is_valid}")
            return is_valid
            
    except Exception as e:
        logger.error(f"Token验证异常: {str(e)}")
        return False


async def logout_oauth_token(access_token: str) -> bool:
    """
    回收OAuth2 token（登出）
    
    Args:
        access_token: OAuth2 access token
        
    Returns:
        是否成功回收
    """
    try:
        async with httpx.AsyncClient(verify=settings.VERIFY_SSL, timeout=10.0) as client:
            response = await client.get(
                f"{settings.OAUTH_SERVER_BASE_URL}{settings.OAUTH_LOGOUT_ENDPOINT}",
                params={
                    'client_id': settings.OAUTH_CLIENT_ID,
                    'client_secret': settings.OAUTH_CLIENT_SECRET,
                    'access_token': access_token,
                }
            )
            
            result = response.json()
            success = result.get('code') == 200
            logger.info(f"Token回收结果: {'成功' if success else '失败'}")
            return success
            
    except Exception as e:
        logger.error(f"Token回收异常: {str(e)}")
        # 即使回收失败也不影响本地登出流程
        return False


def create_local_jwt(user_info: dict) -> str:
    """
    为OAuth用户创建本地JWT token
    
    Args:
        user_info: 用户信息字典，包含user_id, username等
        
    Returns:
        JWT token字符串
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    jwt_payload = JWTPayload(
        user_id=user_info['user_id'],
        username=user_info['username'],
        is_superuser=False,  # OAuth用户默认不是超级管理员
        exp=expire,
    )
    
    token = create_access_token(data=jwt_payload)
    logger.info(f"为用户 {user_info['username']} 创建本地JWT token")
    return token
