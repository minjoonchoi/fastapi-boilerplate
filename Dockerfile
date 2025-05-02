FROM python:3.13-slim

# 필요한 시스템 라이브러리 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    gcc \
    ca-certificates \
    bash \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 쉘을 bash로 변경 (source 명령 사용을 위해)
SHELL ["/bin/bash", "-c"]

# 애플리케이션 환경 설정 (기본값은 prod, 빌드 시점에 변경 가능)
ARG APP_ENV=prod
ENV APP_ENV=${APP_ENV}

# 포트 설정 (기본값 8080)
ENV PORT=8080

# API 키 설정 (빌드 시점에 제공해야 함)
ARG API_KEY=""
ENV API_KEY=${API_KEY}

# 작업 디렉토리 설정
WORKDIR /app

# 소스 코드 복사 (의존성 설치 전에 전체 코드 복사)
COPY . .

# README.md 파일이 없을 경우 생성
RUN if [ ! -f README.md ]; then echo "# FastAPI Application" > README.md; fi

# pyproject.toml 에서 문제가 될 수 있는 설정을 제거
RUN if grep -q "default-python" pyproject.toml; then \
        sed -i '/default-python/d' pyproject.toml; \
    fi

# pip를 사용해 uv와 최신 setuptools 설치
RUN pip install --no-cache-dir uv setuptools>=61.0.0 && \
    uv --version && \
    python -c "import setuptools; print(f'setuptools 버전: {setuptools.__version__}')"

# 가상환경 생성 및 패키지 설치 (activate 사용)
ENV VIRTUAL_ENV=/app/.venv
RUN uv venv ${VIRTUAL_ENV} && \
    source ${VIRTUAL_ENV}/bin/activate && \
    # pyproject.toml에서 프로젝트와 의존성 설치
    uv pip install --no-cache-dir -e . && \
    pip list && \
    echo "가상환경 설치 완료: $(which python)"

# 로그 디렉토리 생성
RUN mkdir -p /var/log/app logs

# 환경 변수에 PATH 추가하여 가상환경 활성화
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

# run.py에 실행 권한 부여
RUN chmod +x /app/run.py

# 환경변수에 따라 실행 명령어 결정 (run-dev, run-test, run-prod)
CMD run-${APP_ENV:-prod}

# 애플리케이션 포트 노출
EXPOSE ${PORT} 