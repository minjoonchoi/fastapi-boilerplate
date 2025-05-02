"""
YAML 기반 애플리케이션 설정 관리 모듈
"""
import os
import yaml
import logging
from typing import Dict, Any, Optional, List, Set, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
from copy import deepcopy

# 기본 설정 파일 경로
DEFAULT_CONFIG_PATH = "config.yaml"
COMMON_CONFIG_PATH = "config.common.yaml"

# 모듈 로거 설정 (초기화만 하고 핸들러는 추가하지 않음)
logger = logging.getLogger("yaml_config")

class LoggingFileConfig(BaseModel):
    """로깅 파일 관련 설정"""
    enabled: bool = False
    path: Optional[str] = None

class LoggingJsonConfig(BaseModel):
    """JSON 로깅 관련 설정"""
    enabled: bool = False
    file_path: Optional[str] = None

class LoggingHttpConfig(BaseModel):
    """HTTP 요청/응답 로깅 관련 설정"""
    request_body: bool = True
    response_body: bool = True
    max_body_length: int = 10000
    sensitive_fields: List[str] = [
        "password", "token", "authorization", "api_key", "secret"
    ]
    exclude_patterns: List[str] = [
        "/health/**",  # 모든 헬스 체크 관련 경로
        "/metrics",    # 메트릭 경로 (정확한 매칭)
        "/docs/**",    # Swagger UI 문서 관련 모든 경로
        "/redoc/**",   # ReDoc 문서 관련 모든 경로
        "/openapi.json" # OpenAPI 스키마 파일 (정확한 매칭)
    ]

class LoggingConfig(BaseModel):
    """로깅 관련 설정"""
    level: str = "INFO"
    console: bool = True
    format: str = "text"  # 'text' 또는 'json'
    detailed_format: bool = False
    file: LoggingFileConfig = LoggingFileConfig()
    json_config: LoggingJsonConfig = LoggingJsonConfig()
    http: LoggingHttpConfig = LoggingHttpConfig()

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        """로그 포맷 검증"""
        if v.lower() not in ['text', 'json']:
            raise ValueError("로그 포맷은 'text' 또는 'json' 중 하나여야 합니다.")
        return v.lower()

    @property
    def file_path(self) -> Optional[str]:
        """파일 로깅 경로 가져오기"""
        if self.file.enabled:
            return self.file.path
        return None
    
    @property
    def json_file_path(self) -> Optional[str]:
        """JSON 로깅 파일 경로 가져오기"""
        if self.json_config.enabled:
            return self.json_config.file_path
        return None
    
    @property
    def sensitive_fields_set(self) -> Set[str]:
        """민감 필드 Set으로 변환"""
        return set(self.http.sensitive_fields)

class JwtAuthConfig(BaseModel):
    """JWT 인증 관련 설정"""
    enabled: bool = False
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    token_url: str = "/api/auth/token"
    exclude_patterns: List[str] = [
        "/health/**",    # 모든 헬스 체크 관련 경로
        "/metrics",      # 메트릭 경로 (정확한 매칭)
        "/docs/**",      # Swagger UI 문서 관련 모든 경로
        "/redoc/**",     # ReDoc 문서 관련 모든 경로
        "/openapi.json", # OpenAPI 스키마 파일 (정확한 매칭)
        "/api/auth/token" # 로그인 엔드포인트
    ]

class ApiKeyAuthConfig(BaseModel):
    """API 키 인증 관련 설정"""
    enabled: bool = True
    header_name: str = "Authorization"
    prefix: str = "ApiKey "
    key: Optional[str] = None
    exclude_patterns: List[str] = [
        "/health/**",   # 모든 헬스 체크 관련 경로
        "/metrics",     # 메트릭 경로 (정확한 매칭)
        "/docs/**",     # Swagger UI 문서 관련 모든 경로
        "/redoc/**",    # ReDoc 문서 관련 모든 경로
        "/openapi.json" # OpenAPI 스키마 파일 (정확한 매칭)
    ]
    
    @property
    def api_key(self) -> Optional[str]:
        """
        API 키를 환경변수에서 가져오기
        
        API 키는 항상 환경변수 API_KEY에서만 가져옵니다.
        환경변수가 설정되지 않은 경우 None을 반환합니다.
        
        Returns:
            API 키 문자열 또는 None
        """
        # 환경변수에서 API 키 가져오기
        return os.environ.get("API_KEY")

class ApiAuthConfig(BaseModel):
    """API 인증 관련 설정"""
    api_key: ApiKeyAuthConfig = ApiKeyAuthConfig()
    jwt: JwtAuthConfig = JwtAuthConfig()

