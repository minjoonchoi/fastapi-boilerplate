# FastAPI Boilerplate

FastAPI 애플리케이션 보일러플레이트 프로젝트입니다.

## 주요 기능

- 모듈화된 프로젝트 구조
- YAML 기반의 환경별 설정 관리
- 상세한 HTTP 요청/응답 로깅 미들웨어
- 통합 인증 시스템 (JWT 토큰 및 API 키 지원)
- 후행 슬래시 자동 정규화 미들웨어
- 헬스 체크 엔드포인트
- 파일 업로드 지원
- OpenAPI 문서 커스터마이징 및 Swagger UI 향상
- Docker 및 Docker Compose 지원
- Python 3.11+ 지원
- 의존성 관리를 위한 pyproject.toml 구조
- uv 패키지 관리자 지원

## 환경별 설정 사용 방법

이 프로젝트는 YAML 기반의 설정 시스템을 사용하며, 여러 환경(개발, 테스트, 프로덕션)에 따라 다른 설정을 적용할 수 있습니다.

### 설정 파일 구조

- `config.common.yaml`: 모든 환경에서 공통으로 사용되는 기본 설정
- `config.dev.yaml`: 개발 환경 고유 설정
- `config.test.yaml`: 테스트 환경 고유 설정
- `config.prod.yaml`: 프로덕션 환경 고유 설정

환경별 설정 파일은 공통 설정을 덮어쓰는 방식으로 작동합니다. 즉, 공통 설정에 정의된 값이 환경별 설정 파일에도 있다면 환경별 설정이 우선합니다.

### 공통 설정과 환경별 설정 작성 방법

1. 모든 환경에서 동일하게 사용할 설정은 `config.common.yaml`에 작성합니다.
2. 환경별로 다르게 적용할 설정만 각 환경 설정 파일에 작성합니다.

예를 들어:

```yaml
# config.common.yaml
api:
  prefix: "/api"

logging:
  console: true
  detailed_format: true
```

```yaml
# config.dev.yaml
app:
  name: "FastAPI Dev"
  env: "dev"
  debug: true

logging:
  level: "DEBUG"  # 공통 설정의 logging과 병합됨
```

### 로컬에서 특정 환경 사용하기

환경 변수 `APP_ENV`를 설정하여 특정 환경의 설정을 사용할 수 있습니다:

```bash
# 개발 환경 설정 사용
APP_ENV=dev python main.py

# 테스트 환경 설정 사용
APP_ENV=test python main.py

# 프로덕션 환경 설정 사용
APP_ENV=prod python main.py
```

또는 run.py 스크립트를 사용할 수 있습니다:

```bash
# 개발 환경 실행
python run.py dev

# 테스트 환경 실행
python run.py test

# 프로덕션 환경 실행
python run.py prod
```

pyproject.toml에 정의된 스크립트를 사용할 수도 있습니다:

```bash
# 개발 환경 실행
run-dev

# 테스트 환경 실행
run-test

# 프로덕션 환경 실행
run-prod
```

### Docker 빌드 시 환경 지정

Docker 이미지를 빌드할 때 `--build-arg` 옵션을 사용하여 환경을 지정할 수 있습니다:

```bash
# 개발 환경 이미지 빌드
docker build --build-arg APP_ENV=dev -t myapp:dev .

# 프로덕션 환경 이미지 빌드
docker build --build-arg APP_ENV=prod -t myapp:prod .
```

### Docker Compose로 여러 환경 실행

```bash
# 개발 환경 실행
docker-compose up app-dev

# 테스트 환경 실행
docker-compose up app-test

# 프로덕션 환경 실행
docker-compose up app-prod
```

## 설정 우선순위

설정은 다음 우선순위로 적용됩니다:

1. 환경별 설정 (`config.<env>.yaml`)
2. 공통 설정 (`config.common.yaml`)
3. 코드에 내장된 기본값

설정 파일을 찾는 순서는 다음과 같습니다:

1. `CONFIG_PATH` 환경 변수에 지정된 파일
2. `APP_ENV` 환경 변수 값에 따른 `config.<env>.yaml` 파일
3. 기본 `config.yaml` 파일

## 개발 가이드

### 의존성 설치

```bash
# uv 사용 (권장)
uv pip install -e .

# 개발 의존성 포함하여 설치
uv pip install -e ".[dev]"

# pip 사용
pip install -e .
```

### 개발 서버 실행

