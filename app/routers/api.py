from fastapi import APIRouter, HTTPException, Security, Depends
from typing import Optional, List
from app.routers import upload, auth
from app.core.yaml_config import yaml_settings
from app.core.security import global_auth_header  # 보안 모듈에서 가져오기

# 라우터 설정 - 라우터 수준에서 인증 의존성 적용
router = APIRouter(
    prefix="/api",
    tags=["api"],
    responses={401: {"description": "인증 실패"}},
    dependencies=[Depends(global_auth_header)]  # 모든 엔드포인트에 기본 적용
)

# 업로드 라우터 포함
router.include_router(upload.router)

# 인증 라우터 포함
router.include_router(auth.router)

@router.get("/items", summary="모든 항목 조회")
async def get_items():
    """
    모든 항목의 목록을 가져옵니다.
    
    이 엔드포인트는 API 키 인증이 필요합니다.
    """
    return [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
        {"id": 3, "name": "Item 3"},
    ]

@router.get("/items/{item_id}", summary="특정 항목 조회")
async def get_item(item_id: int):
    """
    특정 ID의 항목 정보를 가져옵니다.
    
    이 엔드포인트는 API 키 인증이 필요합니다.
    """
    items = {
        1: {"id": 1, "name": "Item 1"},
        2: {"id": 2, "name": "Item 2"},
        3: {"id": 3, "name": "Item 3"},
    }
    
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return items[item_id]

# 인증이 필요 없는 엔드포인트는 별도 라우터로 등록
public_router = APIRouter(
    prefix="/api/public",
    tags=["api"],
    dependencies=[]  # 인증 의존성 제외
)

@public_router.get("/sample", summary="공개 샘플 데이터 조회")
async def get_public_sample():
    """
    인증 없이 접근 가능한 공개 샘플 데이터입니다.
    
    이 엔드포인트는 API 키 인증이 필요하지 않습니다.
    """
    return {
        "message": "이 데이터는 인증 없이 접근할 수 있습니다.",
        "timestamp": "2025-05-06T12:34:56Z"
    } 