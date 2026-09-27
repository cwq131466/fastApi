"""
交换机服务模块
提供通过 JumpServer 跳板机 SSH 登录交换机获取端口状态的功能
支持多品牌扩展架构
"""
import logging
import re
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional

from app.schemas.asset import DeviceInfo, Dot1XUserInfo, MacAddressInfo, PortInfo

logger = logging.getLogger(__name__)

# JumpServer 跳板机配置
JUMPSERVER_HOST = "32.15.64.5"
JUMPSERVER_PORT = 2222
JUMP_SERVER_USERNAME_PREFIX = "net_api@admin@"
SSH_PASSWORD = "Gfdx_api@12345"


class BaseSwitchHandler(ABC):
    """交换机处理器基类"""

    @abstractmethod
    def fetch_port_info(self, switch_ip: str, progress_callback: Optional[Callable] = None) -> Dict:
        """
        获取交换机端口信息

        Args:
            switch_ip: 交换机 IP 地址
            progress_callback: 进度回调函数，接收 (phase: str, message: str) 参数

        Returns:
            包含 device_info 和 ports 的字典
        """
        pass

    def _connect_ssh(self, switch_ip: str):
        """
        通过 JumpServer 建立 SSH 连接

        Args:
            switch_ip: 交换机 IP 地址

        Returns:
            paramiko.SSHClient 实例
        """
        try:
            import paramiko
        except ImportError:
            raise ImportError("paramiko 未安装，请运行: pip install paramiko")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        username = f"{JUMP_SERVER_USERNAME_PREFIX}{switch_ip}"
        logger.info(f"正在通过 JumpServer 连接交换机: {switch_ip}")

        ssh.connect(
            hostname=JUMPSERVER_HOST,
            port=JUMPSERVER_PORT,
            username=username,
            password=SSH_PASSWORD,
            timeout=10,
        )
        return ssh

    def _execute_command(self, ssh, command: str) -> str:
        """
        执行 SSH 命令并返回输出

        Args:
            ssh: paramiko.SSHClient 实例
            command: 要执行的命令

        Returns:
            命令输出字符串
        """
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode("utf-8", errors="ignore")
        error = stderr.read().decode("utf-8", errors="ignore")

        if error:
            logger.warning(f"命令执行警告: {command}, 错误: {error}")

        return output


