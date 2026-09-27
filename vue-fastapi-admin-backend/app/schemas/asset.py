# -*- coding: utf-8 -*-
"""
资产相关的 Pydantic 数据模型
用于 API 请求和响应的数据验证与序列化
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ProtocolInfo(BaseModel):
    """协议信息"""
    name: str
    port: int


class PlatformInfo(BaseModel):
    """平台信息"""
    id: Union[int, str]  # JumpServer API返回int，需要兼容
    name: str


class CategoryInfo(BaseModel):
    """分类信息"""
    value: str
    label: str


class GatheredInfo(BaseModel):
    """采集信息"""
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None
    sn: Optional[str] = None


class SpecInfo(BaseModel):
    """规格信息"""
    cpu_model: Optional[str] = None
    memory_total: Optional[str] = None
    disk_total: Optional[str] = None


class HardwareInfo(BaseModel):
    """硬件信息（详细）"""
    cpu_cores: Optional[int] = None
    cpu_usage: Optional[str] = None
    memory_usage: Optional[str] = None
    disk_usage: Optional[str] = None
    temperature: Optional[str] = None
    power_status: Optional[str] = None
    fan_status: Optional[str] = None


class NetworkInfo(BaseModel):
    """网络信息"""
    total_interfaces: Optional[int] = None
    active_interfaces: Optional[int] = None
    bandwidth_usage: Optional[str] = None
    packet_loss_rate: Optional[str] = None


class SystemInfo(BaseModel):
    """系统信息"""
    os_version: Optional[str] = None
    uptime: Optional[str] = None
    last_login: Optional[str] = None
    config_last_modified: Optional[str] = None


class AssetBase(BaseModel):
    """资产基础信息（精简版，只返回必要字段）"""
    id: str
    name: str
    address: str
    category: CategoryInfo
    platform: PlatformInfo
    is_active: bool = True
    comment: Optional[str] = None
    labels: List[str] = []

    class Config:
        from_attributes = True


class AssetDetail(AssetBase):
    """资产详细信息"""
    created_by: Optional[str] = None
    date_created: Optional[str] = None
    org_id: Optional[str] = None
    nodes: List[Any] = []
    domain: Optional[Any] = None
    admin_user: Optional[Any] = None
    gathered_info: Optional[GatheredInfo] = None
    spec_info: Optional[SpecInfo] = None
    hardware_info: Optional[HardwareInfo] = None
    network_info: Optional[NetworkInfo] = None
    system_info: Optional[SystemInfo] = None

    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    """资产列表响应"""
    results: List[AssetBase]
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str
    jumpserver_connected: bool
    mock_data_enabled: bool
    message: Optional[str] = None

    class Config:
        from_attributes = True


class Dot1XUserInfo(BaseModel):
    """dot1X 认证用户信息"""
    mac: str
    auth_state: Optional[str] = None


class MacAddressInfo(BaseModel):
    """MAC 地址信息"""
    mac: str           # MAC 地址
    vlan: Optional[int] = None  # VLAN ID


class PortInfo(BaseModel):
    """端口信息"""
    name: str                    # 端口名称，如 GE1/0/1
    status: str                  # up / down / adm
    speed: Optional[str] = None  # 速率，如 1G(a), 100M
    duplex: Optional[str] = None # 双工模式，F(a)/H(a)
    port_type: Optional[str] = None  # 端口类型，A(ccess)/T(runk)/H(ybrid)
    pvid: Optional[int] = None   # PVID
    description: Optional[str] = None  # 端口描述
    mac_addresses: List[MacAddressInfo] = []  # 该端口学习到的 MAC 地址列表（含 VLAN）
    dot1x_enabled: bool = False        # 是否开启 dot1X
    dot1x_users: List[Dot1XUserInfo] = []  # dot1X 认证用户列表


class DeviceInfo(BaseModel):
    """设备信息"""
    model: Optional[str] = None
    uptime: Optional[str] = None
    cpu_usage: Optional[str] = None
    memory_usage: Optional[str] = None


class SwitchPortResponse(BaseModel):
    """交换机端口状态响应"""
    device_info: Optional[DeviceInfo] = None
    ports: List[PortInfo] = []
    message: Optional[str] = None
