"""
후행 슬래시 제거 미들웨어

URL 경로에서 후행 슬래시를 제거하여 일관된 경로 처리를 보장합니다.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send, Message
from fastapi.responses import RedirectResponse
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class TrailingSlashMiddleware(BaseHTTPMiddleware):
    """
    URL 경로에서 후행 슬래시를 제거하는 미들웨어
    
    예: /api/users/ -> /api/users
    
    루트 경로 "/"는 변경하지 않습니다.
    """
    
    def __init__(self, app: ASGIApp, redirect: bool = True):
        """
        미들웨어 초기화
        
        Args:
            app: ASGI 애플리케이션
            redirect: True면 후행 슬래시가 있는 URL을 슬래시 없는 URL로 리다이렉트합니다(301).
                     False면 내부적으로 경로를 수정하여 리다이렉트 없이 처리합니다.
        """
        super().__init__(app)
        self.redirect = redirect
        logger.info("후행 슬래시 제거 미들웨어 활성화")
        
    async def dispatch(self, request: Request, call_next):
        """
        요청을 처리하고 필요한 경우 후행 슬래시를 제거합니다.
        
        Args:
            request: HTTP 요청 객체
            call_next: 다음 미들웨어 호출 함수
            
        Returns:
            HTTP 응답 객체
        """
        path = request.url.path
        
        # 루트 경로('/')는 그대로 유지
        if path != "/" and path.endswith("/"):
            # 슬래시를 제거한 새 경로
            normalized_path = path.rstrip("/")
            
            if self.redirect:
                # 301 리다이렉트 (영구 이동)
                redirect_url = str(request.url.replace(path=normalized_path))
                logger.debug(f"후행 슬래시 리다이렉트: {path} -> {normalized_path}")
                return RedirectResponse(redirect_url, status_code=301)
            else:
                # 경로를 내부적으로 수정 (리다이렉트 없음)
                logger.debug(f"후행 슬래시 내부 제거: {path} -> {normalized_path}")
                request.scope["path"] = normalized_path
        
        # 다음 미들웨어로 요청 전달
        response = await call_next(request)
        return response 