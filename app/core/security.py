"""
인증 및 보안 관련 기능을 관리하는 모듈
- API 키
- JWT 토큰
- 인증 의존성
"""

from fastapi.security.api_key import APIKeyHeader
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from app.core.yaml_config import yaml_settings

# 인증 스키마 메타데이터 설정
api_key_header_name = yaml_settings.api.auth.api_key.header_name
api_key_prefix = yaml_settings.api.auth.api_key.prefix.strip()
api_key_header_description = f"API 키 인증 ({api_key_header_name} 헤더에 '{api_key_prefix}your-api-key' 형식으로 전달)"

jwt_token_description = "JWT 인증 (Authorization 헤더에 'Bearer your-token' 형식으로 전달)"
jwt_token_url = yaml_settings.api.auth.jwt.token_url

# 전역에서 사용할 인증 헤더 의존성
global_auth_header = APIKeyHeader(
    name="Authorization",
    auto_error=False,
    description="모든 인증 방식(JWT, API Key, Custom Header)을 지원하는 전역 인증 헤더"
)