```bash
# run.py 사용
python run.py dev

# pyproject.toml script 사용
run-dev

# uvicorn 직접 사용
uvicorn main:app --reload
```

### 테스트 실행

```bash
pytest
```

## 배포 가이드

### Docker 이미지 빌드

```bash
docker build --build-arg APP_ENV=prod -t myapp:prod .
```

### Docker 이미지 실행

```bash
docker run -p 8000:8000 myapp:prod
```

### Docker Compose 사용

```bash
# 모든 서비스 시작
docker-compose up

# 특정 환경 실행
docker-compose up app-prod

# 백그라운드 실행
docker-compose up -d
```

## API 문서

애플리케이션 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 인증 시스템

이 애플리케이션은 통합된 인증 헤더 시스템을 사용합니다. 모든 보호된 엔드포인트는 `Authorization` 헤더를 통해 인증됩니다.

### 지원하는 인증 방식

`Authorization` 헤더는 다음 두 가지 형식을 지원합니다:

1. **JWT 토큰 인증**: `Bearer your-token` 형식으로 전달
2. **API 키 인증**: `ApiKey your-api-key` 형식으로 전달

### API 요청 시 인증 헤더 사용법

API 요청 시 다음과 같이 인증 헤더를 포함해야 합니다:

```
# JWT 토큰 인증
Authorization: Bearer your-jwt-token

# API 키 인증
Authorization: ApiKey your-api-key
```

예제 (curl 사용):

```bash
# JWT 토큰 사용
curl -H "Authorization: Bearer your-jwt-token" http://localhost:8000/api/items

# API 키 사용
curl -H "Authorization: ApiKey your-api-key" http://localhost:8000/api/items
```

### JWT 토큰 발급 받기

JWT 토큰을 발급받으려면 `/api/auth/token` 엔드포인트를 사용합니다:

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=password"
```

응답으로 access_token과 refresh_token을 받게 됩니다.

### Swagger UI에서 인증하기

Swagger UI에서 API를 테스트하기 위해 다음 단계를 따르세요:

1. 화면 상단의 "Authorize" 버튼 클릭
2. "CustomHeaderAuth" 섹션에서 완전한 헤더 값 입력:
   - JWT 토큰 사용: `Bearer eyJ0eXAi...`
   - API 키 사용: `ApiKey your-api-key`
3. "Authorize" 버튼 클릭하여 인증 정보 적용

인증 정보는 페이지를 새로고침해도 유지됩니다.

### API 키 설정 방법

API 키는 보안을 위해 환경변수로만 관리됩니다:

```bash
# 환경변수로 API 키 설정 후 실행
API_KEY=your-secret-api-key python run.py dev
```

### 인증 제외 경로

인증에서 제외할 경로 패턴은 YAML 설정 파일에서 관리됩니다. 기본 설정에서는 다음 경로가 제외됩니다:

```yaml
# config.common.yaml
api:
  auth:
    api_key:
      exclude_patterns:
        - "/health/**"    # 헬스 체크 경로 및 모든 하위 경로
        - "/metrics"      # 메트릭 경로
        - "/docs/**"      # Swagger UI 문서 관련 모든 경로
        - "/redoc/**"     # ReDoc 문서 관련 모든 경로
        - "/openapi.json" # OpenAPI 스키마 파일
    jwt:
      exclude_patterns:
        - "/health/**"    # 헬스 체크 경로 및 모든 하위 경로
        - "/metrics"      # 메트릭 경로
        - "/docs/**"      # Swagger UI 문서 관련 모든 경로
        - "/redoc/**"     # ReDoc 문서 관련 모든 경로
        - "/openapi.json" # OpenAPI 스키마 파일
        - "/api/auth/token" # 로그인 엔드포인트
```

## 라우터 시스템

애플리케이션은 다음과 같은 라우터 구조를 가지고 있습니다:

1. **보호된 라우터**: 인증이 필요한 엔드포인트
   - `api_router`: 인증이 필요한 API 엔드포인트
   - `auth_protected_router`: 인증이 필요한 인증 관련 엔드포인트
   
2. **공개 라우터**: 인증이 필요 없는 엔드포인트
   - `api_public_router`: 인증이 필요 없는 API 엔드포인트
   - `auth_router`: 인증이 필요 없는 인증 관련 엔드포인트
   - `health_router`: 헬스 체크 엔드포인트

### 새 엔드포인트 추가 방법

#### 인증이 필요한 엔드포인트 추가

```python
# app/routers/custom.py 예시
from fastapi import APIRouter, Depends
from app.core.security import global_auth_header

