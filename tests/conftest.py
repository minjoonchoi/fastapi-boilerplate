"""
pytest 설정 파일
"""
import pytest
import os
import sys

# 프로젝트 루트를 sys.path에 추가하여 app 모듈을 임포트 할 수 있게 함
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def app_env():
    """테스트를 위한 환경 변수 설정"""
    # 원래 환경 변수 백업
    original_env = os.environ.copy()
    
    # 테스트 환경 설정
    os.environ["APP_ENV"] = "test"
    os.environ["API_KEY"] = "test-api-key"
    
    yield
    
    # 테스트 후 환경 변수 복원
    os.environ.clear()
    os.environ.update(original_env) 