#!/usr/bin/env python
"""
패턴 매칭 테스트 도구

명령줄에서 직접 패턴 매칭을 테스트할 수 있는 스크립트입니다.

사용법:
    python tests/test_pattern_matcher.py /some/path /pattern/**
    python tests/test_pattern_matcher.py /test/abc/1 "/test/*/1"
    python tests/test_pattern_matcher.py --test-all
"""
import sys
import argparse
from app.middleware.api_key_auth import APIKeyAuthMiddleware
from fastapi import FastAPI

# 테스트용 앱 초기화
app = FastAPI()
path_matcher = APIKeyAuthMiddleware(app)

def match_path(path, pattern):
    """패턴이 경로와 일치하는지 확인합니다."""
    result = path_matcher.path_match(path, pattern)
    return result

def test_predefined_cases():
    """미리 정의된 테스트 케이스를 실행합니다."""
    test_cases = [
        # /** 테스트
        ("/health", "/health/**", True),
        ("/health/liveness", "/health/**", True), 
        ("/healthcheck", "/health/**", False),
        
        # /* 테스트
        ("/api/users", "/api/*", True),
        ("/api/users/me", "/api/*", False),
        ("/api", "/api/*", False),
        
        # 복합 테스트
        ("/test/abc/1", "/test/*/1", True),
        ("/test/123/1", "/test/*/1", True),
        ("/test/abc/def/1", "/test/*/1", False),
        
        # 정확한 매칭
        ("/metrics", "/metrics", True),
        ("/metrics/custom", "/metrics", False)
    ]
    
    passed = 0
    failed = 0
    
    print("실행 중인 테스트 케이스:")
    print("=" * 60)
    
    for i, (path, pattern, expected) in enumerate(test_cases, 1):
        result = match_path(path, pattern)
        status = "✅ 통과" if result == expected else "❌ 실패"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{i}. {status} | 경로: '{path}' | 패턴: '{pattern}' | 기대값: {expected} | 결과: {result}")
    
    print("=" * 60)
    print(f"총 테스트: {len(test_cases)}, 통과: {passed}, 실패: {failed}")
    
    return failed == 0

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="경로 패턴 매칭 테스트 도구")
    parser.add_argument("--test-all", action="store_true", help="미리 정의된 모든 테스트 케이스 실행")
    parser.add_argument("path", nargs="?", help="테스트할 경로")
    parser.add_argument("pattern", nargs="?", help="테스트할 패턴")
    
    args = parser.parse_args()
    
    if args.test_all:
        success = test_predefined_cases()
        sys.exit(0 if success else 1)
        
    if not args.path or not args.pattern:
        parser.print_help()
        sys.exit(1)
    
    result = match_path(args.path, args.pattern)
    print(f"경로: '{args.path}'")
    print(f"패턴: '{args.pattern}'")
    print(f"결과: {'일치함' if result else '일치하지 않음'}")

if __name__ == "__main__":
    main() 