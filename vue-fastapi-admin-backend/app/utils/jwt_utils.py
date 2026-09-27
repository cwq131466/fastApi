import jwt
from jwt.exceptions import PyJWTError

from app.schemas.login import JWTPayload
from app.settings.config import settings


def create_access_token(*, data: JWTPayload):
    payload = data.model_dump().copy()
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    解码 JWT token
    
    Args:
        token: JWT token 字符串
        
    Returns:
        解码后的 payload 字典
        
    Raises:
        jwt.ExpiredSignatureError: token 已过期
        jwt.InvalidTokenError: token 无效
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except PyJWTError as e:
        raise e