# 인증이 필요한 라우터 생성
router = APIRouter(
    prefix="/custom",
    tags=["custom"],
    responses={401: {"description": "인증 실패"}},
    dependencies=[Depends(global_auth_header)]  # 인증 의존성 적용
)

@router.get("/items")
async def get_items():
    return [{"id": 1, "name": "Item 1"}]
```

#### 인증이 필요 없는 엔드포인트 추가

```python
# app/routers/custom.py 예시
from fastapi import APIRouter

# 인증이 필요 없는 라우터 생성
public_router = APIRouter(
    prefix="/custom",
    tags=["custom"]
)

@public_router.get("/public-items")
async def get_public_items():
    return [{"id": 1, "name": "Public Item 1"}]
```

## 로깅 시스템

애플리케이션은 자세한 HTTP 요청/응답 로깅 시스템을 갖추고 있습니다.

### 로깅 제외 경로

로깅 미들웨어에서 제외할 경로 패턴은 YAML 설정 파일에서 관리됩니다:

```yaml
# config.common.yaml
logging:
  http:
    exclude_patterns:
      - "/health/**"     # 헬스 체크 경로 및 모든 하위 경로
      - "/metrics"     # 메트릭 경로
      - "/docs/**"       # Swagger UI 문서 관련 모든 경로
      - "/redoc/**"      # ReDoc 문서 관련 모든 경로
      - "/openapi.json" # OpenAPI 스키마 파일
      - "/favicon.ico"  # 파비콘 요청
```

### 패턴 매칭 규칙

경로 패턴은 다음 두 가지 와일드카드를 지원합니다:

- `/*`: 정확히 하나의 경로 세그먼트와 매칭
- `/**`: 0개 이상의 모든 하위 경로와 재귀적으로 매칭

## 후행 슬래시 처리

애플리케이션은 후행 슬래시(trailing slash)를 자동으로 제거하여 URL 경로를 일관되게 처리합니다:

- 모든 URL에서 후행 슬래시가 자동으로 제거됩니다 (루트 경로 '/' 제외)
- 예: `/api/users/` 경로는 자동으로 `/api/users`로 처리
- 미들웨어는 내부적으로 경로를 정규화하므로 리다이렉트가 발생하지 않음

## 프로젝트 구조

```
├── app/                # 애플리케이션 패키지
│   ├── __init__.py     # 패키지 초기화
│   ├── core/           # 핵심 기능
│   │   ├── __init__.py
│   │   ├── auth.py     # 인증 관련 핵심 기능
│   │   ├── security.py # 보안 스키마 정의
│   │   ├── logging_config.py # 로깅 설정
│   │   ├── status.py   # HTTP 상태 코드 및 응답
│   │   └── yaml_config.py # YAML 설정 처리
│   ├── middleware/     # 미들웨어 컴포넌트
│   │   ├── __init__.py
│   │   ├── request_logging.py # 요청/응답 로깅
│   │   ├── api_key_auth.py # 인증 미들웨어
│   │   └── trailing_slash.py # 후행 슬래시 제거 미들웨어
│   └── routers/        # API 엔드포인트
│       ├── __init__.py
│       ├── api.py      # API 라우터
│       ├── auth.py     # 인증 라우터
│       ├── upload.py   # 파일 업로드 라우터
│       └── health.py   # 헬스 체크 엔드포인트
├── uploads/            # 업로드된 파일 저장 디렉토리
├── .dockerignore       # Docker 빌드 제외 파일
├── .gitignore          # Git 제외 파일
├── config.common.yaml  # 공통 설정
├── config.dev.yaml     # 개발 환경 설정
├── config.test.yaml    # 테스트 환경 설정
├── config.prod.yaml    # 프로덕션 환경 설정
├── docker-compose.yml  # Docker Compose 설정
├── Dockerfile          # Docker 빌드 지침
├── main.py             # 애플리케이션 진입점
├── pyproject.toml      # 프로젝트 및 의존성 정보
├── run.py              # 실행 스크립트
└── README.md           # 프로젝트 문서
```

## 의존성

주요 의존성 목록:

- fastapi==0.115.12
- uvicorn==0.34.2
- pydantic==2.11.4
- python-dotenv==1.1.0
- pyyaml==6.0.1
- python-multipart==0.0.9
- python-jose==3.3.0
- passlib==1.7.4

개발 의존성:
- pytest
- black