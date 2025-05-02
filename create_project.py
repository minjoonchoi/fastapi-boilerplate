#!/usr/bin/env python3
"""
FastAPI Boilerplate 프로젝트 생성 스크립트

이 스크립트는 현재 FastAPI Boilerplate 프로젝트를 기반으로 새 프로젝트를 생성합니다.
경로와 프로젝트명을 입력받아 새 프로젝트를 설정합니다.
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path
import re


def parse_arguments():
    """명령줄 인자를 파싱합니다."""
    parser = argparse.ArgumentParser(
        description="FastAPI Boilerplate 프로젝트를 기반으로 새 프로젝트를 생성합니다."
    )
    parser.add_argument(
        "project_name",
        help="새 프로젝트의 이름 (예: my-awesome-api)"
    )
    parser.add_argument(
        "destination_path",
        nargs="?",
        default=".",
        help="새 프로젝트가 생성될 경로 (기본값: 현재 디렉토리)"
    )
    parser.add_argument(
        "--no-git-init",
        action="store_true",
        help="git 저장소 초기화를 건너뜁니다."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="간소화된 출력을 표시합니다."
    )
    return parser.parse_args()


def validate_project_name(project_name):
    """프로젝트 이름이 유효한지 확인합니다."""
    if not re.match(r'^[a-z0-9][a-z0-9_-]*$', project_name):
        print("오류: 프로젝트 이름은 소문자, 숫자, 하이픈(-), 언더스코어(_)만 사용할 수 있으며, 문자나 숫자로 시작해야 합니다.")
        sys.exit(1)
    return project_name


def get_source_project_path():
    """현재 스크립트가 있는 디렉토리를 반환합니다."""
    return os.path.dirname(os.path.abspath(__file__))


def create_project_directory(destination_path, project_name):
    """프로젝트 디렉토리를 생성합니다."""
    project_path = os.path.join(destination_path, project_name)
    if os.path.exists(project_path):
        print(f"오류: 경로가 이미 존재합니다: {project_path}")
        sys.exit(1)
    os.makedirs(project_path)
    return project_path


def copy_project_files(source_path, destination_path):
    """소스에서 대상으로 프로젝트 파일을 복사합니다."""
    # 특정 파일들을 제외하고 복사할 항목 (.gitignore는 복사함)
    ignore_patterns = ('.git', '__pycache__', '*.pyc', '*.pyo', '*.pyd', 
                        '.DS_Store', '.env', '.venv', 'env', 'venv', 'ENV', 
                        'env.bak', 'venv.bak', '.pytest_cache', 'create_project.py',
                        'CREATE_PROJECT_README.md')
    
    # 항목별로 복사
    for item in os.listdir(source_path):
        # 무시할 패턴인지 확인
        if any(fnmatch(item, pattern) for pattern in ignore_patterns):
            continue
        
        src_item_path = os.path.join(source_path, item)
        dst_item_path = os.path.join(destination_path, item)
        
        if os.path.isdir(src_item_path):
            # 디렉토리면 재귀적으로 복사
            shutil.copytree(src_item_path, dst_item_path, 
                           ignore=shutil.ignore_patterns(*ignore_patterns))
        else:
            # 파일이면 그대로 복사
            shutil.copy2(src_item_path, dst_item_path)


def fnmatch(name, pattern):
    """간단한 패턴 매칭 함수 (glob 스타일)"""
    if pattern.startswith('*'):
        return name.endswith(pattern[1:])
    return name == pattern


def initialize_git_repository(project_path, quiet=False):
    """새 프로젝트 디렉토리에서 git 저장소를 초기화합니다."""
    current_dir = os.getcwd()
    try:
        os.chdir(project_path)
        if not quiet:
            print(f"git 저장소 초기화 중: {project_path}")
        
        # git 초기화
        subprocess.run(["git", "init"], check=True, 
                      stdout=subprocess.DEVNULL if quiet else None)
        # 초기 커밋 생성
        subprocess.run(["git", "add", "."], check=True,
                      stdout=subprocess.DEVNULL if quiet else None)
        subprocess.run(["git", "commit", "-m", "Initial commit from FastAPI Boilerplate"], check=True,
                      stdout=subprocess.DEVNULL if quiet else None)
        
        if not quiet:
            print("git 저장소가 성공적으로 초기화되었습니다.")
    
    except subprocess.CalledProcessError as e:
        print(f"git 명령 실행 중 오류 발생: {e}")
    
    finally:
        # 원래 작업 디렉토리로 돌아가기
        os.chdir(current_dir)


def update_project_references(project_path, project_name, original_name="FastAPI Boilerplate"):
    """
    프로젝트 내 파일의 FastAPI Boilerplate 참조를 새 프로젝트 이름으로 업데이트합니다.
    """
    # 업데이트할 파일 목록
    files_to_update = [
        os.path.join(project_path, "README.md"),
        os.path.join(project_path, "main.py"),
        os.path.join(project_path, "config.common.yaml"),
        os.path.join(project_path, "config.dev.yaml"),
        os.path.join(project_path, "config.prod.yaml"),
        os.path.join(project_path, "config.test.yaml"),
    ]
    
    # 추가적으로 대상 파일 찾기
    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith(('.py', '.md', '.yaml', '.yml', '.toml')):
                file_path = os.path.join(root, file)
                if file_path not in files_to_update:
                    files_to_update.append(file_path)
    
    # 변환 대상 텍스트 패턴
    replacements = [
        (r"FastAPI Boilerplate", project_name),
        (r"fastapi-boilerplate", project_name.lower().replace(" ", "-")),
        (r"fastapi_boilerplate", project_name.lower().replace(" ", "_").replace("-", "_")),
    ]
    
    # 대상 파일의 내용 업데이트
    for file_path in files_to_update:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # 모든 패턴 치환
                for old, new in replacements:
                    content = re.sub(old, new, content)
                
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(content)
            
            except Exception as e:
                print(f"파일 업데이트 중 오류 발생: {file_path} - {e}")


def main():
    """메인 실행 함수"""
    args = parse_arguments()
    
    # 프로젝트 이름 검증
    project_name = validate_project_name(args.project_name)
    
    # 소스 프로젝트 경로 가져오기
    source_path = get_source_project_path()
    
    # 대상 경로 준비
    destination_path = os.path.abspath(args.destination_path)
    
    if not args.quiet:
        print(f"생성할 프로젝트: {project_name}")
        print(f"대상 경로: {destination_path}")
    
    # 프로젝트 디렉토리 생성
    project_path = create_project_directory(destination_path, project_name)
    
    # 프로젝트 파일 복사
    if not args.quiet:
        print(f"프로젝트 파일 복사 중...")
    copy_project_files(source_path, project_path)
    
    # 프로젝트 내 참조 업데이트
    if not args.quiet:
        print(f"프로젝트 내 참조 업데이트 중...")
    update_project_references(project_path, project_name)
    
    # git 저장소 초기화 (선택적)
    if not args.no_git_init:
        initialize_git_repository(project_path, args.quiet)
    
    if not args.quiet:
        print(f"\n✅ 프로젝트 생성 완료: {project_path}")
        print(f"시작하려면:")
        print(f"  cd {os.path.join(args.destination_path, project_name)}")
        print(f"  python -m venv venv")
        print(f"  source venv/bin/activate  # Windows: venv\\Scripts\\activate")
        print(f"  pip install -e .")
        print(f"  python run.py dev")


if __name__ == "__main__":
    main() 