"""
시스템 상태를 추적하고 준비 상태를 확인하는 모듈입니다.
"""
import logging
import time
from typing import Dict, Optional, List, Callable
import asyncio

logger = logging.getLogger(__name__)

class SystemStatus:
    """
    시스템의 다양한 컴포넌트 상태를 추적하는 클래스입니다.
    """
    def __init__(self):
        self.components: Dict[str, bool] = {
            "database": False,
            "cache": False,
            "local_cache": False,
            "external_services": False
        }
        self.initialized: bool = False
        self.startup_time: Optional[float] = None
        self.last_check_time: Optional[float] = None
        self.errors: List[str] = []

    def reset(self):
        """상태를 초기화합니다."""
        self.__init__()

    def all_systems_ready(self) -> bool:
        """모든 시스템이 준비되었는지 확인합니다."""
        return all(self.components.values()) and self.initialized

    def get_status_report(self) -> Dict:
        """현재 상태에 대한 상세 보고서를 반환합니다."""
        return {
            "ready": self.all_systems_ready(),
            "initialized": self.initialized,
            "components": self.components,
            "startup_time": self.startup_time,
            "last_check_time": self.last_check_time,
            "uptime_seconds": time.time() - self.startup_time if self.startup_time else None,
            "errors": self.errors if self.errors else None
        }


# 시스템 상태 싱글톤 인스턴스
system_status = SystemStatus()


async def check_database_connection() -> bool:
    """
    데이터베이스 연결을 확인합니다.
    실제 구현에서는 DB 연결 풀에 대한 검증을 수행합니다.
    """
    try:
        # 예시: 실제로는 데이터베이스 커넥션 풀에서 연결을 가져와 쿼리 실행
        logger.info("데이터베이스 연결 확인 중...")
        
        # 실제 데이터베이스 연결 코드를 여기에 구현
        # 예: async with db_pool.acquire() as conn:
        #        await conn.execute("SELECT 1")
        
        # 시뮬레이션을 위한 지연
        await asyncio.sleep(0.5)
        return True
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {str(e)}")
        system_status.errors.append(f"Database error: {str(e)}")
        return False


async def check_cache_connection() -> bool:
    """
    Redis 또는 memcached와 같은 외부 캐시 연결을 확인합니다.
    """
    try:
        logger.info("캐시 서버 연결 확인 중...")
        
        # 실제 캐시 연결 코드를 여기에 구현
        # 예: await redis.ping()
        
        # 시뮬레이션을 위한 지연
        await asyncio.sleep(0.3)
        return True
    except Exception as e:
        logger.error(f"캐시 연결 실패: {str(e)}")
        system_status.errors.append(f"Cache error: {str(e)}")
        return False


async def initialize_local_cache() -> bool:
    """
    애플리케이션의 로컬 캐시를 초기화합니다.
    (예: 자주 사용되는 설정 값이나 참조 데이터)
    """
    try:
        logger.info("로컬 캐시 초기화 중...")
        
        # 실제 로컬 캐시 초기화 코드를 여기에 구현
        # 예: await load_config_to_memory()
        
        # 시뮬레이션을 위한 지연
        await asyncio.sleep(0.2)
        return True
    except Exception as e:
        logger.error(f"로컬 캐시 초기화 실패: {str(e)}")
        system_status.errors.append(f"Local cache error: {str(e)}")
        return False


async def check_external_services() -> bool:
    """
    외부 API 또는 서비스 연결을 확인합니다.
    """
    try:
        logger.info("외부 서비스 연결 확인 중...")
        
        # 실제 외부 서비스 확인 코드를 여기에 구현
        # 예: async with httpx.AsyncClient() as client:
        #        response = await client.get("https://external-api.example.com/health")
        
        # 시뮬레이션을 위한 지연
        await asyncio.sleep(0.4)
        return True
    except Exception as e:
        logger.error(f"외부 서비스 확인 실패: {str(e)}")
        system_status.errors.append(f"External service error: {str(e)}")
        return False


async def warmup() -> bool:
    """
    애플리케이션 시작 시 모든 필요한 서비스 및 연결을 확인하고 초기화합니다.
    이 함수는 애플리케이션 시작 시 호출되어야 합니다.
    """
    logger.info("시스템 웜업 시작...")
    system_status.reset()
    system_status.startup_time = time.time()
    system_status.last_check_time = time.time()
    
    # 필요한 모든 컴포넌트 확인
    system_status.components["database"] = await check_database_connection()
    system_status.components["cache"] = await check_cache_connection()
    system_status.components["local_cache"] = await initialize_local_cache()
    system_status.components["external_services"] = await check_external_services()
    
    # 최종 초기화 상태 설정
    system_status.initialized = True
    system_status.last_check_time = time.time()
    
    ready = system_status.all_systems_ready()
    if ready:
        logger.info("시스템 웜업 완료: 모든 컴포넌트 준비됨")
    else:
        logger.warning(f"시스템 웜업 완료: 일부 컴포넌트 준비 안 됨 - {system_status.get_status_report()}")
    
    return ready


async def check_system_health() -> Dict:
    """
    모든 시스템 구성 요소의 현재 상태를 확인하고 보고서를 반환합니다.
    이 함수는 정기적인 상태 확인 또는 readiness 엔드포인트에서 호출할 수 있습니다.
    """
    system_status.last_check_time = time.time()
    
    # 이미 초기화되었다면 빠른 상태 보고
    if system_status.initialized:
        # 필요에 따라 여기에 일부 컴포넌트의 상태를 다시 확인할 수 있습니다
        return system_status.get_status_report()
    
    # 아직 초기화되지 않았다면 웜업 수행
    await warmup()
    return system_status.get_status_report() 