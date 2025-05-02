#!/usr/bin/env python3
"""
FastAPI 프로젝트 생성 스크립트
이 스크립트는 fastapi-boilerplate를 기반으로 새로운 프로젝트를 생성합니다.
"""

import os
import sys
import shutil
import re
from pathlib import Path

def get_project_name():
    """프로젝트 이름을 입력받습니다."""
    while True:
        name = input("새로운 프로젝트 이름을 입력하세요 (예: my-fastapi-app): ").strip()
        if not name:
            print("프로젝트 이름은 비워둘 수 없습니다.")
            continue
        if not re.match(r'^[a-z0-9-]+$', name):
            print("프로젝트 이름은 소문자, 숫자, 하이픈(-)만 사용할 수 있습니다.")
            continue
        return name

def update_file_content(file_path, old_name, new_name):
    """파일 내용에서 프로젝트 이름을 변경합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 프로젝트 이름 변경
        content = content.replace(old_name, new_name)
        
        # 패키지 이름 변경 (하이픈을 언더스코어로)
        old_pkg = old_name.replace('-', '_')
        new_pkg = new_name.replace('-', '_')
        content = content.replace(old_pkg, new_pkg)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Error updating {file_path}: {e}")

def update_pyproject_toml(file_path, new_name):
    """pyproject.toml 파일을 업데이트합니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 프로젝트 이름만 변경하고 패키지 이름은 app으로 유지
        content = re.sub(
            r'name = "fastapi-boilerplate"',
            f'name = "{new_name}"',
            content
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print(f"Error updating pyproject.toml: {e}")

def create_new_project():
    """새로운 프로젝트를 생성합니다."""
    # 현재 디렉토리 확인
    current_dir = Path.cwd()
    if current_dir.name != "fastapi-boilerplate":
        print("이 스크립트는 fastapi-boilerplate 디렉토리에서 실행해야 합니다.")
        sys.exit(1)
    
    # 새 프로젝트 이름 입력
    new_name = get_project_name()
    
    # 상위 디렉토리로 이동
    parent_dir = current_dir.parent
    new_project_dir = parent_dir / new_name
    
    # 새 프로젝트 디렉토리가 이미 존재하는지 확인
    if new_project_dir.exists():
        print(f"Error: {new_name} 디렉토리가 이미 존재합니다.")
        sys.exit(1)
    
    try:
        # 프로젝트 복사
        print(f"프로젝트를 {new_name}으로 복사하는 중...")
        shutil.copytree(current_dir, new_project_dir, ignore=shutil.ignore_patterns(
            '.git', '__pycache__', '*.pyc', '.pytest_cache', '.ruff_cache',
            '*.egg-info', '.venv', 'venv', 'logs', 'uploads'
        ))
        
        # 새 프로젝트 디렉토리로 이동
        os.chdir(new_project_dir)
        
        # 파일 내용 업데이트
        files_to_update = [
            'README.md',
            'Dockerfile',
            'docker-compose.yml',
            'main.py',
            'run.py'
        ]
        
        for file in files_to_update:
            if os.path.exists(file):
                update_file_content(file, 'fastapi-boilerplate', new_name)
        
        # pyproject.toml 업데이트
        if os.path.exists('pyproject.toml'):
            update_pyproject_toml('pyproject.toml', new_name)
        
        # git 초기화
        os.system('git init')
        
        print(f"\n프로젝트가 성공적으로 생성되었습니다: {new_name}")
        print("\n다음 단계:")
        print(f"1. cd {new_name}")
        print("2. make venv")
        print("3. make install")
        print("4. make run-dev")
        
    except Exception as e:
        print(f"Error: {e}")
        if new_project_dir.exists():
            shutil.rmtree(new_project_dir)
        sys.exit(1)

if __name__ == "__main__":
    create_new_project() 