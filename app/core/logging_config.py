"""
애플리케이션의 로깅 설정을 관리하는 모듈입니다.
다양한 환경과 요구사항에 맞게 로거를 구성합니다.
"""
import logging
import logging.config
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# 기본 로그 포맷 설정
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"

# 환경별 로그 레벨 매핑
ENV_LOG_LEVELS = {
    "dev": logging.DEBUG,
    "test": logging.DEBUG,
    "stage": logging.INFO,
    "prod": logging.WARNING,
}

def load_logging_config(env: str = None) -> Dict[str, Any]:
    """
    YAML 파일에서 로깅 설정을 로드합니다.
    
    Args:
        env: 환경 설정 (dev, test, stage, prod)
        
    Returns:
        Dict[str, Any]: 로깅 설정 딕셔너리
    """
    # 프로젝트 루트 디렉토리 찾기
    root_dir = Path(__file__).parents[2]  # app/core 디렉토리에서 두 단계 위
    
    # 환경 가져오기
    if env is None:
        env = get_environment()
    
    # 환경별 설정 파일 경로 설정
    env_config_file = root_dir / "config" / f"logging_config_{env}.yaml"
    default_config_file = root_dir / "config" / "logging_config.yaml"
    
    # 먼저 환경별 설정 파일 시도, 없으면 기본 설정 파일 사용
    config_file = env_config_file if env_config_file.exists() else default_config_file
    
    # YAML 파일 로드
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            
        # 로그 디렉토리 확인 (파일 핸들러가 있는 경우)
        for handler_config in config.get('handlers', {}).values():
            if 'filename' in handler_config:
                log_path = handler_config['filename']
                log_dir = os.path.dirname(log_path)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
            
        # 환경별 로그 레벨 조정 (env_log_levels가 있는 경우)
        if 'env_log_levels' in config and env in config['env_log_levels']:
            # 루트 로거 레벨 설정
            root_level = config['env_log_levels'][env]
            if '' in config['loggers']:
                config['loggers']['']['level'] = root_level
            
            # app 로거 레벨 설정 (있을 경우)
            if 'app' in config['loggers']:
                config['loggers']['app']['level'] = root_level
                
        # 'env_log_levels' 키 제거 (logging.dictConfig에서 사용하지 않음)
        if 'env_log_levels' in config:
            del config['env_log_levels']
            
        logging.info(f"로깅 설정을 {config_file} 파일에서 로드했습니다.")
        return config
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"로깅 설정 파일을 로드하는 데 실패했습니다: {e}")
        
        # 기본 로깅 설정 반환
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": DETAILED_FORMAT
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                }
            },
            "loggers": {
                "": {
                    "level": get_log_level(env),
                    "handlers": ["console"],
                    "propagate": False
                }
            }
        }

def setup_logging() -> Dict[str, Any]:
    """
    애플리케이션 로깅을 설정하고 Uvicorn 로그 설정을 반환합니다.
    
    YAML 파일에서 로깅 설정을 로드하여 애플리케이션에 적용하고,
    동일한 설정을 Uvicorn에 전달할 수 있는 형태로 반환합니다.
    
    Returns:
        Dict[str, Any]: Uvicorn 호환 로그 설정 딕셔너리
    """
    # 순환 참조 방지를 위해 함수 내에서 임포트
    from app.core.yaml_config import get_environment_from_yaml
    
    # 현재 환경 가져오기
    env = get_environment_from_yaml()
    
    # YAML 파일에서 로깅 설정 로드
    log_config = load_logging_config(env)
    
    # 로깅 설정 적용
    logging.config.dictConfig(log_config)
    
    # yaml_config 모듈 로거 설정 확인 (특별 처리가 필요할 경우)
    yaml_config_logger = logging.getLogger("yaml_config")
    if not yaml_config_logger.handlers:
        # YAML 설정이 적용되지 않은 경우에만 수동 설정
        yaml_config_logger.propagate = True
    
    # 로깅 초기화 메시지
    logging.info("로깅 설정이 YAML 파일에서 로드되었습니다.")
    
    # Uvicorn에 전달할 수 있는 설정 반환 (동일한 설정 사용)
    return log_config

# 하위 호환성을 위한 함수 (기존 코드에서 사용 중인 경우)
def setup_initial_logging():
    """애플리케이션 시작 전 초기 로깅 설정을 구성합니다."""
    setup_logging()

def get_environment() -> str:
    """애플리케이션 실행 환경을 결정합니다."""
    return os.environ.get("APP_ENV", "dev").lower()

def get_log_level(env: str = None) -> int:
    """환경에 따른 로그 레벨을 반환합니다."""
    env = env or get_environment()
    return ENV_LOG_LEVELS.get(env, logging.INFO)

def get_logger(name: str) -> logging.Logger:
    """
    지정된 이름으로 로거를 가져옵니다.
    
    애플리케이션 내에서 로거를 획득할 때 이 함수를 사용해야 합니다.
    
    Args:
        name: 로거 이름 (일반적으로 __name__ 사용)
        
    Returns:
        구성된 로거 인스턴스
    """
    return logging.getLogger(name) 