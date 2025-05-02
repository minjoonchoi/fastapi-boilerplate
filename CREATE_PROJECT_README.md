# FastAPI 프로젝트 생성 스크립트

`create_project.py` 스크립트는 FastAPI Boilerplate 프로젝트를 기반으로 새로운 프로젝트를 쉽게 생성할 수 있는 도구입니다.

## 기능

- FastAPI Boilerplate 프로젝트를 지정한 경로에 복사
- 프로젝트 이름과 관련 참조 자동 변경
- git 저장소 초기화 (새로운 .git 폴더 생성)
- 불필요한 파일 (__pycache__ 등) 제외 처리
- 기존 .gitignore 파일 사용 (존재하는 경우)

## 사용법

```bash
./create_project.py <프로젝트명> [경로]
```

### 인자 설명

- `<프로젝트명>`: 필수 인자. 새 프로젝트의 이름 (예: my-awesome-api)
- `[경로]`: 선택 인자. 새 프로젝트가 생성될 경로 (기본값: 현재 디렉토리)

### 옵션

- `--no-git-init`: git 저장소 초기화를 건너뜁니다.
- `--quiet`: 간소화된 출력을 표시합니다.

## 사용 예제

### 기본 사용법

```bash
# 현재 디렉토리에 'my-api-project' 프로젝트 생성
./create_project.py my-api-project
```

### 특정 경로에 프로젝트 생성

```bash
# /path/to/projects 디렉토리에 'my-api-project' 프로젝트 생성
./create_project.py my-api-project /path/to/projects
```

### git 초기화 없이 프로젝트 생성

```bash
./create_project.py my-api-project --no-git-init
```

### 간소화된 출력으로 프로젝트 생성

```bash
./create_project.py my-api-project --quiet
```

## 설치 방법

스크립트를 실행하기 전에 실행 권한을 부여해야 합니다:

```bash
chmod +x create_project.py
```

## 프로젝트 생성 후 작업

스크립트는 프로젝트 생성 후 다음 단계를 수행하도록 안내합니다:

1. 생성된 프로젝트 디렉토리로 이동
2. 가상 환경 생성 및 활성화
3. 프로젝트 의존성 설치
4. 개발 서버 실행

```bash
cd <프로젝트명>
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
python run.py dev
```

## 참고 사항

- 프로젝트 이름은 소문자, 숫자, 하이픈(-), 언더스코어(_)만 사용할 수 있으며, 문자나 숫자로 시작해야 합니다.
- 대상 디렉토리가 이미 존재하는 경우 스크립트가 중단됩니다.
- 스크립트는 `README.md`, `main.py`, 설정 파일 등의 내용에서 'FastAPI Boilerplate'를 새 프로젝트 이름으로 자동 변경합니다.
- 소스 프로젝트에 `.gitignore` 파일이 있으면 그대로 복사해서 사용하고, 없는 경우에만 기본 내용으로 새로 생성합니다. 