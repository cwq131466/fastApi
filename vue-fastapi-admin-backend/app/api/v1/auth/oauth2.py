"""
OAuth2 统一认证 API 路由
处理登录、回调、登出等接口
"""
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from loguru import logger
from starlette.middleware.sessions import SessionMiddleware

from app.controllers.user import user_controller
from app.core.oauth2_auth import (
    check_token_valid,
    create_local_jwt,
    exchange_code_for_token,
    get_authorization_url,
    get_user_info_from_oauth,
    logout_oauth_token,
)
from app.schemas.base import Success
from app.settings.config import settings

router = APIRouter(tags=["OAuth2认证"])


def get_frontend_callback_url(frontend_type: str) -> str:
    """根据前端类型获取回调URL"""
    frontend_urls = settings.FRONTEND_URLS.split(",")
    if frontend_type == "backend":
        # 管理后台使用第二个URL
        return frontend_urls[1].strip() if len(frontend_urls) > 1 else frontend_urls[0].strip()
    else:
        # 用户门户使用第一个URL（默认）
        return frontend_urls[0].strip()


@router.get("/oauth2/login", summary="OAuth2登录入口")
async def oauth_login(request: Request, frontend: str = Query(default="frontend")):
    """
    OAuth2登录入口
    参数 frontend: 前端标识，可选值 'frontend'(用户门户) 或 'backend'(管理后台)
    重定向到统一认证服务进行授权
    """
    if not settings.OAUTH_ENABLED:
        logger.warning("OAuth2认证未启用")
        raise HTTPException(status_code=400, detail="OAuth2认证未启用，请使用账号密码登录")
    
    try:
        # 生成随机state用于CSRF保护
        state = secrets.token_urlsafe(32)
        
        # 将state和frontend标识存储到session中
        request.session['oauth_state'] = state
        request.session['oauth_frontend'] = frontend  # 新增：存储前端标识
        
        # 生成授权URL
        auth_url, _ = get_authorization_url(state)
        
        logger.info(f"发起OAuth2登录请求，前端类型: {frontend}，重定向到: {auth_url}")
        
        # 重定向到统一认证服务
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"OAuth2登录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"登录过程发生错误: {str(e)}")


