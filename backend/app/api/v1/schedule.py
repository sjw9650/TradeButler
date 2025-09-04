#!/usr/bin/env python3
"""
스케줄링 관리 API

RSS 수집 스케줄을 관리하는 API 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime
import logging

from ...workers.scheduled_tasks import (
    scheduled_rss_ingestion,
    scheduled_korean_news_ingestion,
    scheduled_us_news_ingestion,
    scheduled_all_news_ingestion,
    health_check
)
from ...workers.beat_config import BEAT_SCHEDULE, SCHEDULE_DESCRIPTIONS

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/schedules", summary="스케줄 목록 조회")
def get_schedules() -> Dict[str, Any]:
    """
    현재 설정된 스케줄 목록을 조회합니다.
    
    Returns
    -------
    Dict[str, Any]
        스케줄 목록과 설명
    """
    schedules = []
    
    for schedule_name, schedule_config in BEAT_SCHEDULE.items():
        schedules.append({
            "name": schedule_name,
            "description": SCHEDULE_DESCRIPTIONS.get(schedule_name, "설명 없음"),
            "task": schedule_config["task"],
            "schedule": str(schedule_config["schedule"]),
            "queue": schedule_config["options"].get("queue", "default"),
            "priority": schedule_config["options"].get("priority", 5)
        })
    
    return {
        "schedules": schedules,
        "total": len(schedules),
        "timezone": "Asia/Seoul"
    }


@router.post("/trigger/korean", summary="한국 뉴스 수집 트리거")
def trigger_korean_news() -> Dict[str, Any]:
    """
    한국 뉴스 RSS 수집을 즉시 실행합니다.
    
    Returns
    -------
    Dict[str, Any]
        실행 결과
    """
    try:
        task = scheduled_korean_news_ingestion.delay()
        
        return {
            "status": "triggered",
            "task_id": task.id,
            "message": "한국 뉴스 RSS 수집이 시작되었습니다.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"한국 뉴스 수집 트리거 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"수집 시작 실패: {str(e)}")


@router.post("/trigger/us", summary="미국 뉴스 수집 트리거")
def trigger_us_news() -> Dict[str, Any]:
    """
    미국 뉴스 RSS 수집을 즉시 실행합니다.
    
    Returns
    -------
    Dict[str, Any]
        실행 결과
    """
    try:
        task = scheduled_us_news_ingestion.delay()
        
        return {
            "status": "triggered",
            "task_id": task.id,
            "message": "미국 뉴스 RSS 수집이 시작되었습니다.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"미국 뉴스 수집 트리거 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"수집 시작 실패: {str(e)}")


@router.post("/trigger/all", summary="전체 뉴스 수집 트리거")
def trigger_all_news() -> Dict[str, Any]:
    """
    모든 뉴스 RSS 수집을 즉시 실행합니다.
    
    Returns
    -------
    Dict[str, Any]
        실행 결과
    """
    try:
        task = scheduled_all_news_ingestion.delay()
        
        return {
            "status": "triggered",
            "task_id": task.id,
            "message": "전체 뉴스 RSS 수집이 시작되었습니다.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"전체 뉴스 수집 트리거 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"수집 시작 실패: {str(e)}")


@router.post("/trigger/custom", summary="커스텀 수집 트리거")
def trigger_custom_ingestion(feed_groups: List[str]) -> Dict[str, Any]:
    """
    지정된 피드 그룹의 RSS 수집을 즉시 실행합니다.
    
    Parameters
    ----------
    feed_groups : List[str]
        수집할 피드 그룹 목록 (korean, us_news)
        
    Returns
    -------
    Dict[str, Any]
        실행 결과
    """
    try:
        task = scheduled_rss_ingestion.delay(feed_groups)
        
        return {
            "status": "triggered",
            "task_id": task.id,
            "feed_groups": feed_groups,
            "message": f"피드 그룹 {feed_groups}의 RSS 수집이 시작되었습니다.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"커스텀 수집 트리거 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"수집 시작 실패: {str(e)}")


@router.get("/health", summary="시스템 상태 확인")
def check_health() -> Dict[str, Any]:
    """
    시스템 상태를 확인합니다.
    
    Returns
    -------
    Dict[str, Any]
        시스템 상태 정보
    """
    try:
        task = health_check.delay()
        result = task.get(timeout=10)
        
        return result
    except Exception as e:
        logger.error(f"헬스 체크 실패: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/status", summary="스케줄러 상태 확인")
def get_scheduler_status() -> Dict[str, Any]:
    """
    Celery Beat 스케줄러 상태를 확인합니다.
    
    Returns
    -------
    Dict[str, Any]
        스케줄러 상태 정보
    """
    try:
        from ...workers.celery_app import celery
        
        # Celery Beat 상태 확인
        inspect = celery.control.inspect()
        active_queues = inspect.active_queues()
        scheduled = inspect.scheduled()
        
        return {
            "status": "running",
            "active_queues": active_queues,
            "scheduled_tasks": scheduled,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"스케줄러 상태 확인 실패: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
