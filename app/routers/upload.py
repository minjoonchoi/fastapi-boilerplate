from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from typing import List, Optional
import os
import uuid
import shutil
import aiofiles
from pathlib import Path
from datetime import datetime

from app.core.logging_config import get_logger
from app.core.yaml_config import yaml_settings

router = APIRouter(prefix="/upload", tags=["upload"])

# 로거 설정
logger = get_logger(__name__)

# YAML 설정에서 업로드 설정 가져오기
UPLOAD_DIR = Path(yaml_settings.upload.path)
MAX_FILE_SIZE = yaml_settings.upload.max_file_size
TOTAL_MAX_SIZE = yaml_settings.upload.max_total_size
ALLOWED_EXTENSIONS = yaml_settings.upload.allowed_extensions

# 파일 확장자 검증 함수
def is_valid_extension(filename: str) -> bool:
    """
    파일 확장자가 허용된 확장자 목록에 있는지 확인
    빈 목록인 경우 모든 확장자 허용
    """
    if not ALLOWED_EXTENSIONS:  # 빈 목록이면 모든 확장자 허용
        return True
        
    extension = os.path.splitext(filename)[1].lower().lstrip('.')
    return extension in [ext.lower().lstrip('.') for ext in ALLOWED_EXTENSIONS]

@router.post("/file", 
            summary="단일 파일 업로드",
            description=f"단일 파일을 업로드합니다. 최대 파일 크기: {MAX_FILE_SIZE/(1024*1024)}MB")
async def upload_file(
    file: UploadFile = File(...),
    content_length: Optional[int] = Header(None)
):
    """
    단일 파일 업로드 API
    
    파일 크기 제한: {MAX_FILE_SIZE/(1024*1024)}MB
    허용 파일 형식: {", ".join(ALLOWED_EXTENSIONS) if ALLOWED_EXTENSIONS else "모든 형식"}
    
    이 엔드포인트는 API 키 인증이 필요합니다.
    """
    # 파일 크기 검사 (Header에서 content_length 확인)
    if content_length and content_length > MAX_FILE_SIZE:
        logger.warning(f"파일 크기 제한 초과: {content_length} 바이트")
        raise HTTPException(
            status_code=413,
            detail=f"파일 크기가 제한({MAX_FILE_SIZE/(1024*1024)}MB)을 초과했습니다."
        )
    
    # 파일 확장자 검사
    if not is_valid_extension(file.filename):
        logger.warning(f"허용되지 않은 파일 형식: {file.filename}")
        raise HTTPException(
            status_code=415, 
            detail="허용되지 않은 파일 형식입니다."
        )
    
    # 업로드 디렉토리 생성 (없는 경우)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # 고유한 파일명 생성 (UUID + 원본 확장자)
    original_filename = file.filename
    extension = os.path.splitext(original_filename)[1] if original_filename else ""
    unique_filename = f"{uuid.uuid4()}{extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    try:
        # 파일 저장 (비동기)
        async with aiofiles.open(file_path, 'wb') as f:
            # 청크 단위로 파일 읽기/쓰기
            chunk_size = 1024 * 1024  # 1MB 청크
            total_size = 0
            
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    # 청크 읽는 중간에 크기 제한 초과 확인
                    await f.close()
                    os.unlink(file_path)  # 파일 삭제
                    logger.warning(f"파일 업로드 중 크기 제한 초과: {total_size} 바이트")
                    raise HTTPException(
                        status_code=413, 
                        detail=f"파일 크기가 제한({MAX_FILE_SIZE/(1024*1024)}MB)을 초과했습니다."
                    )
                
                await f.write(chunk)
        
        logger.info(f"파일 업로드 성공: {original_filename} -> {unique_filename} ({total_size} 바이트)")
        
        # 성공 응답
        return {
            "filename": original_filename,
            "stored_filename": unique_filename,
            "size": total_size,
            "content_type": file.content_type,
            "upload_time": datetime.now().isoformat()
        }
    
    except Exception as e:
        # 에러 발생 시 파일 삭제 시도
        if os.path.exists(file_path):
            os.unlink(file_path)
        
        logger.error(f"파일 업로드 실패: {original_filename} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류 발생: {str(e)}")


