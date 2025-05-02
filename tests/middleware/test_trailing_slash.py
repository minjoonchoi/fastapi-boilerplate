"""
TrailingSlashMiddleware 단위 테스트
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.trailing_slash import TrailingSlashMiddleware


class TestTrailingSlashMiddleware:
    """후행 슬래시 미들웨어 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.app = FastAPI()
        
        @self.app.get("/test")
        def test_route():
            return {"message": "test route"}
            
        @self.app.get("/")
        def root_route():
            return {"message": "root route"}

    def test_internal_path_modification(self):
        """내부 경로 수정 모드 테스트"""
        self.app.add_middleware(
            TrailingSlashMiddleware,
            redirect=False
        )
        
        client = TestClient(self.app)
        
        # 후행 슬래시가 있는 경로 요청
        response = client.get("/test/")
        assert response.status_code == 200
        assert response.json() == {"message": "test route"}
        
        # 루트 경로는 그대로 유지
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "root route"}

    def test_redirect_mode(self):
        """리다이렉트 모드 테스트"""
        self.app.add_middleware(
            TrailingSlashMiddleware,
            redirect=True
        )
        
        client = TestClient(self.app)
        
        # 리다이렉트 확인
        response = client.get("/test/", follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "http://testserver/test"
        
        # 리다이렉트 따라가기
        response = client.get("/test/", follow_redirects=True)
        assert response.status_code == 200
        assert response.json() == {"message": "test route"} 