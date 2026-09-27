
"""
资产相关的 API 路由
提供资产的增删改查接口
"""
import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.responses import StreamingResponse
import json

from app.core.dependency import AuthControl
from app.core.exceptions import AssetNotFoundError
from app.models.admin import User
from app.schemas.asset import (
    AssetBase,
    AssetDetail,
    AssetListResponse,
    HealthCheckResponse,
    SwitchPortResponse,
)
from app.schemas.base import Success
from app.services.jumpserver_client import get_jumpserver_client
from app.services.mock_asset_data import (
    generate_mock_assets,
    get_mock_asset_detail,
    search_mock_assets,
    get_switch_ports_via_paramiko,
)
from app.services.port_auth_service import get_port_auth_service
from app.services.switch_service import get_switch_service
from app.settings.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", summary="健康检查")
async def health_check(current_user=Depends(AuthControl.is_authed)):
    """
    健康检查接口

    返回应用的健康状态、JumpServer 连接状态和模拟数据启用状态
    """
    # 根据 OAUTH_ENABLED 判断是否使用真实环境
    use_real_environment = settings.OAUTH_ENABLED

    jumpserver_connected = False
    message = "OK"

    if use_real_environment:
        try:
            client = get_jumpserver_client()
            # 真正测试 JumpServer 连接
            client.test_authentication()
            jumpserver_connected = True
            message = "JumpServer 连接正常"
        except Exception as e:
            jumpserver_connected = False
            message = f"JumpServer 连接失败: {str(e)}"
            logger.warning(f"健康检查 - JumpServer 连接失败: {e}")
    else:
        message = "使用模拟数据模式（OAUTH_ENABLED=false）"

    health_data = HealthCheckResponse(
        status="healthy" if (
            not use_real_environment or jumpserver_connected) else "unhealthy",
        jumpserver_connected=jumpserver_connected,
        mock_data_enabled=not use_real_environment,
        message=message,
    )

    return Success(data=health_data.dict())


@router.get("/", summary="获取资产列表")
async def list_assets(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user=Depends(AuthControl.is_authed),
):
    """
    获取资产列表

    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大100
    - **keyword**: 搜索关键词（可选）

    根据 OAUTH_ENABLED 配置决定使用真实 JumpServer API 还是模拟数据
    """
    # 根据 OAUTH_ENABLED 判断是否使用真实环境
    use_real_environment = settings.OAUTH_ENABLED

    try:
        if not use_real_environment:
            # 使用模拟数据
            logger.info(f"使用模拟数据获取资产列表: page={page}, page_size={page_size}")

            if keyword:
                all_assets = search_mock_assets(keyword)
            else:
                all_assets = generate_mock_assets(25)

            # 计算分页
            total_count = len(all_assets)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_assets = all_assets[start_index:end_index]

            # 构建响应
            next_url = None
            previous_url = None
            if end_index < total_count:
                next_url = f"/api/v1/assets/?page={page + 1}&page_size={page_size}"
            if page > 1:
                previous_url = f"/api/v1/assets/?page={page - 1}&page_size={page_size}"

            response_data = AssetListResponse(
                results=paginated_assets,
                count=total_count,
                next=next_url,
                previous=previous_url,
            )

            return Success(data=response_data.dict())
        else:
            # 使用真实 JumpServer API
            logger.info(
                f"使用 JumpServer API 获取资产列表: page={page}, page_size={page_size}")

            client = get_jumpserver_client()
            offset = (page - 1) * page_size

            result = client.get_assets(
                limit=page_size, offset=offset, keyword=keyword)

            response_data = AssetListResponse(
                results=result.get("results", []),
                count=result.get("count", 0),
                next=result.get("next"),
                previous=result.get("previous"),
            )

            return Success(data=response_data.dict())

    except Exception as e:
        logger.error(f"获取资产列表失败: {e}", exc_info=True)
        # 如果真实 API 调用失败且未强制使用真实数据，回退到模拟数据
        if not use_real_environment:
            logger.warning("回退到模拟数据")
            all_assets = generate_mock_assets(25)
            response_data = AssetListResponse(
                results=all_assets[:page_size],
                count=len(all_assets),
                next=None,
                previous=None,
            )
            return Success(data=response_data.dict())
        raise


