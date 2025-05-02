"""
요청/응답 로깅 미들웨어 테스트

이 모듈은 요청 및 응답 로깅 미들웨어의 기능을 테스트합니다:
- 요청 및 응답 본문 로깅
- 민감 정보 마스킹
- 제외 경로에 대한 로깅 제외
- 대용량 요청/응답 본문 잘라내기
"""
from unittest.mock import patch, MagicMock

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.request_logging import RequestResponseLoggingMiddleware


class TestRequestResponseLoggingMiddleware:
    """요청/응답 로깅 미들웨어 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.app = FastAPI()
        
        @self.app.post("/api/users")
        async def create_user(request: Request):
            body = await request.json()
            return {"status": "created", "user": body.get("username")}
            
        @self.app.get("/api/test")
        def api_test():
            return {"status": "ok"}

    @patch("app.middleware.request_logging.logger")
    @patch("app.middleware.request_logging.yaml_settings")
    def test_request_logging(self, mock_settings, mock_logger):
        """기본 로깅 기능 테스트"""
        # 설정 모킹
        logging_config = MagicMock()
        logging_config.enabled = True
        logging_config.exclude_patterns = []
        logging_config.sensitive_fields_set = set()
        logging_config.max_body_length = 10000
        mock_settings.logging = logging_config
        
        # 로거 모킹
        mock_logger.info = MagicMock()
        
        # 미들웨어 추가
        self.app.add_middleware(RequestResponseLoggingMiddleware)
        client = TestClient(self.app)
        
        # 요청 전송
        response = client.post("/api/users", json={"username": "testuser"})
        assert response.status_code == 200
        
        # 로거 호출 확인
        assert mock_logger.info.call_count >= 1
        
        # API 요청 로깅 확인
        api_request_logged = False
        for call in mock_logger.info.call_args_list:
            if call[0] and "Request" in str(call[0][0]) and "/api/users" in str(call[0][0]):
                api_request_logged = True
                break
        
        assert api_request_logged, "API 요청이 로깅되지 않았습니다" 