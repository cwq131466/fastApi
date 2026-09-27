"""
JumpServer API 客户端服务
基于 drf-httpsig 模块进行 AccessKey/SecretKey 认证
"""
import datetime
import logging
from typing import Dict, List, Optional

import requests
from httpsig.requests_auth import HTTPSignatureAuth

from app.settings.config import settings
from app.core.exceptions import JumpServerAuthError, JumpServerConnectionError

logger = logging.getLogger(__name__)


class JumpServerClient:
    """JumpServer API 客户端"""

    def __init__(
        self,
        url: str = None,
        access_key_id: str = None,
        access_key_secret: str = None,
        org_id: str = None,
        verify_ssl: bool = None,
    ):
        """
        初始化 JumpServer 客户端

        Args:
            url: JumpServer 服务器地址
            access_key_id: Access Key ID
            access_key_secret: Access Key Secret
            org_id: 组织ID
            verify_ssl: 是否验证 SSL 证书
        """
        self.base_url = url or settings.JUMPSERVER_URL
        self.access_key_id = access_key_id or settings.ACCESS_KEY_ID
        self.access_key_secret = access_key_secret or settings.ACCESS_KEY_SECRET
        self.org_id = org_id or settings.ORG_ID
        self.verify_ssl = verify_ssl if verify_ssl is not None else settings.VERIFY_SSL

        # 创建认证对象
        self.auth = self._create_auth()

    def _create_auth(self) -> HTTPSignatureAuth:
        """创建 HTTP 签名认证对象"""
        signature_headers = ["(request-target)", "accept", "date"]
        return HTTPSignatureAuth(
            key_id=self.access_key_id,
            secret=self.access_key_secret,
            algorithm="hmac-sha256",
            headers=signature_headers,
        )

    def _get_headers(self) -> Dict[str, str]:
        """构建请求头"""
        gmt_format = "%a, %d %b %Y %H:%M:%S GMT"
        headers = {
            "Accept": "application/json",
            "Date": datetime.datetime.utcnow().strftime(gmt_format),
        }

        # 如果指定了组织ID，添加组织头
        if self.org_id:
            headers["X-JMS-ORG"] = self.org_id

        return headers

    def test_authentication(self) -> bool:
        """
        测试认证是否有效

        Returns:
            bool: 认证是否成功

        Raises:
            JumpServerAuthError: 认证失败
            JumpServerConnectionError: 连接失败
        """
        url = f"{self.base_url}/api/v1/users/users/"
        headers = self._get_headers()
        params = {"limit": 1}

        try:
            response = requests.get(
                url, auth=self.auth, headers=headers, params=params, verify=self.verify_ssl
            )

            if response.status_code == 200:
                logger.info("JumpServer 认证成功")
                return True
            elif response.status_code == 401:
                raise JumpServerAuthError("无效的 AccessKey")
            elif response.status_code == 403:
                raise JumpServerAuthError("权限不足：该用户没有API访问权限")
            else:
                raise JumpServerConnectionError(
                    f"认证测试失败，状态码: {response.status_code}"
                )

        except requests.exceptions.SSLError as e:
            raise JumpServerConnectionError(f"SSL证书错误: {e}")
        except requests.exceptions.ConnectionError as e:
            raise JumpServerConnectionError(f"无法连接到 JumpServer: {e}")
        except JumpServerAuthError:
            raise
        except Exception as e:
            raise JumpServerConnectionError(f"认证测试异常: {e}")

    def get_assets(
        self, limit: int = 100, offset: int = 0, keyword: str = None
    ) -> Dict:
        """
        获取资产列表

        Args:
            limit: 每页数量
            offset: 偏移量
            keyword: 搜索关键词

        Returns:
            Dict: 包含资产列表和总数的字典

        Raises:
            JumpServerAuthError: 认证失败
            JumpServerConnectionError: 连接失败
        """
        # 尝试多个可能的 API 端点
        endpoints_to_try = [
            "/api/v1/assets/assets/",  # 标准资产接口
            "/api/v1/perms/users/self/assets/",  # 用户授权资产接口
        ]

        last_error = None

        for endpoint in endpoints_to_try:
            url = f"{self.base_url}{endpoint}"
            headers = self._get_headers()
            params = {"limit": limit, "offset": offset}

            if keyword:
                params["search"] = keyword

            try:
                logger.info(f"尝试访问 JumpServer API: {url}")
                response = requests.get(
                    url, auth=self.auth, headers=headers, params=params, verify=self.verify_ssl
                )

                logger.info(f"JumpServer 响应状态码: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"成功获取资产数据")

                    # 处理不同的响应格式
                    if isinstance(data, dict):
                        return {
                            "results": data.get("results", []),
                            "count": data.get("count", 0),
                            "next": data.get("next"),
                            "previous": data.get("previous"),
                        }
                    elif isinstance(data, list):
                        return {"results": data, "count": len(data)}
                    else:
                        return {"results": [], "count": 0}
                elif response.status_code == 401:
                    raise JumpServerAuthError("认证失败：无效的 AccessKey")
                elif response.status_code == 403:
                    raise JumpServerAuthError("权限不足")
                else:
                    # 记录错误但继续尝试下一个端点
                    error_msg = f"访问 {endpoint} 失败，状态码: {response.status_code}, 响应: {response.text[:200]}"
                    logger.warning(error_msg)
                    last_error = JumpServerConnectionError(
                        f"获取资产失败，状态码: {response.status_code}"
                    )
                    continue  # 尝试下一个端点

            except (JumpServerAuthError, JumpServerConnectionError) as e:
                logger.warning(f"访问 {endpoint} 异常: {e}")
                last_error = e
                if isinstance(e, JumpServerAuthError):
                    raise  # 认证错误不需要尝试其他端点
                continue
            except requests.exceptions.SSLError as e:
                raise JumpServerConnectionError(f"SSL证书错误: {e}")
            except requests.exceptions.ConnectionError as e:
                raise JumpServerConnectionError(f"无法连接到 JumpServer: {e}")
            except Exception as e:
                last_error = JumpServerConnectionError(f"获取资产异常: {e}")
                continue

        # 所有端点都失败了
        if last_error:
            raise last_error
        else:
            raise JumpServerConnectionError("无法获取资产列表")

    def get_asset_detail(self, asset_id: str) -> Optional[Dict]:
        """
        获取单个资产的详细信息

        Args:
            asset_id: 资产ID

        Returns:
            Dict: 资产详情，如果不存在返回 None

        Raises:
            JumpServerAuthError: 认证失败
            JumpServerConnectionError: 连接失败
        """
        url = f"{self.base_url}/api/v1/assets/assets/{asset_id}/"
        headers = self._get_headers()

        try:
            response = requests.get(
                url, auth=self.auth, headers=headers, verify=self.verify_ssl
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            elif response.status_code == 401:
                raise JumpServerAuthError("认证失败：无效的 AccessKey")
            elif response.status_code == 403:
                raise JumpServerAuthError("权限不足")
            else:
                raise JumpServerConnectionError(
                    f"获取资产详情失败，状态码: {response.status_code}"
                )

        except (JumpServerAuthError, JumpServerConnectionError):
            raise
        except requests.exceptions.SSLError as e:
            raise JumpServerConnectionError(f"SSL证书错误: {e}")
        except requests.exceptions.ConnectionError as e:
            raise JumpServerConnectionError(f"无法连接到 JumpServer: {e}")
        except Exception as e:
            raise JumpServerConnectionError(f"获取资产详情异常: {e}")

    def get_my_assets(self) -> List[Dict]:
        """
        获取当前用户授权的资产

        Returns:
            List[Dict]: 资产列表

        Raises:
            JumpServerAuthError: 认证失败
            JumpServerConnectionError: 连接失败
        """
        url = f"{self.base_url}/api/v1/users/my/assets/"
        headers = self._get_headers()

        try:
            response = requests.get(
                url, auth=self.auth, headers=headers, verify=self.verify_ssl
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "results" in data:
                    return data["results"]
                elif isinstance(data, list):
                    return data
                else:
                    return []
            elif response.status_code == 401:
                raise JumpServerAuthError("认证失败：无效的 AccessKey")
            elif response.status_code == 403:
                raise JumpServerAuthError("权限不足")
            else:
                raise JumpServerConnectionError(
                    f"获取用户资产失败，状态码: {response.status_code}"
                )

        except (JumpServerAuthError, JumpServerConnectionError):
            raise
        except requests.exceptions.SSLError as e:
            raise JumpServerConnectionError(f"SSL证书错误: {e}")
        except requests.exceptions.ConnectionError as e:
            raise JumpServerConnectionError(f"无法连接到 JumpServer: {e}")
        except Exception as e:
            raise JumpServerConnectionError(f"获取用户资产异常: {e}")


# 创建全局客户端实例（懒加载）
_client_instance = None


def get_jumpserver_client() -> JumpServerClient:
    """
    获取 JumpServer 客户端实例（单例模式）

    Returns:
        JumpServerClient: 客户端实例
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = JumpServerClient()
    return _client_instance