@router.get("/{asset_id}", summary="获取资产详情")
async def get_asset(
    asset_id: str,
    current_user=Depends(AuthControl.is_authed),
):
    """
    获取单个资产的详细信息

    - **asset_id**: 资产ID

    根据 OAUTH_ENABLED 配置决定使用真实 JumpServer API 还是模拟数据
    """
    # 根据 OAUTH_ENABLED 判断是否使用真实环境
    use_real_environment = settings.OAUTH_ENABLED

    try:
        if not use_real_environment:
            # 使用模拟数据
            logger.info(f"使用模拟数据获取资产详情: {asset_id}")
            asset = get_mock_asset_detail(asset_id)

            if asset is None:
                raise AssetNotFoundError(asset_id)

            return Success(data=asset)
        else:
            # 使用真实 JumpServer API
            logger.info(f"使用 JumpServer API 获取资产详情: {asset_id}")

            client = get_jumpserver_client()
            asset = client.get_asset_detail(asset_id)

            if asset is None:
                raise AssetNotFoundError(asset_id)

            return Success(data=asset)

    except AssetNotFoundError:
        raise
    except Exception as e:
        logger.error(f"获取资产详情失败: {e}", exc_info=True)
        # 如果真实 API 调用失败且未强制使用真实数据，回退到模拟数据
        if not use_real_environment:
            logger.warning("回退到模拟数据")
            asset = get_mock_asset_detail(asset_id)
            if asset:
                return Success(data=asset)
        raise


@router.get("/{asset_id}/ports", summary="获取交换机端口状态信息")
async def get_switch_ports(
    asset_id: str,
    current_user=Depends(AuthControl.is_authed),
):
    """
    获取交换机的端口状态信息

    通过 paramiko 登录交换机，获取：
    - 设备型号、运行时间
    - 所有端口的状态（up/down）
    - 端口速率、双工模式、MAC地址、dot1X状态等

    - **asset_id**: 资产ID

    根据 OAUTH_ENABLED 配置决定使用真实 SSH 连接还是模拟数据
    """
    use_real_environment = settings.OAUTH_ENABLED

    try:
        # 获取资产基本信息
        if not use_real_environment:
            asset = get_mock_asset_detail(asset_id)
        else:
            client = get_jumpserver_client()
            asset = client.get_asset_detail(asset_id)

        if asset is None:
            raise AssetNotFoundError(asset_id)

        switch_ip = asset.get("address")
        platform_name = asset.get("platform", {}).get("name", "UniFi")

        if not use_real_environment:
            # 使用模拟数据
            ports_data = get_switch_ports_via_paramiko(asset)
        else:
            # 使用真实交换机服务
            service = get_switch_service()
            ports_data = service.get_port_info(switch_ip, platform_name)

        # 确保数据可 JSON 序列化（处理 Pydantic 模型）
        if isinstance(ports_data, dict):
            if "device_info" in ports_data and hasattr(ports_data["device_info"], "model_dump"):
                ports_data["device_info"] = ports_data["device_info"].model_dump()
            if "ports" in ports_data:
                serialized_ports = []
                for port in ports_data["ports"]:
                    if hasattr(port, "model_dump"):
                        port_dict = port.model_dump()
                        # 嵌套对象也需要序列化
                        if "mac_addresses" in port_dict:
                            port_dict["mac_addresses"] = [
                                m.model_dump() if hasattr(m, "model_dump") else m
                                for m in port_dict["mac_addresses"]
                            ]
                        if "dot1x_users" in port_dict:
                            port_dict["dot1x_users"] = [
                                u.model_dump() if hasattr(u, "model_dump") else u
                                for u in port_dict["dot1x_users"]
                            ]
                        serialized_ports.append(port_dict)
                    else:
                        serialized_ports.append(port)
                ports_data["ports"] = serialized_ports

        return Success(data=ports_data)

    except AssetNotFoundError:
        raise
    except Exception as e:
        logger.error(f"获取端口信息失败: {e}", exc_info=True)
        raise


