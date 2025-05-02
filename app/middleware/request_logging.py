"""
HTTP 요청/응답 로깅을 위한 미들웨어
"""
import time
import uuid
import logging
import json
import io
import copy
import fnmatch
from typing import List, Dict, Any, Set, Optional, Union, Tuple
from fastapi import Request, Response
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send, Message
from starlette.datastructures import Headers, UploadFile
from app.core.yaml_config import yaml_settings

logger = logging.getLogger(__name__)

# 로깅에서 제외할 민감한 필드 (YAML 설정에서 가져옴)
DEFAULT_SENSITIVE_FIELDS = yaml_settings.logging.sensitive_fields_set

# 파일 관련 컨텐츠 타입
FILE_CONTENT_TYPES = {
    "multipart/form-data",
    "application/octet-stream",
    "application/pdf",
    "application/zip",
    "application/x-zip-compressed",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/svg+xml",
    "application/vnd.openxmlformats-officedocument",
    "application/vnd.ms-excel",
    "application/msword",
    "application/vnd.ms-powerpoint",
    "audio/",
    "video/"
}

class ResponseLoggerMiddleware(BaseHTTPMiddleware):
    """응답 본문을 로깅하기 위한 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        return response

class LoggableJSONResponse(JSONResponse):
    """로깅 가능한 JSON 응답"""
    def __init__(self, *args, **kwargs):
        self.body_raw = kwargs.get("content")
        super().__init__(*args, **kwargs)

class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP 요청과 응답을 상세하게 로깅하는 미들웨어입니다.
    - 요청 ID, 처리 시간, 상태 코드
    - 요청 파라미터(쿼리, 경로)
    - 요청 헤더(선택적으로 필터링)
    - 요청 본문(JSON만 처리, 크기 제한, 민감 정보 필터링)
    - 응답 본문(JSON만 처리, 크기 제한)
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        exclude_paths: List[str] = None,
        sensitive_fields: Set[str] = None,
        max_body_length: int = 10000,
        log_request_headers: bool = True,
        log_response_headers: bool = False,
        log_request_body: bool = True,
        log_response_body: bool = True,
    ):
        super().__init__(app)
        # 추가 제외 경로 (설정에 있는 패턴 외에 추가로 제외할 경로)
        self.additional_exclude_paths = exclude_paths or []
        
        # YAML 설정에서 제외 패턴 가져오기
        self.exclude_patterns = yaml_settings.logging.http.exclude_patterns
        
        logger.info(f"로깅 미들웨어 제외 패턴: {self.exclude_patterns}")
        
        self.sensitive_fields = sensitive_fields or DEFAULT_SENSITIVE_FIELDS
        self.max_body_size = max_body_length  # 내부적으로는 max_body_size로 저장
        self.log_request_headers = log_request_headers
        self.log_response_headers = log_response_headers
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """민감한 정보를 마스킹합니다."""
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if key.lower() in self.sensitive_fields:
                    masked_data[key] = "******"  # 민감 정보 마스킹
                else:
                    # 재귀적으로 하위 객체도 마스킹
                    masked_data[key] = self._mask_sensitive_data(value)
            return masked_data
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        return data
    
    def _truncate_body(self, body: str) -> str:
        """본문이 너무 클 경우 잘라냅니다."""
        if len(body) > self.max_body_size:
            return body[:self.max_body_size] + "... [truncated]"
        return body
    
    def _is_file_request(self, request: Request) -> bool:
        """요청이 파일 업로드 요청인지 확인합니다."""
        content_type = request.headers.get("content-type", "").lower()
        
        # multipart/form-data 요청은 일반적으로 파일 업로드에 사용됨
        if any(content_type.startswith(file_type) for file_type in FILE_CONTENT_TYPES):
            return True
        
        # '/upload', '/file', '/download' 등이 포함된 경로는 파일 관련 요청으로 간주
        if any(keyword in request.url.path.lower() for keyword in ["/upload", "/file", "/download", "/attachment"]):
            return True
            
        return False
    
    def _is_file_response(self, response: Response) -> bool:
        """응답이 파일 다운로드 응답인지 확인합니다."""
        # FileResponse 인스턴스인 경우
        if isinstance(response, FileResponse):
            return True
        
        # Content-Disposition 헤더가 attachment 또는 inline을 포함하는 경우
        content_disposition = response.headers.get("content-disposition", "").lower()
        if "attachment" in content_disposition or "inline" in content_disposition:
            return True
        
        # Content-Type 헤더가 바이너리 또는 미디어 파일을 나타내는 경우
        content_type = response.headers.get("content-type", "").lower()
        if any(content_type.startswith(file_type) for file_type in FILE_CONTENT_TYPES):
            return True
            
        return False
    
    def _get_file_details(self, request: Request, content_type: str) -> Dict[str, Any]:
        """
        파일 업로드 요청에서 파일 정보를 추출합니다.
        실제 파일 내용 대신 파일 메타데이터만 반환합니다.
        """
        file_details = {
            "type": "file_upload",
            "content_type": content_type,
        }
        
        # 파일 이름이 URL에 포함된 경우 추출 시도
        if "/upload/" in request.url.path:
            parts = request.url.path.split("/")
            for part in parts:
                if "." in part:  # 파일 확장자가 있는 경우
                    file_details["filename"] = part
                    break
        
        return file_details
    
    async def _get_request_body(self, request: Request) -> Optional[str]:
        """요청 본문을 가져옵니다. 파일 업로드의 경우 파일 정보만 반환합니다."""
        if not self.log_request_body:
            return None
            
        try:
            content_type = request.headers.get("content-type", "").lower()
            
            # 파일 업로드 요청인 경우
            if self._is_file_request(request):
                file_info = self._get_file_details(request, content_type)
                return json.dumps({"file_upload_info": file_info, "message": "<file content not logged>"})
            
            # 일반 요청인 경우 기존 로직 적용
            body = await request.body()
            if body:
                body_str = body.decode('utf-8')
                
                # 요청 객체의 body를 복원하여 다음 미들웨어에서도 사용할 수 있게 함
                async def receive() -> Message:
                    return {"type": "http.request", "body": body}
                request._receive = receive
                
                # JSON인 경우만 파싱하여 민감 정보 마스킹
                try:
                    json_body = json.loads(body_str)
                    masked_body = self._mask_sensitive_data(json_body)
                    return self._truncate_body(json.dumps(masked_body))
                except json.JSONDecodeError:
                    # JSON이 아닌 경우 원본 텍스트 반환
                    return self._truncate_body(body_str)
        except Exception as e:
            logger.warning(f"요청 본문 로깅 실패: {str(e)}")
        
        return None
    
    def _get_query_params(self, request: Request) -> Dict[str, str]:
        """쿼리 파라미터를 가져와 민감 정보를 마스킹합니다."""
        params = {}
        for key, value in request.query_params.items():
            if key.lower() in self.sensitive_fields:
                params[key] = "******"
            else:
                params[key] = value
        return params
    
    def _get_headers(self, headers: Headers, is_request: bool = True) -> Dict[str, str]:
        """헤더를 가져와 민감 정보를 마스킹합니다."""
        if (is_request and not self.log_request_headers) or (not is_request and not self.log_response_headers):
            return {}
            
        result = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_fields or key.lower() == "authorization":
                result[key] = "******"
            else:
                result[key] = value
        return result
    
    def path_match(self, path: str, pattern: str) -> bool:
        """
        경로와 패턴이 일치하는지 확인
        
        지원하는 패턴:
        - '/*': 정확히 하나의 경로 세그먼트와 매칭 (예: /api/* 는 /api/users와 매칭되지만 /api/users/me나 /api/users/와는 매칭되지 않음)
        - '/**': 0개 이상의 모든 하위 경로와 재귀적으로 매칭 (예: /api/** 는 /api, /api/users, /api/users/me 모두와 매칭)
        
        Args:
            path: 요청 경로
            pattern: 패턴
            
        Returns:
            매칭 여부
        """
        # 패턴에 '/**'가 포함된 경우 (재귀적 매칭)
        if '/**' in pattern:
            # 기본 경로 추출 (/** 이전 부분)
            base_path = pattern.split('/**')[0]
            
            # 기본 경로가 일치하는지 확인
            return path == base_path or path.startswith(base_path + '/')
        
        # 패턴에 '/*'가 포함된 경우 (단일 세그먼트 매칭)
        elif '/*' in pattern:
            # 테스트 케이스에 따라 후행 슬래시('/')가 있는 경로는 /* 패턴과 매칭되지 않아야 함
            # 예: /api/users/는 /api/*와 매칭되지 않음 (후행 슬래시가 있으므로)
            # 주의: 실제 애플리케이션에서는 TrailingSlashMiddleware에 의해 이미 처리되지만,
            # 단위 테스트와 백업 안전장치로 여기에도 로직 유지
            if path != '/' and path.endswith('/'):
                return False
                
            # 패턴과 경로를 세그먼트로 분할
            pattern_segments = pattern.split('/')
            path_segments = path.split('/')
            
            # 빈 문자열 세그먼트 제거 (경로 끝에 '/'가 있는 경우)
            if path_segments and path_segments[-1] == '':
                path_segments.pop()
                
            if pattern_segments and pattern_segments[-1] == '':
                pattern_segments.pop()
            
            # 세그먼트 수가 다르면 매칭되지 않음
            if len(pattern_segments) != len(path_segments):
                return False
            
            # 각 세그먼트 비교
            for i, pattern_seg in enumerate(pattern_segments):
                # 와일드카드(*) 세그먼트는 항상 매칭됨
                if pattern_seg == '*':
                    continue
                # 세그먼트가 다르면 매칭되지 않음
                if pattern_seg != path_segments[i]:
                    return False
            
            # 모든 세그먼트가 매칭됨
            return True
        
        # 정확한 경로 매칭
        else:
            return path == pattern
    
    async def _capture_response_body(self, response: Response) -> Optional[str]:
        """응답 본문을 가져옵니다. 파일 다운로드의 경우 파일 정보만 반환합니다."""
        if not self.log_response_body:
            return None
            
        try:
            # 파일 다운로드 응답인 경우
            if self._is_file_response(response):
                file_info = {
                    "type": "file_download",
                    "content_type": response.headers.get("content-type", "unknown"),
                }
                
                # Content-Disposition 헤더에서 파일명 추출 시도
                content_disposition = response.headers.get("content-disposition", "")
                if content_disposition:
                    import re
                    filename_match = re.search(r'filename="?([^";]+)"?', content_disposition)
                    if filename_match:
                        file_info["filename"] = filename_match.group(1)
                
                return json.dumps({"file_download_info": file_info, "message": "<file content not logged>"})
            
            # LoggableJSONResponse인 경우 직접 본문 접근
            if isinstance(response, LoggableJSONResponse):
                raw_body = response.body_raw
                if raw_body:
                    masked_body = self._mask_sensitive_data(raw_body)
                    return self._truncate_body(json.dumps(masked_body))
            
            # JSONResponse인 경우 본문 파싱 시도
            elif isinstance(response, JSONResponse):
                body = response.body
                if body:
                    body_str = body.decode('utf-8')
                    try:
                        json_body = json.loads(body_str)
                        masked_body = self._mask_sensitive_data(json_body)
                        return self._truncate_body(json.dumps(masked_body))
                    except json.JSONDecodeError:
                        return self._truncate_body(body_str)
        except Exception as e:
            logger.warning(f"응답 본문 로깅 실패: {str(e)}")
        
        return None
    
    def is_path_excluded(self, path: str) -> bool:
        """
        경로가 로깅에서 제외되어야 하는지 확인
        
        Args:
            path: 요청 경로
            
        Returns:
            제외 여부
        """
        # 추가 제외 경로 확인 (정확한 경로 매칭)
        for exclude_path in self.additional_exclude_paths:
            if path.startswith(exclude_path):
                logger.debug(f"추가 제외 경로 매칭: {path} -> {exclude_path}")
                return True
        
        # 설정에 있는 패턴 확인 (커스텀 패턴 매칭)
        for pattern in self.exclude_patterns:
            if self.path_match(path, pattern):
                logger.debug(f"제외 패턴 매칭: {path} -> {pattern}")
                return True
                
        return False
    
    async def dispatch(self, request: Request, call_next):
        """요청과 응답을 처리하면서 로깅을 수행합니다."""
        # 특정 경로 제외 (상태 확인 엔드포인트 등)
        path = request.url.path
        if self.is_path_excluded(path):
            return await call_next(request)
        
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        
        # 요청 시작 시간
        start_time = time.time()
        
        # 요청 본문 가져오기 (미리 읽어둠)
        request_body = await self._get_request_body(request)
        
        # 로깅 컨텍스트 초기화
        logging_context = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown",
            "query_params": self._get_query_params(request),
            "path_params": dict(request.path_params),
            "headers": self._get_headers(request.headers)
        }
        
        # 요청 본문 추가 (있는 경우만)
        if request_body:
            logging_context["request_body"] = request_body
        
        # 요청 로깅
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra=logging_context
        )
        
        try:
            # 요청 처리
            response = await call_next(request)
            
            # 응답 시간 계산
            process_time = time.time() - start_time
            
            # 응답 본문 가져오기
            response_body = await self._capture_response_body(response)
            
            # 로깅 컨텍스트 업데이트
            logging_context.update({
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2)
            })
            
            # 응답 헤더 추가 (설정된 경우만)
            if self.log_response_headers:
                logging_context["response_headers"] = self._get_headers(response.headers, is_request=False)
            
            # 응답 본문 추가 (있는 경우만)
            if response_body:
                logging_context["response_body"] = response_body
            
            # 응답 로깅
            logger.info(
                f"Request completed: {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {round(process_time * 1000, 2)}ms",
                extra=logging_context
            )
            
            # 요청 ID를 응답 헤더에 추가
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # 예외 발생 시 로깅
            process_time = time.time() - start_time
            logging_context.update({
                "status_code": 500,
                "process_time_ms": round(process_time * 1000, 2),
                "error": str(e)
            })
            
            logger.exception(
                f"Request failed: {request.method} {request.url.path} - "
                f"Error: {str(e)} - "
                f"Time: {round(process_time * 1000, 2)}ms",
                extra=logging_context
            )
            
            # 예외 다시 발생시켜 FastAPI의 예외 처리기가 처리하도록 함
            raise

# 기존 RequestLoggingMiddleware는 새로운 RequestResponseLoggingMiddleware로 대체합니다
RequestLoggingMiddleware = RequestResponseLoggingMiddleware 