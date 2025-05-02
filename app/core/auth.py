"""
인증 관련 유틸리티 함수 모듈
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Union, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.yaml_config import yaml_settings
from app.core.logging_config import get_logger

# 로거 설정
logger = get_logger(__name__)

# 비밀번호 해싱을 위한 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
SECRET_KEY = yaml_settings.api.auth.jwt.secret_key
ALGORITHM = yaml_settings.api.auth.jwt.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = yaml_settings.api.auth.jwt.token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = yaml_settings.api.auth.jwt.refresh_token_expire_days

# 사용자 모델 (예시)
class User:
    def __init__(self, username: str, email: str = None, disabled: bool = False):
        self.username = username
        self.email = email
        self.disabled = disabled

# 비밀번호 유틸리티 함수
def get_password_hash(password: str) -> str:
    """비밀번호를 해시화합니다."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증: 일반 텍스트와 해시된 비밀번호 비교"""
    return pwd_context.verify(plain_password, hashed_password)

# 예시 사용자 데이터베이스 (실제로는 데이터베이스에서 가져와야 함)
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": get_password_hash("admin123"),
        "disabled": False,
    },
    "user": {
        "username": "user",
        "email": "user@example.com",
        "hashed_password": get_password_hash("user123"),
        "disabled": False,
    }
}

def get_user(username: str) -> Optional[User]:
    """사용자 이름으로 사용자 정보 조회 (예시)"""
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return User(
            username=user_dict["username"],
            email=user_dict["email"],
            disabled=user_dict["disabled"]
        )
    return None

def authenticate_user(username: str, password: str) -> Union[User, bool]:
    """사용자 인증: 사용자 이름과 비밀번호로 검증"""
    user = None
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        if verify_password(password, user_dict["hashed_password"]):
            return User(
                username=user_dict["username"],
                email=user_dict["email"],
                disabled=user_dict["disabled"]
            )
    return False

# 토큰 관련 함수
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """리프레시 토큰 생성"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "refresh": True})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """토큰 디코딩"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT 디코딩 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_token_data(token: str) -> Dict[str, Any]:
    """토큰에서 데이터 추출 (검증 포함)"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 정보입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError as e:
        logger.warning(f"JWT 검증 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        ) 