@router.get("/{asset_id}/ports/stream")
async def get_switch_ports_stream(
    asset_id: str,
    request: Request,
    token: Optional[str] = Query(None, description="认证token（可选，也可从Header获取）"),
):
    """
    通过 SSE 流式获取交换机端口信息（带实时进度）
    
    返回格式：
    - event: progress - 进度更新
    - event: complete - 完成，包含完整数据
    - event: error - 错误信息
    """
    from fastapi import HTTPException
    
    # 尝试从 URL 参数或 Header 获取 token
    auth_token = token or request.headers.get("token")
    
    if not auth_token:
        raise HTTPException(status_code=401, detail="缺少认证token")
    
    # 验证 token
    try:
        import jwt
        decode_data = jwt.decode(auth_token, settings.SECRET_KEY, algorithms=settings.JWT_ALGORITHM)
        user_id = decode_data.get("user_id")
        current_user = await User.filter(id=user_id).first()
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication failed")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="无效的Token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期")
    use_real_environment = settings.OAUTH_ENABLED
    
    async def event_generator():
        import asyncio
        from queue import Queue
        from threading import Thread
        
        # 使用队列来传递进度消息
        progress_queue = Queue()
        
        try:
            # 获取资产基本信息
            if not use_real_environment:
                asset = get_mock_asset_detail(asset_id)
            else:
                client = get_jumpserver_client()
                asset = client.get_asset_detail(asset_id)

            if asset is None:
                raise AssetNotFoundError(asset_id)

            switch_ip = asset.get("address")
            platform_name = asset.get("platform", {}).get("name", "UniFi")

            # 发送开始事件
            yield f"event: start\ndata: {json.dumps({'message': '开始获取交换机信息'}, ensure_ascii=False)}\n\n"

            if not use_real_environment:
                # 模拟环境：发送模拟进度
                phases = [
                    ("connecting", "正在连接交换机..."),
                    ("connected", "连接成功，开始获取数据..."),
                    ("executing_interface", "正在获取端口状态..."),
                    ("parsing_interface", "解析端口数据..."),
                    ("interface_done", "已获取 48 个端口信息"),
                    ("executing_mac", "正在获取 MAC 地址表..."),
                    ("parsing_mac", "解析 MAC 地址数据..."),
                    ("mac_done", "已获取 120 条 MAC 记录"),
                    ("executing_dot1x", "正在获取 dot1X 会话信息..."),
                    ("parsing_dot1x", "解析 dot1X 数据..."),
                    ("dot1x_done", "已获取 35 条 dot1X 会话"),
                    ("merging", "正在合并数据..."),
                    ("completed", "数据加载完成！"),
                ]
                
                for phase, msg in phases:
                    await asyncio.sleep(0.5)  # 模拟延迟
                    data = {"phase": phase, "message": msg}
                    yield f"event: progress\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                
                ports_data = get_switch_ports_via_paramiko(asset)
            else:
                # 真实环境：使用队列实现真正的实时推送
                from concurrent.futures import ThreadPoolExecutor
                from queue import Queue
                import time
                
                # 创建线程安全的队列
                progress_queue = Queue()
                
                def sync_fetch():
                    """在线程中执行的同步函数"""
                    service = get_switch_service()
                    
                    # 创建一个回调，将消息放入队列
                    def progress_callback(phase: str, message: str):
                        data = {
                            "phase": phase,
                            "message": message,
                            "timestamp": time.time()
                        }
                        progress_queue.put(data)  # 线程安全
                    
                    return service.get_port_info(switch_ip, platform_name, progress_callback)
                
                # 启动后台任务：在线程池中执行
                loop = asyncio.get_event_loop()
                executor = ThreadPoolExecutor()
                fetch_task = loop.run_in_executor(executor, sync_fetch)
                
                # 同时监听队列，实时推送进度
                while True:
                    # 检查是否完成
                    if fetch_task.done():
                        # 获取最终结果（如果有异常会在这里抛出）
                        try:
                            ports_data = fetch_task.result()
                        except Exception as e:
                            logger.error(f"获取交换机信息失败: {e}", exc_info=True)
                            error_data = {"success": False, "error": str(e)}
                            yield f"event: error\ndata: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                            return
                        
                        # 处理完剩余的消息
                        while not progress_queue.empty():
                            msg = progress_queue.get_nowait()
                            yield f"event: progress\ndata: {json.dumps(msg, ensure_ascii=False)}\n\n"
                        break
                    
                    # 从队列中获取进度消息并立即推送
                    try:
                        msg = progress_queue.get(timeout=0.1)
                        yield f"event: progress\ndata: {json.dumps(msg, ensure_ascii=False)}\n\n"
                    except:
                        # 超时或队列为空，继续循环
                        continue

            # 确保数据可 JSON 序列化
            if isinstance(ports_data, dict):
                if "device_info" in ports_data and hasattr(ports_data["device_info"], "model_dump"):
                    ports_data["device_info"] = ports_data["device_info"].model_dump()
                if "ports" in ports_data:
                    serialized_ports = []
                    for port in ports_data["ports"]:
                        if hasattr(port, "model_dump"):
                            port_dict = port.model_dump()
                            if "mac_addresses" in port_dict:
                                port_dict["mac_addresses"] = [
                                    m.model_dump() if hasattr(m, "model_dump") else m
                                    for m in port_dict["mac_addresses"]
                                ]
                            if "dot1x_users" in port_dict:
                                port_dict["dot1x_users"] = [
                                    u.model_dump() if hasattr(u, "model_dump") else u
                                    for u in port_dict["dot1x_users"]
                                ]
                            serialized_ports.append(port_dict)
                        else:
                            serialized_ports.append(port)
                    ports_data["ports"] = serialized_ports

            # 发送完成事件
            result = {
                "success": True,
                "data": ports_data,
            }
            yield f"event: complete\ndata: {json.dumps(result, ensure_ascii=False)}\n\n"

        except AssetNotFoundError:
            error_data = {"success": False, "error": f"资产 {asset_id} 不存在"}
            yield f"event: error\ndata: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"获取交换机端口信息失败: {e}", exc_info=True)
            error_data = {"success": False, "error": str(e)}
            yield f"event: error\ndata: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )


