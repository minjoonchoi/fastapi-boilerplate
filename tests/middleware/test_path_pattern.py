"""
경로 패턴 매칭 유틸리티 테스트
"""
from fastapi import FastAPI

from app.middleware.api_key_auth import APIKeyAuthMiddleware
from app.middleware.request_logging import RequestResponseLoggingMiddleware


class TestPathPatternMatching:
    """경로 패턴 매칭 메서드 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.app = FastAPI()
        self.middleware = APIKeyAuthMiddleware(self.app)
    
    def test_path_match(self):
        """path_match 메서드 테스트"""
        # /** 패턴 테스트 (재귀적 매칭)
        assert self.middleware.path_match("/health", "/health/**") is True
        assert self.middleware.path_match("/health/liveness", "/health/**") is True
        assert self.middleware.path_match("/healthcheck", "/health/**") is False
        
        # /* 패턴 테스트 (단일 세그먼트 매칭)
        assert self.middleware.path_match("/api/users", "/api/*") is True
        assert self.middleware.path_match("/api/users/me", "/api/*") is False
        assert self.middleware.path_match("/api", "/api/*") is False
        
        # 정확한 경로 테스트
        assert self.middleware.path_match("/metrics", "/metrics") is True
        assert self.middleware.path_match("/metrics/custom", "/metrics") is False
        
        # 후행 슬래시 처리 확인
        assert self.middleware.path_match("/api/users/", "/api/*") is False
    
    def test_is_path_excluded(self):
        """is_path_excluded 메서드 테스트"""
        # 제외 패턴 설정
        self.middleware.api_key_settings.exclude_patterns = ["/health/**", "/metrics"]
        
        # 제외된 경로 확인
        assert self.middleware.is_path_excluded("/health") is True
        assert self.middleware.is_path_excluded("/health/status") is True
        assert self.middleware.is_path_excluded("/metrics") is True
        
        # 제외되지 않은 경로 확인
        assert self.middleware.is_path_excluded("/api") is False 