class UniFiSwitchHandler(BaseSwitchHandler):
    """紫光交换机处理器"""

    def fetch_port_info(self, switch_ip: str, progress_callback: Optional[Callable] = None) -> Dict:
        """
        获取紫光交换机端口信息

        执行三条命令：
        1. dis inter brief - 获取端口基本状态
        2. dis mac-address - 获取 MAC 地址与端口映射
        3. dis dot1x sessions - 获取 dot1X 会话信息

        Args:
            switch_ip: 交换机 IP 地址
            progress_callback: 进度回调函数

        Returns:
            包含 device_info 和 ports 的字典
        """
        ssh = None
        try:
            # 阶段1: 连接交换机
            if progress_callback:
                progress_callback("connecting", "正在连接交换机...")
            
            ssh = self._connect_ssh(switch_ip)
            
            if progress_callback:
                progress_callback("connected", "连接成功，开始获取数据...")

            # 阶段2: 执行第一条命令 - 获取端口基本信息
            if progress_callback:
                progress_callback("executing_interface", "正在获取端口状态...")
            
            logger.info(f"执行命令: dis inter brief")
            inter_brief_output = self._execute_command(ssh, "dis inter brief")
            
            if progress_callback:
                progress_callback("parsing_interface", f"解析端口数据... (共{len(inter_brief_output)}字符)")
            
            ports = self._parse_interface_brief(inter_brief_output)
            
            if progress_callback:
                progress_callback("interface_done", f"已获取 {len(ports)} 个端口信息")

            # 阶段3: 执行第二条命令 - 获取 MAC 地址
            if progress_callback:
                progress_callback("executing_mac", "正在获取 MAC 地址表...")
            
            logger.info(f"执行命令: dis mac-address")
            mac_address_output = self._execute_command(ssh, "dis mac-address")
            
            if progress_callback:
                progress_callback("parsing_mac", f"解析 MAC 地址数据... (共{len(mac_address_output)}字符)")
            
            mac_map = self._parse_mac_address(mac_address_output)
            
            if progress_callback:
                progress_callback("mac_done", f"已获取 {sum(len(v) for v in mac_map.values())} 条 MAC 记录")

            # 阶段4: 执行第三条命令 - 获取 dot1X 会话
            if progress_callback:
                progress_callback("executing_dot1x", "正在获取 dot1X 会话信息...")
            
            logger.info(f"执行命令: dis dot1x sessions")
            dot1x_sessions_output = self._execute_command(ssh, "dis dot1x sessions")
            
            if progress_callback:
                progress_callback("parsing_dot1x", f"解析 dot1X 数据... (共{len(dot1x_sessions_output)}字符)")
            
            dot1x_map = self._parse_dot1x_sessions(dot1x_sessions_output)
            
            if progress_callback:
                progress_callback("dot1x_done", f"已获取 {sum(len(v) for v in dot1x_map.values())} 条 dot1X 会话")

            # 阶段5: 合并数据
            if progress_callback:
                progress_callback("merging", "正在合并数据...")
            
            for port in ports:
                port_name = port.name

                # 从 dis mac-address 获取 MAC 地址（包括所有端口类型）
                if port_name in mac_map:
                    port.mac_addresses = list(mac_map[port_name])

                # 从 dis dot1x sessions 获取 dot1X 信息
                if port_name in dot1x_map:
                    port.dot1x_enabled = True
                    port.dot1x_users = dot1x_map[port_name]

                    # 将 dot1X 用户的 MAC 补充到 mac_addresses 中
                    existing_macs = {m.mac for m in port.mac_addresses}
                    for user in dot1x_map[port_name]:
                        if user.mac not in existing_macs:
                            port.mac_addresses.append(MacAddressInfo(mac=user.mac, vlan=None))
                            existing_macs.add(user.mac)

            # 获取设备信息
            device_info = DeviceInfo(
                model="UniFi Switch",
                uptime="N/A",
            )

            if progress_callback:
                progress_callback("completed", "数据加载完成！")

            return {
                "device_info": device_info,
                "ports": ports,
                "message": "success",
            }

        except Exception as e:
            logger.error(f"获取紫光交换机端口信息失败: {e}", exc_info=True)
            
            if progress_callback:
                progress_callback("error", f"连接失败: {str(e)}")
            
            return {
                "device_info": None,
                "ports": [],
                "message": f"连接失败: {str(e)}",
            }
        finally:
            if ssh:
                ssh.close()

    def _parse_interface_brief(self, output: str) -> List[PortInfo]:
        """
        解析 dis inter brief 命令输出

        只解析 bridge mode 下的端口列表
        """
        ports = []

        # 找到 bridge mode 部分
        bridge_mode_match = re.search(
            r"Brief information on interfaces in bridge mode:.*?(?=Brief information|$)",
            output,
            re.DOTALL,
        )

        if not bridge_mode_match:
            return ports

        bridge_section = bridge_mode_match.group(0)

        # 解析每个端口行
        port_pattern = re.compile(
            r"^(GE\d+/\d+/\d+|XGE\d+/\d+/\d+)\s+"  # 接口名称
            r"(UP|DOWN|ADM)\s+"  # 链路状态
            r"(\S+)\s+"  # 速率
            r"(\S+)\s+"  # 双工
            r"([ATH])\s+"  # 类型
            r"(\d+)[ ]*"  # PVID (只匹配空格，不匹配换行符)
            r"([^\n]*)$",  # 描述 (不跨行匹配)
            re.MULTILINE,
        )

        for match in port_pattern.finditer(bridge_section):
            name = match.group(1)
            status = match.group(2)
            speed = match.group(3)
            duplex = match.group(4)
            port_type = match.group(5)
            pvid = int(match.group(6))
            description = match.group(7).strip() if match.group(7) else None

            # 标准化状态
            if status == "ADM":
                status = "adm"
            elif status == "UP":
                status = "up"
            else:
                status = "down"

            # 标准化类型
            type_map = {"A": "access", "T": "trunk", "H": "hybrid"}
            port_type_normalized = type_map.get(port_type, port_type)

            # 标准化双工模式
            duplex_clean = duplex.replace("(a)", "").replace("A", "")
            if duplex_clean.startswith("F"):
                duplex_normalized = "full"
            elif duplex_clean.startswith("H"):
                duplex_normalized = "half"
            else:
                duplex_normalized = duplex_clean

            ports.append(
                PortInfo(
                    name=name,
                    status=status,
                    speed=speed if speed != "auto" else None,
                    duplex=duplex_normalized,
                    port_type=port_type_normalized,
                    pvid=pvid,
                    description=description if description else None,
                )
            )

        return ports

    def _parse_mac_address(self, output: str) -> Dict[str, List[MacAddressInfo]]:
        """
        解析 dis mac-address 命令输出

        返回 {端口名: [MacAddressInfo列表]} 的映射
        """
        mac_map: Dict[str, List[MacAddressInfo]] = {}

        # 解析每行 MAC 地址记录
        mac_pattern = re.compile(
            r"([0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4})\s+"  # MAC 地址
            r"(\d+)\s+"  # VLAN ID
            r"\w+\s+"  # State (Learned/Static等)
            r"(GE\d+/\d+/\d+|XGE\d+/\d+/\d+|GigabitEthernet\d+/\d+/\d+)"  # Port
            r"\s*[YN]?",  # Aging (可选)
            re.MULTILINE | re.IGNORECASE,
        )

        for match in mac_pattern.finditer(output):
            mac = match.group(1)
            vlan = int(match.group(2))
            port = match.group(3)

            # 标准化端口名称：将 GigabitEthernet 转换为 GE
            if port.startswith("GigabitEthernet"):
                port_num = port[len("GigabitEthernet"):]
                port = f"GE{port_num}"

            if port not in mac_map:
                mac_map[port] = []
            mac_map[port].append(MacAddressInfo(mac=mac, vlan=vlan))
            logger.debug(f"解析到MAC地址: {mac} -> 端口: {port}, VLAN: {vlan}")

        return mac_map

    def _parse_dot1x_sessions(self, output: str) -> Dict[str, List[Dot1XUserInfo]]:
        """
        解析 dis dot1x sessions 命令输出

        返回 {端口名: [dot1X用户列表]} 的映射
        """
        dot1x_map: Dict[str, List[Dot1XUserInfo]] = {}

        # 解析每个端口的 dot1X 会话
        session_pattern = re.compile(
            r"(?:Gigabit)?(?:Ethernet)?(\d+/\d+/\d+)\s+is\s+(link-up|link-down)\s*\n"
            r"\s*Online\s+802\.1X\s+users:\s*(\d+)\s*\n"
            r"(.*?)(?=\n\s*(?:Gigabit)?(?:Ethernet)?\d+/\d+/\d+\s+is|$)",
            re.DOTALL | re.IGNORECASE,
        )

        for match in session_pattern.finditer(output):
            port_num = match.group(1)
            # 构建标准端口名 (GE1/0/37)
            port_name = f"GE{port_num}"
            user_count = int(match.group(3))
            content_block = match.group(4) if match.group(4) else ""

            users = []
            if user_count > 0 and content_block:
                # 从内容块中提取MAC地址
                user_pattern = re.compile(
                    r"^\s*([0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4})\s+(\w+).*$",
                    re.MULTILINE | re.IGNORECASE,
                )
                for user_match in user_pattern.finditer(content_block):
                    users.append(
                        Dot1XUserInfo(
                            mac=user_match.group(1),
                            auth_state=user_match.group(2),
                        )
                    )

            dot1x_map[port_name] = users

        return dot1x_map


