"""
API 키 인증 미들웨어 테스트

이 모듈은 API 키 인증 미들웨어의 기능을 테스트합니다:
- 유효한 API 키로 인증 성공
- API 키 누락 시 401 응답
- 잘못된 API 키로 401 응답
- 제외 경로에 대한 인증 우회
- 인증 비활성화 시 모든 요청 허용
"""
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.api_key_auth import APIKeyAuthMiddleware

# 테스트를 위한 상수
TEST_API_KEY = "test-api-key"


class TestAPIKeyAuthMiddleware:
    """API 키 인증 미들웨어 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.app = FastAPI()
        
        @self.app.get("/api/protected")
        def protected_route():
            return {"message": "protected route"}
            
        @self.app.get("/health")
        def health_route():
            return {"status": "ok"}
    
    @patch("app.middleware.api_key_auth.APIKeyAuthMiddleware.is_path_excluded")
    @patch("app.middleware.api_key_auth.yaml_settings")
    def test_authentication(self, mock_settings, mock_is_excluded):
        """인증 기능 테스트"""
        # API 키 설정 모킹
        api_key_settings = MagicMock()
        api_key_settings.enabled = True
        api_key_settings.api_key = TEST_API_KEY
        api_key_settings.header_name = "Authorization"
        api_key_settings.prefix = "ApiKey "
        mock_settings.api.auth.api_key = api_key_settings
        
        # 경로 제외 검사 결과 모킹
        mock_is_excluded.return_value = False
        
        # 미들웨어 추가
        self.app.add_middleware(APIKeyAuthMiddleware)
        client = TestClient(self.app)
        
        # 1. 유효한 API 키로 성공
        response = client.get(
            "/api/protected", 
            headers={"Authorization": f"ApiKey {TEST_API_KEY}"}
        )
        assert response.status_code == 200
        
        # 2. API 키 없이 실패
        response = client.get("/api/protected")
        assert response.status_code == 401
        
        # 3. 잘못된 API 키로 실패
        response = client.get(
            "/api/protected", 
            headers={"Authorization": "ApiKey invalid-key"}
        )
        assert response.status_code == 401

    @patch("app.middleware.api_key_auth.yaml_settings")
    def test_excluded_path(self, mock_settings):
        """제외 경로 테스트"""
        # API 키 설정 모킹
        api_key_settings = MagicMock()
        api_key_settings.enabled = True
        api_key_settings.api_key = TEST_API_KEY
        api_key_settings.header_name = "Authorization"
        api_key_settings.prefix = "ApiKey "
        api_key_settings.exclude_patterns = ["/health/**"]
        mock_settings.api.auth.api_key = api_key_settings
        
        # 미들웨어 추가 
        self.app.add_middleware(APIKeyAuthMiddleware)
        client = TestClient(self.app)
        
        # 제외 경로는 API 키 없이 접근 가능
        response = client.get("/health")
        assert response.status_code == 200
    
    @patch("app.middleware.api_key_auth.yaml_settings")
    def test_auth_disabled(self, mock_settings):
        """인증 비활성화 테스트"""
        # API 키 설정 모킹 (비활성화)
        api_key_settings = MagicMock()
        api_key_settings.enabled = False
        mock_settings.api.auth.api_key = api_key_settings
        
        # 미들웨어 추가
        self.app.add_middleware(APIKeyAuthMiddleware)
        client = TestClient(self.app)
        
        # API 키 없이 접근 가능
        response = client.get("/api/protected")
        assert response.status_code == 200 