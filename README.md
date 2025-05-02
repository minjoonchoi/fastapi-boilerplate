# FastAPI Boilerplate

FastAPI 기반의 프로덕션 레벨 웹 애플리케이션을 위한 보일러플레이트입니다.

## 주요 기능

- 🚀 **FastAPI 기반**: 현대적이고 빠른 Python 웹 프레임워크
- 🔒 **통합 인증 시스템**: JWT 토큰과 API 키 기반 인증
- 📝 **자동 API 문서화**: Swagger UI와 ReDoc 지원
- 🔄 **비동기 처리**: 비동기 데이터베이스 작업 지원
- 📊 **로깅 시스템**: 구조화된 로깅과 요청/응답 로깅
- 🔧 **환경 설정**: YAML 기반 설정 관리
- 🐳 **Docker 지원**: 컨테이너화된 배포 환경
- 📦 **의존성 관리**: uv를 통한 빠른 패키지 관리
- 🧪 **테스트 환경**: pytest 기반 테스트 프레임워크
- 🔍 **코드 품질**: Ruff를 통한 린팅과 포맷팅
- 📈 **성능 모니터링**: 요청/응답 시간 측정
- 🔐 **보안**: CORS, API 키 인증, 요청 검증
- 📁 **파일 업로드**: 안전한 파일 업로드 처리
- 🏥 **헬스 체크**: 시스템 상태 모니터링
- 🔄 **마이그레이션**: Alembic을 통한 데이터베이스 마이그레이션

## 시작하기

### 필수 요구사항

- Python 3.11 이상
- uv (의존성 관리)
- Docker (선택사항)

### 설치

1. 저장소 클론:
```bash
git clone https://github.com/yourusername/fastapi-boilerplate.git
cd fastapi-boilerplate
```

2. 의존성 설치:
```bash
make install
```

3. 환경 설정:
```bash
cp config/config.example.yaml config/config.yaml
# config.yaml 파일을 환경에 맞게 수정
```

### 개발 서버 실행

```bash
make run-dev
```

### 프로덕션 서버 실행

```bash
make run-prod
```

### 테스트 실행

```bash
make test
```

## 프로젝트 구조

```
fastapi-boilerplate/
├── alembic/              # 데이터베이스 마이그레이션
├── app/
│   ├── api/             # API 엔드포인트
│   ├── core/            # 핵심 설정 및 유틸리티
│   ├── db/              # 데이터베이스 관련 코드
│   ├── middleware/      # 미들웨어
│   ├── models/          # 데이터베이스 모델
│   ├── schemas/         # Pydantic 스키마
│   └── services/        # 비즈니스 로직
├── config/              # 설정 파일
├── logs/                # 로그 파일
├── tests/               # 테스트 코드
├── uploads/             # 업로드된 파일
├── .env                 # 환경 변수
├── .gitignore
├── Dockerfile
├── Makefile            # 개발 명령어
├── README.md
├── docker-compose.yml
├── main.py             # 애플리케이션 진입점
├── pyproject.toml      # 프로젝트 메타데이터
└── run.py              # 서버 실행 스크립트
```

## 주요 명령어

- `make install`: 의존성 설치
- `make run-dev`: 개발 서버 실행
- `make run-prod`: 프로덕션 서버 실행
- `make test`: 테스트 실행
- `make lint`: 코드 린팅
- `make format`: 코드 포맷팅
- `make migrate`: 데이터베이스 마이그레이션
- `make docker-build`: Docker 이미지 빌드
- `make docker-run`: Docker 컨테이너 실행
- `make create-project`: 새 프로젝트 생성

## API 문서

- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

## 인증

이 API는 두 가지 인증 방식을 지원합니다:

1. **JWT 토큰**: `Bearer your-token` 형식
2. **API 키**: `ApiKey your-api-key` 형식

## 환경 변수

- `APP_ENV`: 애플리케이션 환경 (dev/prod/test)
- `PORT`: 서버 포트 (기본값: 8080)
- `DATABASE_URL`: 데이터베이스 연결 URL

## 라이선스

MIT License