class ApiConfig(BaseModel):
    """API 관련 설정"""
    prefix: str = "/api"
    auth: ApiAuthConfig = ApiAuthConfig()

class AppConfig(BaseModel):
    """앱 기본 설정"""
    name: str = "FastAPI Boilerplate"
    env: str = "dev"
    debug: bool = False

class DatabaseConfig(BaseModel):
    """데이터베이스 설정 (예시)"""
    url: Optional[str] = None
    pool_size: int = 5
    max_overflow: int = 10

class TestConfig(BaseModel):
    """테스트 관련 설정"""
    mock_enabled: bool = False
    temp_dir: str = "tests/temp"

class UploadConfig(BaseModel):
    """파일 업로드 관련 설정"""
    path: str = "uploads"
    max_file_size: int = 10485760  # 10MB
    max_total_size: int = 52428800  # 50MB
    allowed_extensions: List[str] = []  # 빈 배열은 모든 확장자 허용

class YamlSettings(BaseModel):
    """YAML 기반 애플리케이션 설정"""
    app: AppConfig = AppConfig()
    api: ApiConfig = ApiConfig()
    logging: LoggingConfig = LoggingConfig()
    database: Optional[DatabaseConfig] = None
    test: Optional[TestConfig] = None
    upload: UploadConfig = UploadConfig()

    @model_validator(mode='after')
    def validate_paths(self) -> 'YamlSettings':
        """파일 경로 검증"""
        # 로그 디렉토리 생성
        if self.logging.file_path:
            log_dir = os.path.dirname(self.logging.file_path)
            os.makedirs(log_dir, exist_ok=True)
            
        if self.logging.json_file_path:
            json_log_dir = os.path.dirname(self.logging.json_file_path)
            os.makedirs(json_log_dir, exist_ok=True)
            
        return self

def get_config_path() -> str:
    """
    설정 파일 경로 결정
    
    1. CONFIG_PATH 환경 변수
    2. APP_ENV를 기반으로 config.<env>.yaml 파일
    3. 기본 config.yaml 파일
    
    Returns:
        설정 파일 경로
    """
    # 1. CONFIG_PATH 환경 변수 확인
    config_path = os.environ.get("CONFIG_PATH")
    if config_path and os.path.exists(config_path):
        logger.info(f"설정 파일 사용: {config_path} (CONFIG_PATH 환경 변수)")
        return config_path
    
    # 2. APP_ENV를 기반으로 파일 경로 생성
    app_env = os.environ.get("APP_ENV", "dev").lower()
    env_config_path = f"config.{app_env}.yaml"
    if os.path.exists(env_config_path):
        logger.info(f"설정 파일 사용: {env_config_path} (APP_ENV={app_env})")
        return env_config_path
    
    # 3. 기본 설정 파일
    if os.path.exists(DEFAULT_CONFIG_PATH):
        logger.info(f"기본 설정 파일 사용: {DEFAULT_CONFIG_PATH}")
        return DEFAULT_CONFIG_PATH
    
    # 4. 설정 파일을 찾을 수 없는 경우
    logger.warning(f"설정 파일을 찾을 수 없습니다. 기본 설정값 사용.")
    return DEFAULT_CONFIG_PATH

def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """
    두 딕셔너리를 재귀적으로 병합합니다.
    dict2의 값이 dict1의 값을 덮어씁니다.
    
    특수 규칙:
    1. dict2의 값이 None이면 dict1의 값을 사용합니다.
    2. dict2의 값이 '__reset__'이면 기본값이나 빈 값으로 재설정합니다.
    3. 두 값이 모두 딕셔너리인 경우 재귀적으로 병합합니다.
    4. 두 값이 모두 리스트인 경우 dict2의 리스트가 dict1의 리스트를 완전히 대체합니다.
    5. 그 외의 경우 dict2의 값이 dict1의 값을 대체합니다.
    
    Args:
        dict1: 기본 딕셔너리 (공통 설정)
        dict2: 덮어쓸 딕셔너리 (환경별 설정)
        
    Returns:
        병합된 딕셔너리
    """
    # dict1의 복사본으로 시작
    result = deepcopy(dict1)
    
    # dict2의 모든 키와 값에 대해
    for key, value in dict2.items():
        # 특수 값 처리
        if value is None:
            # None 값은 덮어쓰지 않음 (기존 값 유지)
            continue
            
        if isinstance(value, str) and value == '__reset__':
            # __reset__ 값은 해당 키를 초기화 (비우거나 기본값으로 설정)
            if key in result:
                if isinstance(result[key], dict):
                    result[key] = {}
                elif isinstance(result[key], list):
                    result[key] = []
                elif isinstance(result[key], str):
                    result[key] = ""
                elif isinstance(result[key], (int, float)):
                    result[key] = 0
                elif isinstance(result[key], bool):
                    result[key] = False
                else:
                    result[key] = None
            continue
            
        # 일반 값 처리
        if key in result:
            # 두 값이 모두 딕셔너리인 경우 재귀적으로 병합
            if isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            # 그 외의 경우 (리스트, 문자열, 숫자 등) 환경별 설정이 공통 설정을 덮어씀
            else:
                result[key] = deepcopy(value)
        else:
            # result에 키가 없는 경우 그냥 추가
            result[key] = deepcopy(value)
            
    return result

