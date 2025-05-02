from fastapi import FastAPI, Depends, Security
import uvicorn
import os
import logging
import logging.config
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.status import warmup
from app.core.logging_config import get_logger, setup_logging
# YAML 설정 가져오기
from app.core.yaml_config import yaml_settings, get_log_level_from_yaml
from app.middleware.request_logging import RequestResponseLoggingMiddleware
from app.middleware.api_key_auth import AuthMiddleware
from app.middleware.trailing_slash import TrailingSlashMiddleware

# 로깅 설정 적용 (결과를 저장하여 재사용)
uvicorn_log_config = setup_logging()

# 로거 가져오기
logger = get_logger(__name__)

def ensure_directories():
    """필요한 디렉토리들이 존재하는지 확인하고, 없으면 생성합니다."""
    directories = ["logs", "uploads"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"{directory} 디렉토리를 생성했습니다.")

# API 태그 메타데이터 정의
tags_metadata = [
    {
        "name": "health",
        "description": "Health check endpoints for application monitoring",
    },
    {
        "name": "api",
        "description": "Main API endpoints",
    },
    {
        "name": "auth",
        "description": "Authentication endpoints for access token management",
    },
    {
        "name": "upload",
        "description": "File upload and management endpoints",
    },
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행되는 코드
    logger.info("애플리케이션 시작 중... (YAML 설정 사용)")
    logger.info(f"환경: {yaml_settings.app.env}, 로깅 레벨: {yaml_settings.logging.level}")
    
    
    # 시스템 웜업 수행
    is_ready = await warmup()
    
    if is_ready:
        logger.info("애플리케이션이 성공적으로 시작되었습니다.")
    else:
        logger.warning("일부 서비스가 준비되지 않았지만, 애플리케이션을 시작합니다.")
    
    yield  # 여기서 FastAPI가 요청을 처리
    
    # 종료 시 실행되는 코드
    logger.info("애플리케이션이 종료됩니다.")

# FastAPI 애플리케이션 설정
app = FastAPI(
    title=yaml_settings.app.name,
    description="""
    FastAPI Boilerplate 애플리케이션 API 문서
    
    ## 인증 방식
    
    이 API는 통합 인증 헤더 방식을 사용합니다:
    
    **Authorization 헤더 인증**: 모든 보호된 엔드포인트에는 `Authorization` 헤더가 필요합니다. 
    다음 두 가지 형식을 지원합니다:
    
    1. **JWT 토큰**: `Bearer your-token` 형식으로 전달
    2. **API 키**: `ApiKey your-api-key` 형식으로 전달
    
    JWT 토큰을 발급받으려면 `/api/auth/token` 엔드포인트를 사용하세요.
    
    ## Swagger UI에서 인증하기
    
    Swagger UI에서 API를 테스트하기 위해 다음 단계를 따르세요:
    
    1. 화면 상단의 "Authorize" 버튼 클릭
    2. "CustomHeaderAuth" 섹션에서 완전한 헤더 값 입력:
        - JWT 토큰 사용: `Bearer eyJ0eXAi...`
        - API 키 사용: `ApiKey your-api-key`
    3. "Authorize" 버튼 클릭하여 인증 정보 적용
    
    인증 정보는 페이지를 새로고침해도 유지됩니다.
    """,
    version="0.1.0",
    debug=yaml_settings.app.debug,
    openapi_tags=tags_metadata,
    docs_url=None,  # 기본 /docs URL 비활성화 (커스텀 구성 위해)
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,  # 새로운 lifespan 컨텍스트 매니저 사용
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,  # 모델 섹션 기본적으로 숨김
        "deepLinking": True,  # URL에 현재 보고 있는 태그/작업 포함
        "displayRequestDuration": True,  # 요청 지속 시간 표시
        "filter": True,  # 엔드포인트 필터링 사용
        "syntaxHighlight.theme": "monokai"  # 구문 강조 테마
    }
)


# 후행 슬래시 제거 미들웨어 추가 (가장 먼저 적용)
app.add_middleware(
    TrailingSlashMiddleware,
    redirect=False  # 내부적으로 경로 수정 (리다이렉트 없음)
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 프로덕션 환경에서는 특정 출처 지정
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청/응답 로깅 미들웨어 추가
app.add_middleware(
    RequestResponseLoggingMiddleware,
    # 제외 패턴은 YAML 설정 파일에서 관리됩니다 (logging.http.exclude_patterns)
    log_request_body=yaml_settings.logging.http.request_body,
    log_response_body=yaml_settings.logging.http.response_body,
    max_body_length=yaml_settings.logging.http.max_body_length,
    sensitive_fields=yaml_settings.logging.sensitive_fields_set
)

# 인증 미들웨어 추가
app.add_middleware(
    AuthMiddleware,
    # 제외 패턴은 YAML 설정 파일에서 관리됩니다
)

# 커스텀 Swagger UI 엔드포인트
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - API 문서",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        init_oauth={
            "usePkceWithAuthorizationCodeGrant": True,
            "useBasicAuthenticationWithAccessCodeGrant": True
        },
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,  # 모델 섹션 기본적으로 숨김
            "deepLinking": True,  # URL에 현재 보고 있는 태그/작업 포함
            "displayRequestDuration": True,  # 요청 지속 시간 표시
            "filter": True,  # 엔드포인트 필터링 사용
            "syntaxHighlight.theme": "monokai",  # 구문 강조 테마
            "persistAuthorization": True,  # 인증 정보 유지 (Python의 True 사용)
            "tryItOutEnabled": True,  # Try it out 버튼 기본 활성화
            "displayOperationId": False,
            # 추가 설정
            "supportedSubmitMethods": ["get", "put", "post", "delete", "options", "head", "patch", "trace"],
            "docExpansion": "list",
            "withCredentials": True,  # 인증 정보 포함
            "showExtensions": True,    # 확장 정보 표시
            "displayAuthorizationButton": True  # 인증 버튼 표시 강제
        }
    )

# 라우터 등록
from app.routers.api import router as api_router, public_router as api_public_router
from app.routers.auth import router as auth_router, protected_router as auth_protected_router
from app.routers.health import router as health_router

# API 라우터 등록 - 보안 설정별로 구분
app.include_router(api_router)  # 인증 필요한 API 라우터
app.include_router(api_public_router)  # 인증 필요 없는 API 라우터

# 인증 라우터 등록 - 보안 설정별로 구분
app.include_router(auth_router)  # 인증 필요 없는 인증 라우터
app.include_router(auth_protected_router)  # 인증 필요한 인증 라우터

# 헬스 체크 라우터 등록 (인증 없음)
app.include_router(health_router, dependencies=[])

# 필요한 디렉토리 생성
ensure_directories()

# 정적 파일 제공 설정 (업로드된 파일용)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/", tags=["root"])
async def root():
    return {"message": f"Welcome to {yaml_settings.app.name}", "docs": "/docs"}

if __name__ == "__main__":
    # 로그 설정이 제대로 적용되었는지 확인
    logger.info("애플리케이션 시작을 위해 uvicorn 서버를 구동합니다.")
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", "8080")), 
        reload=yaml_settings.app.debug,
        log_config=uvicorn_log_config
    ) 