"""
인증 미들웨어 모듈

HTTP 요청의 인증 헤더를 확인하고 API 키 또는 JWT 토큰 방식으로 인증합니다.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import fnmatch

from app.core.yaml_config import yaml_settings
from app.core.logging_config import get_logger
from app.core.auth import get_token_data

logger = get_logger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """
    인증을 처리하는 미들웨어
    
    HTTP 요청의 Authorization 헤더를 확인하고 다음 인증 방식을 지원합니다:
    1. API 키 인증: "ApiKey your-api-key" 형식
    2. JWT 토큰 인증: "Bearer your-jwt-token" 형식
    """
    def __init__(
        self, 
        app: ASGIApp, 
        exclude_paths: list = None
    ):
        """
        미들웨어 초기화
        
        Args:
            app: ASGI 애플리케이션
            exclude_paths: 추가로 인증을 건너뛸 경로 목록 (설정에 있는 패턴 외에 추가)
        """
        super().__init__(app)
        self.additional_exclude_paths = exclude_paths or []
        
        # YAML 설정에서 인증 설정 가져오기
        self.api_key_settings = yaml_settings.api.auth.api_key
        self.jwt_settings = yaml_settings.api.auth.jwt
        
        # API 키 인증이 활성화되어 있는지 확인
        self.api_key_enabled = self.api_key_settings.enabled
        
        # JWT 인증이 활성화되어 있는지 확인
        self.jwt_enabled = self.jwt_settings.enabled
        
        if self.api_key_enabled:
            logger.info("API 키 인증 활성화됨")
            logger.info(f"API 키 제외 패턴: {self.api_key_settings.exclude_patterns}")
            
            # API 키가 설정되어 있는지 확인
            if not self.api_key_settings.api_key:
                logger.warning("API 키가 설정되어 있지 않습니다. API 키 인증이 비활성화됩니다.")
                self.api_key_enabled = False
        else:
            logger.info("API 키 인증 비활성화됨")
        
        if self.jwt_enabled:
            logger.info("JWT 인증 활성화됨")
            logger.info(f"JWT 제외 패턴: {self.jwt_settings.exclude_patterns}")
        else:
            logger.info("JWT 인증 비활성화됨")
            
        # 모든 인증 방식이 비활성화된 경우 경고
        if not self.api_key_enabled and not self.jwt_enabled:
            logger.warning("모든 인증 방식이 비활성화되었습니다. 요청이 인증되지 않습니다!")

    def path_match(self, path: str, pattern: str) -> bool:
        """
        경로와 패턴이 일치하는지 확인
        
        지원하는 패턴:
        - '/*': 정확히 하나의 경로 세그먼트와 매칭 (예: /api/* 는 /api/users와 매칭되지만 /api/users/me나 /api/users/와는 매칭되지 않음)
        - '/**': 0개 이상의 모든 하위 경로와 재귀적으로 매칭 (예: /api/** 는 /api, /api/users, /api/users/me 모두와 매칭)
        
        Args:
            path: 요청 경로
            pattern: 패턴
            
        Returns:
            매칭 여부
        """
        # 패턴에 '/**'가 포함된 경우 (재귀적 매칭)
        if '/**' in pattern:
            # 기본 경로 추출 (/** 이전 부분)
            base_path = pattern.split('/**')[0]
            
            # 기본 경로가 일치하는지 확인
            return path == base_path or path.startswith(base_path + '/')
        
        # 패턴에 '/*'가 포함된 경우 (단일 세그먼트 매칭)
        elif '/*' in pattern:
            # 테스트 케이스에 따라 후행 슬래시('/')가 있는 경로는 /* 패턴과 매칭되지 않아야 함
            # 예: /api/users/는 /api/*와 매칭되지 않음 (후행 슬래시가 있으므로)
            # 주의: 실제 애플리케이션에서는 TrailingSlashMiddleware에 의해 이미 처리되지만,
            # 단위 테스트와 백업 안전장치로 여기에도 로직 유지
            if path != '/' and path.endswith('/'):
                return False
                
            # 패턴과 경로를 세그먼트로 분할
            pattern_segments = pattern.split('/')
            path_segments = path.split('/')
            
            # 빈 문자열 세그먼트 제거 (경로 끝에 '/'가 있는 경우)
            if path_segments and path_segments[-1] == '':
                path_segments.pop()
                
            if pattern_segments and pattern_segments[-1] == '':
                pattern_segments.pop()
            
            # 세그먼트 수가 다르면 매칭되지 않음
            if len(pattern_segments) != len(path_segments):
                return False
            
            # 각 세그먼트 비교
            for i, pattern_seg in enumerate(pattern_segments):
                # 와일드카드(*) 세그먼트는 항상 매칭됨
                if pattern_seg == '*':
                    continue
                # 세그먼트가 다르면 매칭되지 않음
                if pattern_seg != path_segments[i]:
                    return False
            
            # 모든 세그먼트가 매칭됨
            return True
        
        # 정확한 경로 매칭
        else:
            return path == pattern

    def is_path_excluded_apikey(self, path: str) -> bool:
        """
        경로가 API 키 인증에서 제외되어야 하는지 확인
        
        Args:
            path: 요청 경로
            
        Returns:
            제외 여부
        """
        # 추가 제외 경로 확인 (정확한 경로 매칭)
        for exclude_path in self.additional_exclude_paths:
            if path.startswith(exclude_path):
                logger.debug(f"API 키 인증 - 추가 제외 경로 매칭: {path} -> {exclude_path}")
                return True
        
        # 설정에 있는 패턴 확인 (커스텀 패턴 매칭)
        for pattern in self.api_key_settings.exclude_patterns:
            if self.path_match(path, pattern):
                logger.debug(f"API 키 인증 - 제외 패턴 매칭: {path} -> {pattern}")
                return True
                
        return False
        
    def is_path_excluded_jwt(self, path: str) -> bool:
        """
        경로가 JWT 인증에서 제외되어야 하는지 확인
        
        Args:
            path: 요청 경로
            
        Returns:
            제외 여부
        """
        # 추가 제외 경로 확인 (정확한 경로 매칭)
        for exclude_path in self.additional_exclude_paths:
            if path.startswith(exclude_path):
                logger.debug(f"JWT 인증 - 추가 제외 경로 매칭: {path} -> {exclude_path}")
                return True
        
        # 설정에 있는 패턴 확인 (커스텀 패턴 매칭)
        for pattern in self.jwt_settings.exclude_patterns:
            if self.path_match(path, pattern):
                logger.debug(f"JWT 인증 - 제외 패턴 매칭: {path} -> {pattern}")
                return True
                
        return False

    async def dispatch(self, request: Request, call_next):
        """
        요청 처리 및 인증
        
        Args:
            request: HTTP 요청 객체
            call_next: 다음 미들웨어 호출 함수
            
        Returns:
            HTTP 응답 객체
        """
        # 모든 인증 방식이 비활성화된 경우
        if not self.api_key_enabled and not self.jwt_enabled:
            return await call_next(request)
        
        # 요청 경로 가져오기
        path = request.url.path
        
        # 인증 헤더 가져오기
        authorization = request.headers.get("Authorization")
        
        # 인증 헤더가 없는 경우
        if not authorization:
            # API 키 인증이 필요한 경로이면서 제외되지 않은 경우 오류 반환
            if self.api_key_enabled and not self.is_path_excluded_apikey(path):
                logger.warning(f"API 키 인증 실패: Authorization 헤더가 없습니다. 경로: {path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "API 키 또는 액세스 토큰이 필요합니다."}
                )
            
            # JWT 인증이 필요한 경로이면서 제외되지 않은 경우 오류 반환
            if self.jwt_enabled and not self.is_path_excluded_jwt(path):
                logger.warning(f"JWT 인증 실패: Authorization 헤더가 없습니다. 경로: {path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "API 키 또는 액세스 토큰이 필요합니다."},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # 인증이 필요하지 않은 경로인 경우 다음 미들웨어로 진행
            return await call_next(request)
        
        # API 키 인증 처리
        if self.api_key_enabled and not self.is_path_excluded_apikey(path):
            api_key_prefix = self.api_key_settings.prefix
            if authorization.startswith(api_key_prefix):
                # API 키 추출
                api_key = authorization[len(api_key_prefix):]
                
                # API 키 검증
                if api_key == self.api_key_settings.api_key:
                    logger.debug(f"API 키 인증 성공: {path}")
                    return await call_next(request)
                else:
                    logger.warning(f"API 키 인증 실패: 잘못된 API 키입니다. 경로: {path}")
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "잘못된 API 키입니다."}
                    )
        
        # JWT 인증 처리
        if self.jwt_enabled and not self.is_path_excluded_jwt(path):
            bearer_prefix = "Bearer "
            if authorization.startswith(bearer_prefix):
                # JWT 토큰 추출
                token = authorization[len(bearer_prefix):]
                
                try:
                    # JWT 토큰 검증
                    token_data = get_token_data(token)
                    logger.debug(f"JWT 인증 성공: {path}")
                    
                    # 요청 상태에 사용자 정보 저장 (다른 미들웨어나 라우터에서 사용)
                    request.state.user = token_data.get("sub")
                    request.state.token_data = token_data
                    
                    return await call_next(request)
                except HTTPException as e:
                    logger.warning(f"JWT 인증 실패: {str(e.detail)}. 경로: {path}")
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": str(e.detail)},
                        headers={"WWW-Authenticate": "Bearer"}
                    )
        
        # 인증 헤더 형식이 맞지 않는 경우
        if self.api_key_enabled and self.jwt_enabled:
            # 두 인증 방식 모두 지원하는 경우
            logger.warning(f"인증 실패: 잘못된 인증 헤더 형식입니다. 경로: {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "인증 헤더 형식이 잘못되었습니다. 'ApiKey' 또는 'Bearer' 접두사를 사용하세요."},
                headers={"WWW-Authenticate": "Bearer"}
            )
        elif self.api_key_enabled:
            # API 키만 지원하는 경우
            api_key_prefix = self.api_key_settings.prefix.strip()
            logger.warning(f"API 키 인증 실패: 인증 헤더 형식이 잘못되었습니다. 경로: {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"인증 헤더 형식이 잘못되었습니다. '{api_key_prefix}' 접두사를 사용하세요."}
            )
        elif self.jwt_enabled:
            # JWT만 지원하는 경우
            logger.warning(f"JWT 인증 실패: 인증 헤더 형식이 잘못되었습니다. 경로: {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "인증 헤더 형식이 잘못되었습니다. 'Bearer' 접두사를 사용하세요."},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 인증이 필요 없는 경로인 경우
        return await call_next(request)

# 이전 클래스 이름 호환성을 위한 별칭
APIKeyAuthMiddleware = AuthMiddleware 