def load_common_config() -> Dict[str, Any]:
    """
    공통 설정 파일 로드
    
    Returns:
        공통 설정 데이터 딕셔너리
    """
    try:
        if os.path.exists(COMMON_CONFIG_PATH):
            with open(COMMON_CONFIG_PATH, 'r') as file:
                common_config = yaml.safe_load(file)
                logger.info(f"공통 설정 파일 로드 성공: {COMMON_CONFIG_PATH}")
                return common_config or {}
    except Exception as e:
        logger.error(f"공통 설정 로드 중 오류 발생: {str(e)}")
    
    return {}

def load_yaml_config(config_path: str = None) -> Dict[str, Any]:
    """
    YAML 설정 파일 로드 및 병합
    
    공통 설정을 로드한 후 환경별 설정을 병합합니다.
    환경별 설정은 항상 공통 설정보다 우선합니다.
    
    Args:
        config_path: YAML 설정 파일 경로
        
    Returns:
        병합된 설정 데이터 딕셔너리
    """
    # 1. 공통 설정 로드
    result_config = load_common_config()
    
    # 2. 환경별 설정 로드 및 병합
    # 설정 파일 경로가 지정되지 않은 경우 자동 결정
    if not config_path:
        config_path = get_config_path()
    
    try:
        # 파일이 존재하는지 확인
        if os.path.exists(config_path):
            # YAML 파일 로드
            with open(config_path, 'r') as file:
                env_config = yaml.safe_load(file) or {}
                logger.info(f"환경 설정 파일 로드 성공: {config_path}")
                
                # 3. 설정 병합 (환경별 설정이 공통 설정을 덮어씀)
                result_config = deep_merge(result_config, env_config)
                logger.info("공통 설정과 환경별 설정 병합 완료 (환경별 설정 우선)")
        else:
            logger.warning(f"환경 설정 파일이 존재하지 않습니다: {config_path}")
    except Exception as e:
        logger.error(f"설정 로드 및 병합 중 오류 발생: {str(e)}")
    
    return result_config

def get_yaml_settings(config_path: Optional[str] = None) -> YamlSettings:
    """
    YAML 설정 파일을 로드하고 YamlSettings 객체 생성
    
    Args:
        config_path: YAML 설정 파일 경로 (없으면 자동 결정)
        
    Returns:
        설정 객체
    """
    # 설정 로드 및 객체 생성
    config_data = load_yaml_config(config_path)
    settings = YamlSettings.model_validate(config_data)
    
    # 설정 정보 로깅
    logger.info(f"애플리케이션 환경: {settings.app.env}")
    logger.info(f"디버그 모드: {settings.app.debug}")
    logger.info(f"로깅 레벨: {settings.logging.level}")
    
    return settings

# 글로벌 설정 객체 생성
yaml_settings = get_yaml_settings()

# Log level 매핑
LOG_LEVEL_MAP = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

def get_log_level_from_yaml() -> int:
    """YAML 설정에서 로그 레벨 정수 값을 가져옵니다"""
    return LOG_LEVEL_MAP.get(yaml_settings.logging.level.upper(), 20)  # 기본값 INFO(20)

# 환경 별 로그 레벨 자동 설정
def get_environment_from_yaml() -> str:
    """YAML 설정에서 환경 정보를 가져옵니다."""
    return yaml_settings.app.env.lower()

# 개발 환경 여부 확인
def is_development() -> bool:
    """개발 환경인지 확인합니다."""
    return get_environment_from_yaml() in ["dev", "development", "local"]
    
# 프로덕션 환경 여부 확인
def is_production() -> bool:
    """프로덕션 환경인지 확인합니다."""
    return get_environment_from_yaml() in ["prod", "production"] 