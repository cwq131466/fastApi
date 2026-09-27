"""
交换机端口认证服务模块
提供通过 JumpServer 跳板机 SSH 登录交换机，开启/关闭端口 dot1x 认证的功能
支持多品牌扩展架构
"""
import re
from abc import ABC, abstractmethod
from typing import Dict, Optional

from loguru import logger

# JumpServer 跳板机配置
JUMPSERVER_HOST = "32.15.64.5"
JUMPSERVER_PORT = 2222
SSH_PASSWORD = "Gfdx_api@12345"


class BasePortAuthHandler(ABC):
    """端口认证处理器基类"""

    def _connect_ssh(self, username: str, password: str):
        """
        通过 JumpServer 建立 SSH 连接

        Args:
            username: JumpServer 用户名（格式：XXX@admin@switch_ip）
            password: JumpServer 密码

        Returns:
            paramiko.SSHClient 实例
        """
        try:
            import paramiko
        except ImportError:
            raise ImportError("paramiko 未安装，请运行: pip install paramiko")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        logger.info(f"正在通过 JumpServer 连接: {username}")

        ssh.connect(
            hostname=JUMPSERVER_HOST,
            port=JUMPSERVER_PORT,
            username=username,
            password=password,
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

    @abstractmethod
    def toggle_port_dot1x(
        self,
        ssh,
        switch_ip: str,
        port_name: str,
        enable: bool,
    ) -> Dict:
        """
        开启或关闭交换机端口的 dot1x 认证

        Args:
            ssh: 已建立的 SSH 连接
            switch_ip: 交换机 IP 地址
            port_name: 端口名称
            enable: True 为开启，False 为关闭

        Returns:
            包含操作结果和验证信息的字典
        """
        pass

    def _check_port_dot1x_status(self, output: str, port_name: str) -> bool:
        """
        检查指定端口的 dot1x 状态

        Args:
            output: dis dot1x sessions 命令输出
            port_name: 端口名称

        Returns:
            True 表示 dot1x 已启用，False 表示未启用
        """
        # 标准化端口名称（将 GE 转换为 GigabitEthernet）
        normalized_port = port_name
        if port_name.startswith("GE"):
            normalized_port = f"GigabitEthernet{port_name[2:]}"
        elif port_name.startswith("XGE"):
            normalized_port = f"Ten-GigabitEthernet{port_name[3:]}"

        # 查找该端口的 dot1x 会话信息
        pattern = re.compile(
            rf"{re.escape(normalized_port)}\s+is\s+(link-up|link-down)\s*\n"
            r"\s*Online\s+802\.1X\s+users:\s*(\d+)",
            re.IGNORECASE,
        )

        match = pattern.search(output)
        if match:
            user_count = int(match.group(2))
            return True

        return False


class UniswapPortAuthHandler(BasePortAuthHandler):
    """紫光交换机端口认证处理器"""

    def toggle_port_dot1x(
        self,
        ssh,
        switch_ip: str,
        port_name: str,
        enable: bool,
    ) -> Dict:
        """
        紫光交换机：开启或关闭端口 dot1x 认证

        Args:
            ssh: 已建立的 SSH 连接
            switch_ip: 交换机 IP 地址
            port_name: 端口名称（如 GigabitEthernet1/0/37）
            enable: True 为开启，False 为关闭

        Returns:
            包含操作结果和验证信息的字典
        """
        try:
            # 构建配置命令（将所有命令合并为一条，用换行符分隔）
            if enable:
                # 开启 dot1x
                config_commands = (
                    f"system-view\n"
                    f"interface {port_name}\n"
                    f"dot1x\n"
                    f"undo dot1x handshake\n"
                    f"dot1x mandatory-domain dm1\n"
                    f"undo dot1x multicast-trigger\n"
                    f"dot1x port-method portbased\n"
                    f"return\n"
                )
            else:
                # 关闭 dot1x
                config_commands = (
                    f"system-view\n"
                    f"interface {port_name}\n"
                    f"undo dot1x\n"
                    f"return\n"
                )

            logger.info(f"执行配置命令:\n{config_commands}")

            # 一次性执行所有配置命令
            output = self._execute_command(ssh, config_commands)
            logger.debug(f"配置命令输出: {output[:500]}")

            # 等待配置生效
            import time
            time.sleep(2)

            # 验证配置结果
            verify_output = self._execute_command(ssh, "dis dot1x sessions")
            logger.info(f"验证 dot1x 状态:\n{verify_output}")

            # 解析验证结果
            is_enabled = self._check_port_dot1x_status(verify_output, port_name)

            return {
                "success": True,
                "action": "enable" if enable else "disable",
                "port": port_name,
                "switch_ip": switch_ip,
                "dot1x_enabled": is_enabled,
                "verify_output": verify_output,
                "message": f"端口 {port_name} dot1x {'已开启' if enable else '已关闭'}",
            }

        except Exception as e:
            logger.error(f"端口 dot1x 配置失败: {e}", exc_info=True)
            return {
                "success": False,
                "action": "enable" if enable else "disable",
                "port": port_name,
                "switch_ip": switch_ip,
                "message": f"操作失败: {str(e)}",
            }


class PortAuthService:
    """
    端口认证服务类
    根据交换机平台名称路由到对应的处理器
    """

    def __init__(self):
        # 注册处理器
        self.handlers: Dict[str, BasePortAuthHandler] = {
            "UniFi": UniswapPortAuthHandler(),
            # 预留其他品牌扩展
            # "Huawei": HuaweiPortAuthHandler(),
            # "H3C": H3CPortAuthHandler(),
        }

    def toggle_port_dot1x(
        self,
        switch_ip: str,
        port_name: str,
        enable: bool,
        jumpserver_username: str,
        jumpserver_password: str,
        platform_name: str = "UniFi",
    ) -> Dict:
        """
        开启或关闭交换机端口的 dot1x 认证

        Args:
            switch_ip: 交换机 IP 地址
            port_name: 端口名称（如 GigabitEthernet1/0/37）
            enable: True 为开启，False 为关闭
            jumpserver_username: JumpServer 用户名（不含 net_api@admin@ 前缀）
            jumpserver_password: JumpServer 密码
            platform_name: 平台名称，用于选择处理器

        Returns:
            包含操作结果和验证信息的字典
        """
        handler = self.handlers.get(platform_name)

        if handler is None:
            logger.warning(f"未找到平台 '{platform_name}' 的处理器，使用默认处理器")
            handler = self.handlers.get("UniFi")

        if handler is None:
            return {
                "success": False,
                "action": "enable" if enable else "disable",
                "port": port_name,
                "switch_ip": switch_ip,
                "message": f"不支持的平台: {platform_name}",
            }

        ssh = None
        try:
            # 构建完整的 JumpServer 用户名
            full_username = f"{jumpserver_username}@admin@{switch_ip}"
            # 建立 SSH 连接
            ssh = handler._connect_ssh(full_username, jumpserver_password)

            # 调用对应平台的处理器
            return handler.toggle_port_dot1x(ssh, switch_ip, port_name, enable)

        except Exception as e:
            logger.error(f"端口 dot1x 配置失败: {e}", exc_info=True)
            return {
                "success": False,
                "action": "enable" if enable else "disable",
                "port": port_name,
                "switch_ip": switch_ip,
                "message": f"操作失败: {str(e)}",
            }
        finally:
            if ssh:
                ssh.close()


# 全局服务实例
_port_auth_service = None


def get_port_auth_service() -> PortAuthService:
    """获取端口认证服务单例"""
    global _port_auth_service
    if _port_auth_service is None:
        _port_auth_service = PortAuthService()
    return _port_auth_service
