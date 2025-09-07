#!/usr/bin/env python3
"""
인기 뉴스 관련 API 엔드포인트

인기 뉴스 조회 및 분석 기능을 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ...repo.db import SessionLocal, get_db
from ...services.popular_news_analyzer import PopularNewsAnalyzer
from ...workers.tasks import process_popular_news_task

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/popular-news", summary="인기 뉴스 목록 조회")
def get_popular_news(
    limit: int = Query(10, ge=1, le=50, description="조회할 개수"),
    hours: int = Query(24, ge=1, le=168, description="최근 몇 시간 내의 뉴스"),
    db: SessionLocal = Depends(get_db)
) -> Dict[str, Any]:
    """
    인기 뉴스 목록을 조회합니다.
    
    Parameters
    ----------
    limit : int
        조회할 개수
    hours : int
        최근 몇 시간 내의 뉴스
        
    Returns
    -------
    Dict[str, Any]
        인기 뉴스 목록과 메타데이터
    """
    try:
        analyzer = PopularNewsAnalyzer(db)
        popular_news = analyzer.get_popular_news(limit, hours)
        
        # 응답 데이터 구성
        news_list = []
        for content in popular_news:
            popularity_score = analyzer.analyze_popularity_score(content)
            
            news_list.append({
                "id": content.id,
                "title": content.title,
                "url": content.url,
                "source": content.source,
                "published_at": content.published_at.isoformat() if content.published_at else None,
                "lang": content.lang,
                "popularity_score": round(popularity_score, 2),
                "has_ai_summary": content.ai_summary_status == "completed",
                "ai_summarized_at": content.ai_summarized_at.isoformat() if content.ai_summarized_at else None
            })
        
        return {
            "news": news_list,
            "total": len(news_list),
            "limit": limit,
            "hours": hours,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"인기 뉴스 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"인기 뉴스 조회 실패: {str(e)}")


@router.get("/popular-news/{news_id}/summary", summary="인기 뉴스 AI 요약 조회")
def get_popular_news_summary(
    news_id: int,
    db: SessionLocal = Depends(get_db)
) -> Dict[str, Any]:
    """
    특정 인기 뉴스의 AI 요약을 조회합니다.
    
    Parameters
    ----------
    news_id : int
        뉴스 ID
        
    Returns
    -------
    Dict[str, Any]
        AI 요약 정보
    """
    try:
        from ...models.content import Content, AICache
        
        # 뉴스 조회
        content = db.query(Content).filter(Content.id == news_id).first()
        if not content:
            raise HTTPException(status_code=404, detail="뉴스를 찾을 수 없습니다")
        
        # AI 요약 조회
        ai_cache = db.query(AICache).filter(
            AICache.content_hash == content.hash,
            AICache.model_version == "gpt-3.5-turbo"
        ).first()
        
        if not ai_cache:
            return {
                "news_id": news_id,
                "title": content.title,
                "has_summary": False,
                "message": "AI 요약이 아직 생성되지 않았습니다."
            }
        
        return {
            "news_id": news_id,
            "title": content.title,
            "has_summary": True,
            "summary_bullets": ai_cache.summary_bullets,
            "tags": ai_cache.tags,
            "insight": ai_cache.insight,
            "generated_at": ai_cache.created_at.isoformat(),
            "tokens_used": ai_cache.tokens_used,
            "cost": ai_cache.cost
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인기 뉴스 요약 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"인기 뉴스 요약 조회 실패: {str(e)}")


@router.post("/popular-news/process", summary="인기 뉴스 AI 요약 생성")
def process_popular_news(
    limit: int = Query(10, ge=1, le=20, description="처리할 뉴스 개수"),
    db: SessionLocal = Depends(get_db)
) -> Dict[str, Any]:
    """
    인기 뉴스 10개를 선별하고 AI 요약을 생성합니다.
    
    Parameters
    ----------
    limit : int
        처리할 뉴스 개수
        
    Returns
    -------
    Dict[str, Any]
        처리 결과
    """
    try:
        # 비동기 태스크 실행
        task = process_popular_news_task.delay(limit)
        
        return {
            "status": "started",
            "task_id": task.id,
            "message": f"인기 뉴스 {limit}개 AI 요약 처리가 시작되었습니다.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"인기 뉴스 처리 시작 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"인기 뉴스 처리 시작 실패: {str(e)}")


@router.get("/popular-news/stats", summary="인기 뉴스 통계")
def get_popular_news_stats(
    db: SessionLocal = Depends(get_db)
) -> Dict[str, Any]:
    """
    인기 뉴스 관련 통계를 조회합니다.
    
    Returns
    -------
    Dict[str, Any]
        인기 뉴스 통계
    """
    try:
        from ...models.content import Content, AICache
        from sqlalchemy import func, and_
        from datetime import datetime, timedelta
        
        # 최근 24시간 내 뉴스 수
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        total_news_24h = db.query(Content).filter(
            and_(
                Content.published_at >= cutoff_time,
                Content.is_active == True
            )
        ).count()
        
        # AI 요약 완료된 뉴스 수
        ai_summarized_24h = db.query(Content).filter(
            and_(
                Content.published_at >= cutoff_time,
                Content.is_active == True,
                Content.ai_summary_status == "completed"
            )
        ).count()
        
        # 인기 뉴스 분석기로 최신 인기도 점수 계산
        analyzer = PopularNewsAnalyzer(db)
        popular_news = analyzer.get_popular_news(10, 24)
        
        avg_popularity_score = 0
        if popular_news:
            scores = [analyzer.analyze_popularity_score(news) for news in popular_news]
            avg_popularity_score = sum(scores) / len(scores)
        
        return {
            "total_news_24h": total_news_24h,
            "ai_summarized_24h": ai_summarized_24h,
            "ai_summary_rate_24h": round((ai_summarized_24h / total_news_24h * 100) if total_news_24h > 0 else 0, 2),
            "popular_news_count": len(popular_news),
            "avg_popularity_score": round(avg_popularity_score, 2),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"인기 뉴스 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"인기 뉴스 통계 조회 실패: {str(e)}")
