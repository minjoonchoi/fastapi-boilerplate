from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.core.logging_config import get_logger
from app.core.auth import (
    authenticate_user, create_access_token, create_refresh_token, 
    decode_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.core.yaml_config import yaml_settings
from app.core.security import global_auth_header  # security 모듈에서 가져오기

# 로거 설정
logger = get_logger(__name__)

# 공개 접근 가능한 인증 라우터 (토큰 발급 등)
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"description": "인증 실패"}}
)

# 인증이 필요한 인증 라우터 (사용자 정보 조회 등)
protected_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"description": "인증 실패"}},
    dependencies=[Depends(global_auth_header)]
)

# 보안 스키마 정의 (라우터 생성 후 별도 설정)
# /token 엔드포인트를 제외한 모든 경로에 적용

# 토큰 응답 모델
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


# 사용자 응답 모델
class UserResponse(BaseModel):
    username: str
    email: Optional[str] = None


@router.post("/token", summary="액세스 토큰 발급", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    사용자 인증 및 액세스 토큰 발급
    
    아이디와 비밀번호를 통해 사용자를 인증하고, 유효한 JWT 액세스 토큰과 리프레시 토큰을 발급합니다.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"로그인 실패: 잘못된 사용자 이름 또는 비밀번호 ({form_data.username})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 사용자 이름 또는 비밀번호입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 액세스 토큰에 포함될 데이터
    access_token_data = {
        "sub": user.username,
        "email": user.email
    }
    
    # 액세스 토큰 생성
    access_token = create_access_token(
        data=access_token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # 리프레시 토큰 생성
    refresh_token = create_refresh_token(
        data={"sub": user.username}
    )
    
    logger.info(f"사용자 로그인 성공: {user.username}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh", summary="토큰 갱신", response_model=Token)
async def refresh_token(refresh_token: str):
    """
    리프레시 토큰을 사용하여 새로운 액세스 토큰 발급
    
    유효한 리프레시 토큰을 사용하여 새로운 액세스 토큰과 리프레시 토큰을 발급합니다.
    """
    try:
        # 리프레시 토큰 검증
        payload = decode_token(refresh_token)
        
        # 리프레시 토큰인지 확인
        if not payload.get("refresh"):
            logger.warning("토큰 갱신 실패: 유효하지 않은 리프레시 토큰 (refresh 필드 없음)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 리프레시 토큰입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        username = payload.get("sub")
        if not username:
            logger.warning("토큰 갱신 실패: 유효하지 않은 리프레시 토큰 (sub 필드 없음)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 리프레시 토큰입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 새로운 액세스 토큰 발급
        new_access_token = create_access_token(
            data={"sub": username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        # 새로운 리프레시 토큰 발급
        new_refresh_token = create_refresh_token(
            data={"sub": username}
        )
        
        logger.info(f"토큰 갱신 성공: {username}")
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except HTTPException:
        # 이미 처리된 예외는 그대로 전달
        raise
    except Exception as e:
        logger.error(f"토큰 갱신 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@protected_router.get("/me", summary="현재 사용자 정보 조회", response_model=UserResponse)
async def get_current_user_info(authorization: str = Header(None)):
    """
    현재 인증된 사용자의 정보 조회
    
    액세스 토큰을 사용하여 현재 로그인한 사용자의 정보를 조회합니다.
    """
    try:
        # Authorization 헤더가 없으면 에러
        if not authorization:
            logger.warning("사용자 정보 조회 실패: Authorization 헤더가 없습니다.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증 정보가 없습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Bearer 토큰 형식 확인
        if not authorization.startswith("Bearer "):
            logger.warning("사용자 정보 조회 실패: Bearer 토큰 형식이 아닙니다.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 형식입니다. Bearer 토큰을 사용하세요.",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 토큰 추출
        token = authorization.replace("Bearer ", "")
        
        # 토큰에서 사용자 정보 추출
        payload = decode_token(token)
        username = payload.get("sub")
        email = payload.get("email")
        
        if not username:
            logger.warning("사용자 정보 조회 실패: 토큰에 사용자 정보 없음")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 정보입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"사용자 정보 조회 성공: {username}")
        
        return UserResponse(
            username=username,
            email=email
        )
    except HTTPException:
        # 이미 처리된 예외는 그대로 전달
        raise
    except Exception as e:
        logger.error(f"사용자 정보 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        ) 