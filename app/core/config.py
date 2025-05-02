"""
애플리케이션 설정 관리 모듈
"""
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseSettings, Field

class LoggingSettings(BaseSettings):
    """로깅 관련 설정"""
    LEVEL: str = Field("INFO", env="LOG_LEVEL")
    CONSOLE: bool = Field(True, env="LOG_CONSOLE")
    FILE_ENABLED: bool = Field(False, env="LOG_FILE_ENABLED")
    FILE_PATH: Optional[str] = Field(None, env="LOG_FILE_PATH")
    JSON_ENABLED: bool = Field(False, env="LOG_JSON_ENABLED")
    JSON_FILE_PATH: Optional[str] = Field(None, env="LOG_JSON_FILE_PATH")
    DETAILED_FORMAT: bool = Field(False, env="LOG_DETAILED_FORMAT")
    
    # HTTP 요청/응답 로깅 설정
    REQUEST_BODY: bool = Field(True, env="LOG_REQUEST_BODY")
    RESPONSE_BODY: bool = Field(True, env="LOG_RESPONSE_BODY")
    MAX_BODY_LENGTH: int = Field(10000, env="LOG_MAX_BODY_LENGTH")
    SENSITIVE_FIELDS: List[str] = Field(
        ["password", "token", "authorization", "api_key", "secret"],
        env="LOG_SENSITIVE_FIELDS"
    )
    
    class Config:
        env_prefix = ""
        case_sensitive = True
        env_file = ".env"
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            """환경 변수 파싱 커스터마이징"""
            if field_name == "SENSITIVE_FIELDS" and raw_val:
                return [field.strip() for field in raw_val.split(",")]
            return cls.json_loads(raw_val)

class Settings(BaseSettings):
    """애플리케이션 설정"""
    # 기본 설정
    APP_NAME: str = Field("FastAPI Boilerplate", env="APP_NAME")
    APP_ENV: str = Field("dev", env="APP_ENV")
    DEBUG: bool = Field(False, env="DEBUG")
    
    # 로깅 설정
    logging: LoggingSettings = LoggingSettings()
    
    # API 설정
    API_PREFIX: str = Field("/api", env="API_PREFIX")
    
    # 여기에 필요한 다른 설정 추가
    # DB_URL, CACHE_URL 등
    
    class Config:
        env_prefix = ""
        case_sensitive = True
        env_file = ".env"

# 설정 인스턴스 생성
settings = Settings()

# Log level 매핑
LOG_LEVEL_MAP = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

def get_log_level() -> int:
    """설정에서 로그 레벨 정수 값을 가져옵니다"""
    return LOG_LEVEL_MAP.get(settings.logging.LEVEL, 20)  # 기본값 INFO(20) 