@router.get("/oauth2/callback", summary="OAuth2回调处理")
async def oauth_callback(request: Request):
    """
    OAuth2回调处理
    接收授权码，换取token，获取用户信息，创建/更新本地用户，生成本地JWT
    """
    if not settings.OAUTH_ENABLED:
        logger.warning("OAuth2认证未启用")
        raise HTTPException(status_code=400, detail="OAuth2认证未启用")
    
    try:
        # 从query参数获取code和state
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        error = request.query_params.get('error')
        
        # 检查是否有错误
        if error:
            error_description = request.query_params.get('error_description', '未知错误')
            logger.error(f"OAuth2授权失败: {error} - {error_description}")
            raise HTTPException(status_code=400, detail=f"授权失败: {error_description}")
        
        if not code:
            logger.error("缺少授权码")
            raise HTTPException(status_code=400, detail="缺少授权码")
        
        # 验证state（CSRF保护）
        stored_state = request.session.get('oauth_state')
        if not stored_state or state != stored_state:
            logger.warning(f"State验证失败: received={state}, stored={stored_state}")
            raise HTTPException(status_code=400, detail="State验证失败，可能是CSRF攻击")
        
        # 从session中获取前端标识
        frontend_type = request.session.get('oauth_frontend', 'frontend')
        
        # 清除session中的state
        del request.session['oauth_state']
        
        logger.info("开始处理OAuth2回调")
        
        # 用code换取OAuth access token
        token_data = await exchange_code_for_token(code)
        oauth_access_token = token_data.get('access_token')
        
        if not oauth_access_token:
            logger.error("未获取到OAuth access token")
            raise HTTPException(status_code=401, detail="获取访问令牌失败")
        
        # 获取用户信息
        oauth_user_info = await get_user_info_from_oauth(oauth_access_token)
        
        logger.info(f"成功获取OAuth用户信息: {oauth_user_info.get('username')}")
        
        # 自动创建或更新本地用户，同时保存 OAuth access_token
        local_user = await user_controller.get_or_create_oauth_user(
            oauth_user_info, 
            oauth_access_token=oauth_access_token
        )
        
        logger.info(f"本地用户处理完成: ID={local_user.id}, username={local_user.username}")
        
        # 创建本地JWT token
        jwt_token = create_local_jwt({
            'user_id': local_user.id,
            'username': local_user.username,
        })
        
        # 构建前端回调URL，携带JWT token
        frontend_base_url = get_frontend_callback_url(frontend_type)
        frontend_callback_url = f"{frontend_base_url}/auth/callback?token={jwt_token}"
        
        logger.info(f"重定向到前端回调页面 ({frontend_type}): {frontend_callback_url}")
        
        # 重定向到前端
        return RedirectResponse(url=frontend_callback_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth2回调处理异常: {str(e)}", exc_info=True)
        # 从session中获取前端标识用于错误重定向
        frontend_type = request.session.get('oauth_frontend', 'frontend')
        frontend_base_url = get_frontend_callback_url(frontend_type)
        # 重定向到前端登录页面，携带错误信息
        error_url = f"{frontend_base_url}/login?error=认证失败"
        return RedirectResponse(url=error_url)


@router.post("/logout", summary="登出接口")
async def oauth_logout(request: Request):
    """
    登出接口
    1. 从数据库获取当前用户的 OAuth access_token
    2. 调用 OAuth 服务器回收 token
    3. 清除数据库中的 OAuth access_token
    4. 清除后端 Session Cookie
    5. 返回成功响应，前端负责清除 localStorage
    """
    try:
        # 从 JWT token 中获取当前用户ID
        # JWT token 在请求头的 'token' 字段中
        auth_header = request.headers.get('token')
        user_id = None
        
        if auth_header and settings.OAUTH_ENABLED:
            try:
                from app.utils.jwt_utils import decode_access_token
                payload = decode_access_token(auth_header)
                user_id = payload.get('user_id')
                logger.info(f"从 JWT 中解析到用户ID: {user_id}")
            except Exception as e:
                logger.warning(f"解析 JWT token 失败: {str(e)}")
        
        # 1. 如果找到了用户ID，从数据库获取 OAuth access_token 并回收
        if user_id and settings.OAUTH_ENABLED:
            try:
                user = await user_controller.get(id=user_id)
                if user and user.oauth_access_token:
                    oauth_access_token = user.oauth_access_token
                    logger.info(f"找到用户 {user.username} 的 OAuth access_token，准备回收")
                    
                    # 调用 OAuth 服务器回收 token
                    await logout_oauth_token(oauth_access_token)
                    logger.info(f"已回收用户 {user.username} 的 OAuth access_token")
                    
                    # 清除数据库中的 OAuth access_token
                    await user_controller.clear_oauth_token(user_id)
                else:
                    logger.info(f"用户 ID={user_id} 没有存储的 OAuth access_token")
            except Exception as e:
                # OAuth token 回收失败不影响本地登出流程
                logger.warning(f"OAuth token 回收失败: {str(e)}，继续执行本地登出")
        
        # 2. 清除后端 Session Cookie
        request.session.clear()
        logger.info("已清除后端 Session")
        
        logger.info("用户登出成功")
        
        return Success(data={"message": "已成功登出"})
        
    except Exception as e:
        logger.error(f"登出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"登出失败: {str(e)}")


@router.get("/oauth2/config", summary="获取认证配置")
async def get_auth_config():
    """
    获取认证配置
    返回是否启用OAuth2认证
    """
    return Success(data={
        "oauth_enabled": settings.OAUTH_ENABLED,
        "oauth_server_url": settings.OAUTH_SERVER_BASE_URL if settings.OAUTH_ENABLED else None,
    })