@router.post("/ports/dot1x", summary="切换端口 dot1X 鉴权状态")
async def toggle_port_dot1x(
    switch_ip: str = Body(..., embed=True, description="交换机 IP 地址"),
    port_name: str = Body(..., embed=True, description="端口名称（如 GigabitEthernet1/0/37）"),
    enable: bool = Body(..., embed=True, description="True 为开启，False 为关闭"),
    jumpserver_username: str = Body(..., embed=True, description="JumpServer 用户名"),
    jumpserver_password: str = Body(..., embed=True, description="JumpServer 密码"),
    current_user=Depends(AuthControl.is_authed),
):
    """
    切换交换机端口的 dot1X 鉴权状态

    需要提供 JumpServer 认证凭据来执行操作
    会根据资产的平台名称自动选择对应的命令处理器

    - **switch_ip**: 交换机 IP 地址
    - **port_name**: 端口名称（如 GigabitEthernet1/0/37）
    - **enable**: True 为开启 dot1x，False 为关闭
    - **jumpserver_username**: JumpServer 用户名
    - **jumpserver_password**: JumpServer 密码
    """
    try:
        # 验证参数
        if not jumpserver_username or not jumpserver_password:
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail="缺少用户名或密码")

        # 获取资产信息以确定平台名称
        use_real_environment = settings.OAUTH_ENABLED
        platform_name = "UniFi"  # 默认平台

        if not use_real_environment:
            asset = get_mock_asset_detail(switch_ip)
        else:
            client = get_jumpserver_client()
            # 尝试通过 IP 查找资产
            asset = None
            assets_data = client.get_assets(limit=1000)
            assets_list = assets_data.get("results", [])
            for a in assets_list:
                if a.get("address") == switch_ip or a.get("ip") == switch_ip:
                    asset = a
                    break

        if asset:
            platform_name = asset.get("platform", {}).get("name", "UniFi")
            logger.info(f"检测到资产平台: {platform_name}")

        # 调用端口认证服务
        service = get_port_auth_service()
        result = service.toggle_port_dot1x(
            switch_ip=switch_ip,
            port_name=port_name,
            enable=enable,
            jumpserver_username=jumpserver_username,
            jumpserver_password=jumpserver_password,
            platform_name=platform_name,
        )

        if result["success"]:
            return Success(data=result)
        else:
            from fastapi import HTTPException

            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        logger.error(f"切换端口 dot1X 状态失败: {e}", exc_info=True)
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")
