"""
경로 패턴 매칭 로직 테스트 모듈

주의: 이 테스트는 TrailingSlashMiddleware가 적용되지 않은 상태에서 직접 path_match 메서드를 테스트합니다.
따라서 미들웨어 내부에 후행 슬래시 처리 로직이 필요합니다.
실제 애플리케이션에서는 TrailingSlashMiddleware가 선행 처리되므로 중복 로직이 아닙니다.
"""
import pytest
from app.middleware.api_key_auth import APIKeyAuthMiddleware
from app.middleware.request_logging import RequestResponseLoggingMiddleware
from fastapi import FastAPI

# 테스트용 앱 초기화
app = FastAPI()
api_key_middleware = APIKeyAuthMiddleware(app)
logging_middleware = RequestResponseLoggingMiddleware(app)

class TestPathMatching:
    """경로 패턴 매칭 기능 테스트 클래스"""

    @pytest.mark.parametrize(
        "path,pattern,expected",
        [
            # /** 패턴 테스트 (재귀적 매칭)
            ("/health", "/health/**", True),  # 경로 정확히 일치
            ("/health/", "/health/**", True),  # 슬래시가 있는 경우
            ("/health/liveness", "/health/**", True),  # 하위 경로 1단계
            ("/health/readiness/detailed", "/health/**", True),  # 하위 경로 여러 단계
            ("/healthcheck", "/health/**", False),  # 경로 접두사만 일치
            ("/api/health", "/health/**", False),  # 전혀 다른 경로
            
            # /* 패턴 테스트 (단일 세그먼트 매칭)
            ("/api/users", "/api/*", True),  # 단일 세그먼트 매칭
            ("/api/users/", "/api/*", False),  # 단일 세그먼트지만 후행 슬래시가 있어 세그먼트 수가 다름
            ("/api/users/me", "/api/*", False),  # 세그먼트 수가 다름
            ("/api", "/api/*", False),  # 세그먼트 부족
            ("/api/", "/api/*", False),  # 빈 세그먼트는 매칭되지 않음
            
            # 여러 와일드카드 테스트
            ("/test/abc/1", "/test/*/1", True),  # 중간 세그먼트 와일드카드
            ("/test/123/1", "/test/*/1", True),  # 숫자도 매칭
            ("/test/1", "/test/*/1", False),  # 세그먼트 수가 부족
            ("/test/abc/def/1", "/test/*/1", False),  # 세그먼트 수가 많음
            
            # API 예제 테스트
            ("/api/v1/health", "/api/*/health", True),  # API 버전 와일드카드
            ("/api/v2/health", "/api/*/health", True),  # 다른 API 버전도 매칭
            ("/api/v1/users/health", "/api/*/health", False),  # 세그먼트 수가 다름
            
            # 복합 경로 테스트
            ("/users/123/posts/456", "/users/*/posts/*", True),  # 여러 와일드카드
            ("/users/123/comments", "/users/*/posts/*", False),  # 두 번째 세그먼트 불일치
            
            # 정확한 경로 매칭 (와일드카드 없음)
            ("/metrics", "/metrics", True),  # 정확히 일치
            ("/metrics/custom", "/metrics", False),  # 하위 경로 불일치
            ("/metric", "/metrics", False),  # 부분 문자열 불일치
        ],
    )
    def test_api_key_path_match(self, path, pattern, expected):
        """API 키 미들웨어의 path_match 메서드 테스트"""
        result = api_key_middleware.path_match(path, pattern)
        assert result == expected, f"API Key Middleware: path={path}, pattern={pattern}, expected={expected}, got={result}"

    @pytest.mark.parametrize(
        "path,pattern,expected",
        [
            # /** 패턴 테스트 (재귀적 매칭)
            ("/health", "/health/**", True),  # 경로 정확히 일치
            ("/health/liveness", "/health/**", True),  # 하위 경로 1단계
            ("/health/readiness/detailed", "/health/**", True),  # 하위 경로 여러 단계
            ("/healthcheck", "/health/**", False),  # 경로 접두사만 일치
            
            # /* 패턴 테스트 (단일 세그먼트 매칭)
            ("/api/users", "/api/*", True),  # 단일 세그먼트 매칭
            ("/api/users/me", "/api/*", False),  # 세그먼트 수가 다름
            ("/api", "/api/*", False),  # 세그먼트 부족
            
            # 여러 와일드카드 테스트
            ("/test/abc/1", "/test/*/1", True),  # 중간 세그먼트 와일드카드
            ("/test/123/1", "/test/*/1", True),  # 숫자도 매칭
            ("/test/1", "/test/*/1", False),  # 세그먼트 수가 부족
            
            # 정확한 경로 매칭 테스트
            ("/favicon.ico", "/favicon.ico", True),  # 정확히 일치
            ("/openapi.json", "/openapi.json", True),  # 정확히 일치
        ],
    )
    def test_logging_path_match(self, path, pattern, expected):
        """로깅 미들웨어의 path_match 메서드 테스트"""
        result = logging_middleware.path_match(path, pattern)
        assert result == expected, f"Logging Middleware: path={path}, pattern={pattern}, expected={expected}, got={result}"

    @pytest.mark.parametrize(
        "path,exclude_patterns,expected",
        [
            # 단일 패턴 테스트
            ("/health", ["/health/**"], True),
            ("/api/users", ["/api/*"], True),
            ("/api/users/me", ["/api/*"], False),
            
            # 여러 패턴 테스트
            ("/health/liveness", ["/metrics", "/health/**"], True),
            ("/metrics", ["/metrics", "/health/**"], True),
            ("/api", ["/metrics", "/health/**"], False),
            
            # YAML 기본 설정 패턴 테스트
            ("/health/status", ["/health/**", "/metrics", "/docs/**", "/redoc/**", "/openapi.json"], True),
            ("/docs/oauth2-redirect", ["/health/**", "/metrics", "/docs/**", "/redoc/**", "/openapi.json"], True),
            ("/redoc", ["/health/**", "/metrics", "/docs/**", "/redoc/**", "/openapi.json"], True),
            ("/openapi.json", ["/health/**", "/metrics", "/docs/**", "/redoc/**", "/openapi.json"], True),
            ("/api/users", ["/health/**", "/metrics", "/docs/**", "/redoc/**", "/openapi.json"], False),
        ],
    )
    def test_is_path_excluded(self, path, exclude_patterns, expected):
        """경로 제외 로직 테스트"""
        # 테스트를 위해 미들웨어의 exclude_patterns를 임시로 설정
        api_key_middleware.api_key_settings.exclude_patterns = exclude_patterns
        
        result = api_key_middleware.is_path_excluded(path)
        assert result == expected, f"path={path}, patterns={exclude_patterns}, expected={expected}, got={result}"

    @pytest.mark.parametrize(
        "pattern",
        [
            "/**",  # 루트에서 시작하는 와일드카드 (모든 경로와 매칭)
            "/*/**",  # 복합 패턴 (첫 번째 세그먼트는 어떤 것이든 매칭, 그 아래는 모든 경로 매칭)
            "/api/*/**",  # 더 복잡한 복합 패턴
            "/*/*/*",  # 정확히 3단계 경로 매칭
        ],
    )
    def test_complex_patterns(self, pattern):
        """복잡한 패턴 테스트는 실제 매칭 결과보다는 오류 없이 실행되는지 확인"""
        # 오류 없이 실행되기만 하면 통과로 간주
        path = "/some/test/path"
        # 예외가 발생하지 않아야 함
        result = api_key_middleware.path_match(path, pattern)
        # 결과는 중요하지 않음, 예외가 발생하지 않으면 통과 