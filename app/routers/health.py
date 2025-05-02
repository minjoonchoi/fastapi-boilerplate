"""
애플리케이션의 상태 확인을 위한 헬스 체크 관련 라우터 모듈입니다.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Tuple, Any
import logging
from app.core.status import check_system_health

logger = logging.getLogger(__name__)

# 헬스 체크 라우터 생성
router = APIRouter(
    tags=["health"],
)

# 상태 확인 공통 기능 정의
async def get_liveness_status() -> Dict[str, str]:
    """애플리케이션이 실행 중인지 확인하는 기본 liveness 상태를 반환합니다."""
    return {"status": "ok"}

async def get_readiness_status() -> Tuple[bool, Dict]:
    """
    애플리케이션이 요청을 처리할 준비가 되었는지 확인합니다.
    (모든 의존성 서비스가 정상인지 확인)
    
    Returns:
        튜플: (준비 완료 여부, 상태 보고서)
    """
    status_report = await check_system_health()
    is_ready = status_report["ready"]
    return is_ready, status_report

# 기본 헬스 체크
@router.get("/health", 
           summary="기본 상태 확인", 
           description="애플리케이션의 전반적인 상태를 확인합니다",
           openapi_extra={"security": []})
async def health_check(
    liveness_status: Dict = Depends(get_liveness_status),
    readiness_info: Tuple[bool, Dict] = Depends(get_readiness_status)
):
    """
    애플리케이션의 전반적인 상태를 확인합니다.
    liveness와 readiness 모두 정상일 때만 OK를 반환합니다.
    일반적인 상태 확인에 사용됩니다.
    
    이 엔드포인트는 API 키 인증이 필요하지 않습니다.
    """
    is_ready, _ = readiness_info
    
    if is_ready:
        return {"status": "ok"}
    else:
        # readiness가 실패한 경우, 서비스 사용 불가 상태 반환
        raise HTTPException(
            status_code=503, 
            detail={
                "status": "service unavailable",
                "message": "Service is not ready to handle requests",
            }
        )

@router.get("/health/liveness", 
           summary="Liveness 확인", 
           description="애플리케이션이 실행 중인지 확인합니다",
           openapi_extra={"security": []})
async def liveness_check(
    liveness_status: Dict = Depends(get_liveness_status)
):
    """
    애플리케이션이 실행 중인지만 확인합니다.
    컨테이너 오케스트레이션 도구의 liveness probe에 사용됩니다.
    
    이 엔드포인트는 API 키 인증이 필요하지 않습니다.
    """
    return liveness_status

@router.get("/health/readiness", 
           summary="Readiness 확인", 
           description="애플리케이션이 요청을 처리할 준비가 되었는지 확인합니다",
           openapi_extra={"security": []})
async def readiness_check(
    readiness_info: Tuple[bool, Dict] = Depends(get_readiness_status)
):
    """
    애플리케이션이 요청을 처리할 준비가 되었는지 확인합니다.
    모든 필요한 서비스(DB, 캐시 등)가 정상적으로 연결되어 있는지 확인합니다.
    컨테이너 오케스트레이션 도구의 readiness probe에 사용됩니다.
    
    이 엔드포인트는 API 키 인증이 필요하지 않습니다.
    """
    is_ready, status_report = readiness_info
    
    if is_ready:
        return {
            "status": "ok",
            "details": status_report
        }
    else:
        raise HTTPException(
            status_code=503, 
            detail={
                "status": "service unavailable",
                "message": "Service is not ready to handle requests",
                "details": status_report
            }
        )

# 자세한 상태 정보를 제공하는 확장된 엔드포인트
@router.get("/health/status", 
           summary="상세 상태 정보", 
           description="시스템 컴포넌트의 상세 상태 정보를 제공합니다",
           openapi_extra={"security": []})
async def detailed_health_status(
    readiness_info: Tuple[bool, Dict] = Depends(get_readiness_status)
):
    """
    시스템 컴포넌트의 상세 상태 정보를 제공합니다.
    
    이 엔드포인트는 API 키 인증이 필요하지 않습니다.
    """
    _, status_report = readiness_info
    return status_report 