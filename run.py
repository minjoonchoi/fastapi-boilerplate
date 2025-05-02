#!/usr/bin/env python3
"""
FastAPI 서버 실행을 위한 Python 스크립트
이 스크립트는 다양한 환경에서 FastAPI 애플리케이션을 실행하는 함수를 제공합니다.
"""

import os
import sys
import platform
import logging
import uvicorn
import subprocess

# 애플리케이션 실행 전 초기 로깅 설정을 위한 임포트
from app.core.logging_config import setup_logging
from app.core.yaml_config import yaml_settings, get_yaml_settings

def get_worker_count():
    """시스템의 CPU 코어 수에 기반한 워커 수를 반환합니다."""
    try:
        if platform.system() == "Windows":
            import multiprocessing
            return min(multiprocessing.cpu_count() * 2, 8)
        elif platform.system() == "Darwin":  # macOS
            cpu_count = int(subprocess.check_output(["sysctl", "-n", "hw.ncpu"]).decode().strip())
            return min(cpu_count * 2, 8)
        else:  # Linux, etc.
            cpu_count = int(subprocess.check_output(["nproc"]).decode().strip())
            return min(cpu_count * 2, 8)
    except Exception:
        return 4  # 기본값

def dev():
    """개발 환경에서 서버 실행"""
    # 먼저 환경 변수 설정
    os.environ["APP_ENV"] = "dev"
    
    # yaml_settings 객체를 환경 변수 설정 후 다시 가져오기
    global yaml_settings
    yaml_settings = get_yaml_settings()
    
    # 로깅 설정
    log_config = setup_logging()
    
    # 포트 번호 가져오기 (환경 변수 또는 기본값)
    port = int(os.environ.get("PORT", "8080"))
    
    logging.info("개발 서버를 시작합니다...")
    logging.info(f"환경: {os.environ.get('APP_ENV')}")
    logging.info(f"서버 주소: http://localhost:{port}")
    logging.info(f"Swagger UI: http://localhost:{port}/docs")
    
    # Uvicorn 서버 직접 실행
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_config=log_config,
        access_log=False  # 접근 로그는 미들웨어에서 처리
    )

def prod():
    """프로덕션 환경에서 서버 실행"""
    # 먼저 환경 변수 설정
    os.environ["APP_ENV"] = "prod"
    
    # yaml_settings 객체를 환경 변수 설정 후 다시 가져오기
    global yaml_settings
    yaml_settings = get_yaml_settings()
    
    # 로깅 설정
    log_config = setup_logging()
    
    workers = get_worker_count()
    
    # 포트 번호 가져오기 (환경 변수 또는 기본값)
    port = int(os.environ.get("PORT", "8080"))
    
    logging.info("프로덕션 서버를 시작합니다...")
    logging.info(f"환경: {os.environ.get('APP_ENV')}")
    logging.info(f"워커 수: {workers}")
    logging.info(f"서버 주소: http://localhost:{port}")
    
    # Uvicorn 서버 직접 실행
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        workers=workers,
        log_config=log_config,
        access_log=False  # 접근 로그는 미들웨어에서 처리
    )

def test():
    """테스트 환경에서 서버 실행"""
    # 먼저 환경 변수 설정
    os.environ["APP_ENV"] = "test"
    
    # yaml_settings 객체를 환경 변수 설정 후 다시 가져오기
    global yaml_settings
    yaml_settings = get_yaml_settings()
    
    # 로깅 설정
    log_config = setup_logging()
    
    # 포트 번호 가져오기 (환경 변수 또는 기본값)
    port = int(os.environ.get("PORT", "8080"))
    
    logging.info("테스트 서버를 시작합니다...")
    logging.info(f"환경: {os.environ.get('APP_ENV')}")
    logging.info(f"서버 주소: http://localhost:{port}")
    logging.info(f"Swagger UI: http://localhost:{port}/docs")
    
    # Uvicorn 서버 직접 실행
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_config=log_config,
        access_log=False  # 접근 로그는 미들웨어에서 처리
    )

if __name__ == "__main__":
    # 직접 스크립트 실행 시 인자에 따라 다른 모드로 실행
    if len(sys.argv) < 2:
        print("사용법: python run.py [dev|prod|test]")
        sys.exit(1)
        
    mode = sys.argv[1].lower()
    if mode == "dev":
        dev()
    elif mode == "prod":
        prod()
    elif mode == "test":
        test()
    else:
        print(f"알 수 없는 모드: {mode}")
        print("사용법: python run.py [dev|prod|test]")
        sys.exit(1) 