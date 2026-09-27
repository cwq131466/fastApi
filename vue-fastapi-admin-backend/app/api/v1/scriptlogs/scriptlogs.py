from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from tortoise.expressions import Q

from app.models.admin import ScriptRunLog, User
from app.core.dependency import AuthControl, PermissionControl, DependAuth
from app.schemas import Success, SuccessExtra

# 公开路由（接收日志，使用 token 认证）
public_router = APIRouter()

# 需要认证的路由（查询日志，需要角色权限）
auth_router = APIRouter()


class ScriptLogPayload(BaseModel):
    """脚本日志接收的数据模型"""
    TIME: str = Field(..., description="执行时间")
    LEVEL: str = Field(..., description="日志级别")
    INFO: str = Field(..., description="日志信息")
    CMD: Optional[str] = Field(None, description="执行的命令/脚本")
    IP: str = Field(..., description="IP地址")
    OS: Optional[str] = Field(None, description="操作系统")
    Kernel: Optional[str] = Field(None, description="内核版本")
    MAC: Optional[str] = Field(None, description="MAC地址")


@public_router.post("/receive", summary="接收脚本执行日志")
async def receive_script_log(payload: ScriptLogPayload, current_user: User = Depends(AuthControl.is_authed)):
    """
    接收来自客户端的脚本执行日志（需要 token 认证）

    curl -sSf -X POST -H "Content-Type: application/json" \
         -H "User-Agent: NetworkLogger/1.0" \
         -H "token: YOUR_TOKEN_HERE" \
         -d '{"TIME":"2024-01-01T12:00:00","LEVEL":"INFO","INFO":"test","CMD":"test.sh","IP":"192.168.1.1","OS":"Ubuntu","Kernel":"5.4.0","MAC":"00:11:22:33:44:55"}' \
         http://your-server:9999/api/v1/scriptlog/receive
    """
    try:
        # 解析时间字符串为 datetime 对象
        time_str = payload.TIME
        try:
            exec_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            # 如果解析失败，使用当前时间
            exec_time = datetime.now()

        # 创建日志记录，带上用户名
        await ScriptRunLog.create(
            time=exec_time,
            level=payload.LEVEL,
            info=payload.INFO,
            cmd=payload.CMD,
            ip=payload.IP,
            os=payload.OS,
            kernel=payload.Kernel,
            mac=payload.MAC,
            username=current_user.username,  # 通过 token 获取的用户名
        )

        return Success(msg="日志接收成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"日志接收失败: {str(e)}")


@auth_router.get("/list", summary="查看脚本执行日志列表")
async def get_script_log_list(
    current_user: User = Depends(AuthControl.is_authed),
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    level: str = Query("", description="日志级别"),
    ip: str = Query("", description="IP地址"),
    username: str = Query("", description="用户名"),
    keyword: str = Query("", description="搜索关键词（日志信息）"),
    start_time: datetime = Query(None, description="开始时间"),
    end_time: datetime = Query(None, description="结束时间"),
):
    """
    查询脚本执行日志列表，支持多条件筛选（需要登录认证）
    """
    q = Q()

    if level:
        q &= Q(level__icontains=level)
    if ip:
        q &= Q(ip__icontains=ip)
    if username:
        q &= Q(username__icontains=username)
    if keyword:
        q &= Q(info__icontains=keyword)
    if start_time and end_time:
        q &= Q(time__range=[start_time, end_time])
    elif start_time:
        q &= Q(time__gte=start_time)
    elif end_time:
        q &= Q(time__lte=end_time)

    log_objs = await ScriptRunLog.filter(q).offset((page - 1) * page_size).limit(page_size).order_by("-time")
    total = await ScriptRunLog.filter(q).count()
    data = [await log.to_dict() for log in log_objs]

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)