class SwitchService:
    """
    交换机服务类
    根据资产平台名称路由到对应的处理器
    """

    def __init__(self):
        # 注册处理器
        self.handlers: Dict[str, BaseSwitchHandler] = {
            "UniFi": UniFiSwitchHandler(),
            # 预留其他品牌扩展
            # "Huawei": HuaweiSwitchHandler(),
            # "H3C": H3CSwitchHandler(),
        }

    def get_port_info(self, switch_ip: str, platform_name: str = "UniFi", progress_callback: Optional[Callable] = None) -> Dict:
        """
        获取交换机端口信息

        Args:
            switch_ip: 交换机 IP 地址
            platform_name: 平台名称，用于选择处理器
            progress_callback: 进度回调函数

        Returns:
            包含 device_info 和 ports 的字典
        """
        handler = self.handlers.get(platform_name)

        if handler is None:
            logger.warning(f"未找到平台 '{platform_name}' 的处理器，使用默认处理器")
            # 默认使用紫光交换机处理器
            handler = self.handlers.get("UniFi")

        if handler is None:
            return {
                "device_info": None,
                "ports": [],
                "message": f"不支持的平台: {platform_name}",
            }

        return handler.fetch_port_info(switch_ip, progress_callback)


# 全局服务实例
_switch_service = None


def get_switch_service() -> SwitchService:
    """获取交换机服务单例"""
    global _switch_service
    if _switch_service is None:
        _switch_service = SwitchService()
    return _switch_service
