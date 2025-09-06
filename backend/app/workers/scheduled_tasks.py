#!/usr/bin/env python3
"""
스케줄링된 RSS 수집 태스크

Celery Beat을 사용하여 정기적으로 RSS 피드를 자동 수집합니다.
"""

from celery import shared_task
from datetime import datetime
from typing import Dict, Any, Optional
import logging

# from ..services.ingest.multi_rss import ingest_multiple_feeds  # 순환 import 방지

# 로깅 설정
logger = logging.getLogger(__name__)


@shared_task(bind=True, name="scheduled_rss_ingestion")
def scheduled_rss_ingestion(self, feed_groups: Optional[list] = None) -> Dict[str, Any]:
    """
    스케줄링된 RSS 피드 수집 태스크
    
    Parameters
    ----------
    feed_groups : Optional[list], optional
        수집할 피드 그룹 목록. None이면 모든 그룹 수집
        
    Returns
    -------
    Dict[str, Any]
        수집 결과 통계
    """
    task_id = self.request.id
    logger.info(f"스케줄링된 RSS 수집 시작 - Task ID: {task_id}")
    
    try:
        # 순환 import 방지를 위해 함수 내에서 import
        from ..services.ingest.multi_rss import ingest_multiple_feeds
        # RSS 피드 수집 실행
        result = ingest_multiple_feeds(feed_groups)
        
        logger.info(f"RSS 수집 완료 - Task ID: {task_id}, 수집된 기사: {result['total_saved']}개")
        
        return {
            "task_id": task_id,
            "status": "success",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"RSS 수집 실패 - Task ID: {task_id}, 에러: {str(e)}")
        
        return {
            "task_id": task_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="scheduled_korean_news_ingestion")
def scheduled_korean_news_ingestion(self) -> Dict[str, Any]:
    """
    한국 뉴스 RSS 피드 수집 (매시간)
    
    Returns
    -------
    Dict[str, Any]
        수집 결과 통계
    """
    logger.info("한국 뉴스 RSS 수집 시작")
    return scheduled_rss_ingestion.delay(['korean']).get()


@shared_task(bind=True, name="scheduled_us_news_ingestion")
def scheduled_us_news_ingestion(self) -> Dict[str, Any]:
    """
    미국 뉴스 RSS 피드 수집 (30분마다)
    
    Returns
    -------
    Dict[str, Any]
        수집 결과 통계
    """
    logger.info("미국 뉴스 RSS 수집 시작")
    return scheduled_rss_ingestion.delay(['us_news']).get()


@shared_task(bind=True, name="scheduled_all_news_ingestion")
def scheduled_all_news_ingestion(self) -> Dict[str, Any]:
    """
    모든 뉴스 RSS 피드 수집 (매일 새벽 2시)
    
    Returns
    -------
    Dict[str, Any]
        수집 결과 통계
    """
    logger.info("전체 뉴스 RSS 수집 시작")
    return scheduled_rss_ingestion.delay().get()


@shared_task(bind=True, name="health_check")
def health_check(self) -> Dict[str, Any]:
    """
    시스템 상태 확인 태스크 (5분마다)
    
    Returns
    -------
    Dict[str, Any]
        시스템 상태 정보
    """
    try:
        from ..repo.db import engine
        from ..repo.content import ContentRepo
        from ..repo.db import SessionLocal
        
        # 데이터베이스 연결 확인
        db = SessionLocal()
        repo = ContentRepo(db)
        
        # 최근 콘텐츠 수 확인
        recent_contents = repo.list_contents(tags=None, limit=10, offset=0)
        
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "recent_contents": len(recent_contents),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"헬스 체크 실패: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
