"""
模拟数据生成器
生成 JumpServer 交换机资产的基本信息模拟数据
"""
import random
from typing import Dict, List


def generate_mock_assets(count: int = 50) -> List[Dict]:
    """
    生成模拟的交换机资产列表（只包含基本信息）

    Args:
        count: 生成的资产数量，默认50条

    Returns:
        List[Dict]: 模拟资产列表（基本信息）
    """
    # 定义一些基础数据用于生成模拟数据
    locations = [
        "北京数据中心",
        "上海数据中心",
        "广州数据中心",
        "深圳数据中心",
        "成都数据中心",
        "杭州数据中心",
        "武汉数据中心",
        "西安数据中心",
    ]

    brands = ["Huawei", "H3C", "Cisco", "Juniper", "Ruijie"]

    models = {
        "Huawei": ["S5720-52X-PWR-SI", "S6720-30L-HI-24S", "CE6850-48S6Q-HI"],
        "H3C": ["S5560S-28P-EI", "S6520X-54QC-EI", "S10508-V"],
        "Cisco": ["Catalyst 9300", "Catalyst 9500", "Nexus 9000"],
        "Juniper": ["EX4300-48T", "QFX5100-48S", "PTX10008"],
        "Ruijie": ["RG-S6510-48VS", "RG-S6220-48XS", "RG-N18010-X"],
    }

    categories = [
        {"value": "device", "label": "网络设备"},
        {"value": "server", "label": "服务器"},
        {"value": "storage", "label": "存储设备"},
    ]

    platforms = [
        {"id": 1, "name": "Huawei"},
        {"id": 2, "name": "H3C"},
        {"id": 3, "name": "Cisco"},
        {"id": 4, "name": "Juniper"},
        {"id": 5, "name": "Ruijie"},
    ]

    # 标签池
    label_pool = ["核心", "汇聚", "接入", "管理", "生产", "测试", "备份"]

    assets = []

    for i in range(1, count + 1):
        brand = brands[i % len(brands)]
        model_list = models[brand]
        model = model_list[i % len(model_list)]
        platform = platforms[i % len(platforms)]
        category = categories[i % len(categories)]
        location = locations[i % len(locations)]

        # 生成 IP 地址
        subnet = (i // 254) + 1
        host = (i % 254) + 1
        ip_address = f"10.{subnet}.{host // 256}.{host % 256}"

        # 生成标签（1-3个）
        num_labels = (i % 3) + 1
        labels = [label_pool[j % len(label_pool)] for j in range(i, i + num_labels)]

        # 生成备注
        comment = f"{location} - {brand} {model}，用途：{category['label']}"

        # 返回基本信息字段：id, name, address, category, platform, is_active, comment, labels
        asset = {
            "id": f"a{i:07d}-0000-0000-0000-000000000000",
            "name": f"{brand}-{model}-{i:03d}",
            "address": ip_address,
            "category": category,
            "platform": platform,
            "is_active": True,
            "comment": comment,
            "labels": labels,
        }

        assets.append(asset)

    return assets


def get_mock_asset_detail(asset_id: str) -> Dict:
    """
    获取单个资产的基本信息

    Args:
        asset_id: 资产ID

    Returns:
        Dict: 资产基本信息，如果不存在返回 None

    Note:
        详细的端口状态、运行时间等信息需要通过 paramiko 登录交换机获取
        此方法目前只返回基本信息，后续可扩展添加 paramiko 调用
    """
    all_assets = generate_mock_assets(50)

    for asset in all_assets:
        if asset["id"] == asset_id:
            # 当前只返回基本信息
            return asset

    return None


def search_mock_assets(keyword: str) -> List[Dict]:
    """
    搜索模拟资产

    Args:
        keyword: 搜索关键词

    Returns:
        List[Dict]: 匹配的资产列表
    """
    all_assets = generate_mock_assets(50)

    if not keyword:
        return all_assets

    keyword_lower = keyword.lower()
    filtered = [
        asset
        for asset in all_assets
        if keyword_lower in asset["name"].lower()
        or keyword_lower in asset["address"].lower()
        or keyword_lower in asset.get("comment", "").lower()
        or any(keyword_lower in label.lower() for label in asset.get("labels", []))
    ]

    return filtered


# ==================== 模拟交换机端口数据 ====================

def _generate_mock_ports() -> List[Dict]:
    """
    生成紫光交换机风格的模拟端口数据

    Returns:
        端口列表，每个端口为字典格式
    """
    ports = []

    # 生成 48 个 GE 端口
    for i in range(1, 49):
        port_name = f"GE1/0/{i}"

        # 随机分配状态：大部分 down，少数 up，极少数 adm
        rand = random.random()
        if rand < 0.6:
            status = "down"
        elif rand < 0.9:
            status = "up"
        else:
            status = "adm"

        # up 状态的端口才有速率和双工
        speed = None
        duplex = None
        if status == "up":
            speed = random.choice(["1G(a)", "100M", "10M"])
            duplex = random.choice(["full", "half"])

        # 端口类型：大部分 access，少数 trunk
        port_type = "trunk" if i in [45, 48] else "access"
        pvid = 1 if port_type == "trunk" else 341

        # 描述
        descriptions = {
            13: "131Home",
            37: "101Home",
            40: "104Home",
            43: "不要开这个口会有环",
            47: "B01-JIFANG-Jiankong",
        }
        description = descriptions.get(i, None)

        # MAC 地址：只有 up 且非 trunk 的端口才有 MAC（带 VLAN）
        mac_addresses = []
        if status == "up" and port_type != "trunk":
            num_macs = random.randint(1, 5)
            for _ in range(num_macs):
                mac = f"{random.choice(['a899', 'dc2d', '9cb2', 'b8d6'])}-" \
                      f"{random.randint(0, 0xffff):04x}-" \
                      f"{random.randint(0, 0xffff):04x}"
                vlan = pvid  # MAC 的 VLAN 通常与端口 PVID 一致
                mac_addresses.append({"mac": mac, "vlan": vlan})

        # dot1X：少数端口开启
        dot1x_enabled = False
        dot1x_users = []
        if status == "up" and random.random() < 0.15:
            dot1x_enabled = True
            for mac_info in mac_addresses[:2]:  # 最多2个dot1X用户
                dot1x_users.append({
                    "mac": mac_info["mac"],
                    "auth_state": "Authenticated",
                })

        ports.append({
            "name": port_name,
            "status": status,
            "speed": speed,
            "duplex": duplex,
            "port_type": port_type,
            "pvid": pvid,
            "description": description,
            "mac_addresses": mac_addresses,
            "dot1x_enabled": dot1x_enabled,
            "dot1x_users": dot1x_users,
        })

    # 生成 4 个 XGE 端口
    for i in range(49, 53):
        port_name = f"XGE1/0/{i}"
        ports.append({
            "name": port_name,
            "status": "adm",
            "speed": None,
            "duplex": None,
            "port_type": "access",
            "pvid": 1,
            "description": None,
            "mac_addresses": [],
            "dot1x_enabled": False,
            "dot1x_users": [],
        })

    return ports


def get_switch_ports_via_paramiko(asset: Dict) -> Dict:
    """
    获取交换机端口状态信息（模拟数据版本）

    Args:
        asset: 资产基本信息

    Returns:
        Dict: 包含设备信息和端口列表
    """
    # 设置随机种子以确保同一资产每次返回相同数据
    random.seed(hash(asset.get("id", "")) % (2**32))

    ports = _generate_mock_ports()

    return {
        "device_info": {
            "model": "UniFi S5720-52X-PWR-SI",
            "uptime": "125 days, 8 hours",
            "cpu_usage": "15%",
            "memory_usage": "45%",
        },
        "ports": ports,
        "message": "success",
    }