@router.post("/files",
            summary="다중 파일 업로드",
            description=f"여러 파일을 한 번에 업로드합니다. 최대 총 크기: {TOTAL_MAX_SIZE/(1024*1024)}MB")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    content_length: Optional[int] = Header(None)
):
    """
    다중 파일 업로드 API
    
    총 파일 크기 제한: {TOTAL_MAX_SIZE/(1024*1024)}MB
    개별 파일 크기 제한: {MAX_FILE_SIZE/(1024*1024)}MB
    허용 파일 형식: {", ".join(ALLOWED_EXTENSIONS) if ALLOWED_EXTENSIONS else "모든 형식"}
    
    이 엔드포인트는 API 키 인증이 필요합니다.
    """
    # 전체 요청 크기 제한
    if content_length and content_length > TOTAL_MAX_SIZE:
        logger.warning(f"총 파일 크기 제한 초과: {content_length} 바이트")
        raise HTTPException(
            status_code=413,
            detail=f"총 파일 크기가 제한({TOTAL_MAX_SIZE/(1024*1024)}MB)을 초과했습니다."
        )
    
    if not files:
        raise HTTPException(status_code=400, detail="파일이 제공되지 않았습니다.")
    
    # 결과 저장 리스트
    result = []
    total_size = 0
    
    # 업로드 디렉토리 생성 (없는 경우)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    for file in files:
        original_filename = file.filename
        
        # 파일 확장자 검사
        if not is_valid_extension(original_filename):
            logger.warning(f"허용되지 않은 파일 형식: {original_filename}")
            # 이미 업로드된 파일들 삭제
            for item in result:
                try:
                    os.unlink(UPLOAD_DIR / item["stored_filename"])
                except:
                    pass
            raise HTTPException(
                status_code=415, 
                detail=f"허용되지 않은 파일 형식: {original_filename}"
            )
        
        extension = os.path.splitext(original_filename)[1] if original_filename else ""
        unique_filename = f"{uuid.uuid4()}{extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        try:
            # 파일 저장 (비동기)
            async with aiofiles.open(file_path, 'wb') as f:
                # 청크 단위로 파일 읽기/쓰기
                chunk_size = 1024 * 1024  # 1MB 청크
                file_size = 0
                
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    
                    file_size += len(chunk)
                    total_size += len(chunk)
                    
                    # 개별 파일 크기 제한 확인
                    if file_size > MAX_FILE_SIZE:
                        await f.close()
                        os.unlink(file_path)  # 파일 삭제
                        logger.warning(f"파일 크기 제한 초과: {file.filename} - {file_size} 바이트")
                        raise HTTPException(
                            status_code=413, 
                            detail=f"파일 '{file.filename}'의 크기가 제한({MAX_FILE_SIZE/(1024*1024)}MB)을 초과했습니다."
                        )
                    
                    # 전체 크기 제한 확인
                    if total_size > TOTAL_MAX_SIZE:
                        await f.close()
                        os.unlink(file_path)  # 파일 삭제
                        logger.warning(f"총 파일 크기 제한 초과: {total_size} 바이트")
                        raise HTTPException(
                            status_code=413, 
                            detail=f"총 파일 크기가 제한({TOTAL_MAX_SIZE/(1024*1024)}MB)을 초과했습니다."
                        )
                    
                    await f.write(chunk)
            
            # 파일 정보 저장
            result.append({
                "filename": original_filename,
                "stored_filename": unique_filename,
                "size": file_size,
                "content_type": file.content_type,
                "upload_time": datetime.now().isoformat()
            })
            
            logger.info(f"파일 업로드 성공: {original_filename} -> {unique_filename} ({file_size} 바이트)")
            
        except HTTPException:
            # 이미 처리된 HTTPException은 그대로 전달
            # 업로드된 파일들 삭제
            for item in result:
                try:
                    os.unlink(UPLOAD_DIR / item["stored_filename"])
                except:
                    pass
            raise
        
        except Exception as e:
            # 에러 발생 시 파일 삭제 시도
            if os.path.exists(file_path):
                os.unlink(file_path)
            
            # 이미 업로드된 파일들 삭제
            for item in result:
                try:
                    os.unlink(UPLOAD_DIR / item["stored_filename"])
                except:
                    pass
            
            logger.error(f"파일 업로드 실패: {original_filename} - {str(e)}")
            raise HTTPException(status_code=500, detail=f"파일 업로드 중 오류 발생: {str(e)}")
    
    return {
        "message": f"{len(files)}개 파일 업로드 성공",
        "total_size": total_size,
        "files": result
    }

@router.get("/file/{filename}", 
           summary="파일 다운로드",
           description="업로드된 파일을 다운로드합니다.")
async def download_file(filename: str):
    """
    파일 다운로드 API
    
    파일명(UUID)을 이용해 업로드된 파일을 다운로드합니다.
    
    이 엔드포인트는 API 키 인증이 필요합니다.
    """
    file_path = UPLOAD_DIR / filename
    
    if not os.path.exists(file_path):
        logger.warning(f"요청한 파일을 찾을 수 없음: {filename}")
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    logger.info(f"파일 다운로드: {filename}")
    return FileResponse(
        path=file_path,
        filename=filename,  # 다운로드될 파일명
        media_type="application/octet-stream"  # 범용 바이너리 데이터
    )

@router.get("/files", 
           summary="업로드된 파일 목록",
           description="현재 업로드된 모든 파일의 목록을 조회합니다.",
           openapi_extra={"security": []})
async def list_files():
    """
    업로드된 파일 목록 조회 API
    
    모든 업로드된 파일의 목록과 상세 정보를 반환합니다.
    
    이 엔드포인트는 API 키 인증이 필요하지 않습니다.
    """
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        files = []
        
        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                files.append({
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "created": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                    "download_url": f"/api/upload/file/{file_path.name}"
                })
        
        return {
            "total": len(files),
            "files": files
        }
    except Exception as e:
        logger.error(f"파일 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 목록을 조회하는 중 오류가 발생했습니다.") 