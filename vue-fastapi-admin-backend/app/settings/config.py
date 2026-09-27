import os
import typing

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    VERSION: str = "0.1.0"
    APP_TITLE: str = "Vue FastAPI Admin"
    T_NAME: str = "Vue FastAPI Admin"
    APP_DESCRIPTION: str = "Description"

    CORS_ORIGINS: typing.List = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["*"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]

    DEBUG: bool = True

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    SECRET_KEY: str = "3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf"  # openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 day
    
    # OAuth2 统一认证配置
    OAUTH_ENABLED: bool = os.getenv("OAUTH_ENABLED", "false").lower() == "true"
    OAUTH_CLIENT_ID: str = os.getenv("OAUTH_CLIENT_ID", "")
    OAUTH_CLIENT_SECRET: str = os.getenv("OAUTH_CLIENT_SECRET", "")
    OAUTH_SERVER_BASE_URL: str = os.getenv("OAUTH_SERVER_BASE_URL", "http://32.15.80.150:99/oauth2Server")
    OAUTH_AUTHORIZE_ENDPOINT: str = "/oauth2/authorize"
    OAUTH_TOKEN_ENDPOINT: str = "/oauth2/token"
    OAUTH_USERINFO_ENDPOINT: str = "/oauth2/userinfo"
    OAUTH_CHECKLOGIN_ENDPOINT: str = "/oauth2/checkLogin"
    OAUTH_LOGOUT_ENDPOINT: str = "/oauth2/logout"
    # 后端回调地址（统一认证服务回调到这里）
    OAUTH_REDIRECT_URI: str = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:9099/api/v1/auth/oauth2/callback")
    # 前端地址（后端处理后重定向到这里）
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    # 多前端 URL 配置（逗号分隔，用于支持多个前端共用同一后端）
    FRONTEND_URLS: str = os.getenv("FRONTEND_URLS", "http://localhost:5173,http://localhost:3100")
    VERIFY_SSL: bool = os.getenv("VERIFY_SSL", "false").lower() == "true"
    
    # JumpServer 配置（用于交换机管理）
    JUMPSERVER_URL: str = os.getenv("JUMPSERVER_URL", "http://32.15.64.5")
    ACCESS_KEY_ID: str = os.getenv("ACCESS_KEY_ID", "")
    ACCESS_KEY_SECRET: str = os.getenv("ACCESS_KEY_SECRET", "")
    ORG_ID: str = os.getenv("ORG_ID", "")
    
    # Database Configuration
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite").lower()
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "vue_fastapi_admin")
    
    @property
    def TORTOISE_ORM(self) -> dict:
        """根据环境变量动态配置数据库连接"""
        if self.DB_TYPE == "mysql":
            default_connection = "mysql"
            connections = {
                "mysql": {
                    "engine": "tortoise.backends.mysql",
                    "credentials": {
                        "host": self.DB_HOST,
                        "port": self.DB_PORT,
                        "user": self.DB_USER,
                        "password": self.DB_PASSWORD,
                        "database": self.DB_NAME,
                    },
                },
            }
        else:  # Default to SQLite
            default_connection = "sqlite"
            connections = {
                "sqlite": {
                    "engine": "tortoise.backends.sqlite",
                    "credentials": {"file_path": f"{self.BASE_DIR}/db.sqlite3"},
                },
            }
        
        return {
            "connections": connections,
            "apps": {
                "models": {
                    "models": ["app.models", "aerich.models"],
                    "default_connection": default_connection,
                },
            },
            "use_tz": False,
            "timezone": "Asia/Shanghai",
        }
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"


settings = Settings()
