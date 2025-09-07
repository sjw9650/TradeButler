#!/usr/bin/env python3
"""
선택적 AI 파이프라인 API 엔드포인트

팔로잉 기업 관련 뉴스만 자동 요약하고, 나머지는 온디맨드로 처리
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ...repo.db import SessionLocal
from ...services.selective_ai_pipeline import SelectiveAIPipeline
from ...services.company_matcher import CompanyMatcher

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard/{user_id}", summary="사용자 대시보드 데이터 조회")
def get_user_dashboard(user_id: str) -> Dict[str, Any]:
    """
    사용자의 선택적 AI 대시보드 데이터를 조회합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
        
    Returns
    -------
    Dict[str, Any]
        대시보드 데이터
    """
    try:
        db = SessionLocal()
        pipeline = SelectiveAIPipeline(db)
        
        dashboard_data = pipeline.get_user_dashboard_data(user_id)
        
        db.close()
        return dashboard_data
        
    except Exception as e:
        logger.error(f"대시보드 데이터 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"대시보드 데이터 조회 실패: {str(e)}")


@router.get("/priority-content/{user_id}", summary="우선순위 콘텐츠 조회")
def get_priority_content(
    user_id: str,
    limit: int = Query(10, ge=1, le=50, description="조회할 개수")
) -> Dict[str, Any]:
    """
    사용자에게 우선순위가 높은 콘텐츠를 조회합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    limit : int
        조회할 개수
        
    Returns
    -------
    Dict[str, Any]
        우선순위 콘텐츠 목록
    """
    try:
        db = SessionLocal()
        matcher = CompanyMatcher(db)
        
        priority_content = matcher.get_priority_content(user_id, limit)
        
        db.close()
        
        return {
            "user_id": user_id,
            "priority_content": priority_content,
            "total": len(priority_content),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"우선순위 콘텐츠 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"우선순위 콘텐츠 조회 실패: {str(e)}")


@router.post("/process-content/{content_id}", summary="콘텐츠 선택적 AI 처리")
def process_content(
    content_id: int,
    user_id: str = Query("default_user", description="사용자 ID")
) -> Dict[str, Any]:
    """
    특정 콘텐츠를 선택적 AI 파이프라인으로 처리합니다.
    
    Parameters
    ----------
    content_id : int
        콘텐츠 ID
    user_id : str
        사용자 ID
        
    Returns
    -------
    Dict[str, Any]
        처리 결과
    """
    try:
        db = SessionLocal()
        pipeline = SelectiveAIPipeline(db)
        
        result = pipeline.process_new_content(content_id, user_id)
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"콘텐츠 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"콘텐츠 처리 실패: {str(e)}")


@router.post("/process-batch", summary="배치 선택적 AI 처리")
def process_batch(
    user_id: str = Query("default_user", description="사용자 ID"),
    limit: int = Query(50, ge=1, le=100, description="처리할 최대 개수")
) -> Dict[str, Any]:
    """
    배치로 콘텐츠를 선택적 AI 파이프라인으로 처리합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    limit : int
        처리할 최대 개수
        
    Returns
    -------
    Dict[str, Any]
        배치 처리 결과
    """
    try:
        db = SessionLocal()
        pipeline = SelectiveAIPipeline(db)
        
        result = pipeline.process_batch_content(user_id, limit)
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"배치 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"배치 처리 실패: {str(e)}")


@router.post("/on-demand-summary/{content_id}", summary="온디맨드 요약 실행")
def trigger_on_demand_summary(
    content_id: int,
    user_id: str = Query("default_user", description="사용자 ID")
) -> Dict[str, Any]:
    """
    온디맨드 요약을 실행합니다.
    
    Parameters
    ----------
    content_id : int
        콘텐츠 ID
    user_id : str
        사용자 ID
        
    Returns
    -------
    Dict[str, Any]
        요약 결과
    """
    try:
        db = SessionLocal()
        pipeline = SelectiveAIPipeline(db)
        
        result = pipeline.trigger_on_demand_summary(content_id, user_id)
        
        db.close()
        return result
        
    except Exception as e:
        logger.error(f"온디맨드 요약 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"온디맨드 요약 실패: {str(e)}")


@router.get("/match-analysis/{content_id}", summary="콘텐츠 매칭 분석")
def analyze_content_matching(
    content_id: int,
    user_id: str = Query("default_user", description="사용자 ID")
) -> Dict[str, Any]:
    """
    콘텐츠의 기업 매칭 분석을 조회합니다.
    
    Parameters
    ----------
    content_id : int
        콘텐츠 ID
    user_id : str
        사용자 ID
        
    Returns
    -------
    Dict[str, Any]
        매칭 분석 결과
    """
    try:
        db = SessionLocal()
        matcher = CompanyMatcher(db)
        
        match_result = matcher.should_auto_summarize(content_id, user_id)
        
        db.close()
        return match_result
        
    except Exception as e:
        logger.error(f"매칭 분석 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"매칭 분석 실패: {str(e)}")


@router.get("/stats/{user_id}", summary="사용자 통계 조회")
def get_user_stats(user_id: str) -> Dict[str, Any]:
    """
    사용자의 선택적 AI 통계를 조회합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
        
    Returns
    -------
    Dict[str, Any]
        사용자 통계
    """
    try:
        db = SessionLocal()
        matcher = CompanyMatcher(db)
        
        stats = matcher.get_user_summary_stats(user_id)
        
        db.close()
        return stats
        
    except Exception as e:
        logger.error(f"사용자 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 통계 조회 실패: {str(e)}")


@router.get("/on-demand-content", summary="온디맨드 가능 콘텐츠 조회")
def get_on_demand_content(
    user_id: str = Query("default_user", description="사용자 ID"),
    limit: int = Query(20, ge=1, le=100, description="조회할 개수"),
    offset: int = Query(0, ge=0, description="오프셋")
) -> Dict[str, Any]:
    """
    온디맨드 요약이 가능한 콘텐츠를 조회합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    limit : int
        조회할 개수
    offset : int
        오프셋
        
    Returns
    -------
    Dict[str, Any]
        온디맨드 콘텐츠 목록
    """
    try:
        from ...models.content import Content
        
        db = SessionLocal()
        
        # 온디맨드 가능한 콘텐츠 조회
        contents = db.query(Content).filter(
            Content.tags.contains(["on_demand_available"])
        ).order_by(Content.published_at.desc()).offset(offset).limit(limit).all()
        
        total = db.query(Content).filter(
            Content.tags.contains(["on_demand_available"])
        ).count()
        
        on_demand_content = []
        for content in contents:
            on_demand_content.append({
                "id": content.id,
                "title": content.title,
                "author": content.author,
                "url": content.url,
                "source": content.source,
                "published_at": content.published_at.isoformat() if content.published_at else None,
                "tags": content.tags,
                "lang": content.lang
            })
        
        db.close()
        
        return {
            "user_id": user_id,
            "on_demand_content": on_demand_content,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"온디맨드 콘텐츠 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"온디맨드 콘텐츠 조회 실패: {str(e)}")
