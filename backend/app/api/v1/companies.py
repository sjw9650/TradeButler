#!/usr/bin/env python3
"""
기업 관련 API 엔드포인트

기업 추출, 팔로잉, 분석 기능을 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ...repo.db import SessionLocal
from ...repo.company import CompanyRepo
from ...models.company import Company, UserFollowing, CompanyMention
from ...services.company_extractor import process_all_pending_companies
from ...workers.company_tasks import (
    process_all_pending_companies_task,
    # summarize_following_companies_task,  # TODO: 구현 예정
    update_company_statistics_task
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/companies", summary="기업 목록 조회")
def get_companies(
    limit: int = Query(20, ge=1, le=100, description="조회할 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    search: Optional[str] = Query(None, description="기업명 검색"),
    industry: Optional[str] = Query(None, description="업종 필터"),
    sort_by: str = Query("mentions", description="정렬 기준 (mentions/name/created)")
) -> Dict[str, Any]:
    """
    기업 목록을 조회합니다.
    
    Parameters
    ----------
    limit : int
        조회할 개수
    offset : int
        오프셋
    search : Optional[str]
        기업명 검색
    industry : Optional[str]
        업종 필터
    sort_by : str
        정렬 기준
        
    Returns
    -------
    Dict[str, Any]
        기업 목록과 메타데이터
    """
    try:
        db = SessionLocal()
        repo = CompanyRepo(db)
        
        companies = repo.list_companies(
            limit=limit,
            offset=offset,
            search=search,
            industry=industry,
            sort_by=sort_by
        )
        
        total = repo.count_companies(search=search, industry=industry)
        
        # 응답 데이터 구성
        company_list = []
        for company in companies:
            company_list.append({
                "id": company.id,
                "name": company.name,
                "display_name": company.display_name,
                "industry": company.industry,
                "stock_symbol": company.stock_symbol,
                "country": company.country,
                "total_mentions": company.total_mentions,
                "last_mentioned_at": company.last_mentioned_at.isoformat() if company.last_mentioned_at else None,
                "confidence_score": company.confidence_score,
                "is_active": company.is_active,
                "created_at": company.created_at.isoformat()
            })
        
        db.close()
        
        return {
            "companies": company_list,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
        
    except Exception as e:
        logger.error(f"기업 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기업 목록 조회 실패: {str(e)}")


@router.get("/companies/{company_id}", summary="기업 상세 정보 조회")
def get_company(company_id: int) -> Dict[str, Any]:
    """
    특정 기업의 상세 정보를 조회합니다.
    
    Parameters
    ----------
    company_id : int
        기업 ID
        
    Returns
    -------
    Dict[str, Any]
        기업 상세 정보
    """
    try:
        db = SessionLocal()
        repo = CompanyRepo(db)
        
        company = repo.get_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="기업을 찾을 수 없습니다")
        
        # 최근 언급 조회
        recent_mentions = repo.get_recent_mentions(company_id, limit=10)
        
        # 감정 분석 통계
        sentiment_stats = repo.get_sentiment_stats(company_id)
        
        db.close()
        
        return {
            "id": company.id,
            "name": company.name,
            "display_name": company.display_name,
            "industry": company.industry,
            "market_cap": company.market_cap,
            "stock_symbol": company.stock_symbol,
            "country": company.country,
            "website": company.website,
            "description": company.description,
            "aliases": company.aliases,
            "keywords": company.keywords,
            "confidence_score": company.confidence_score,
            "total_mentions": company.total_mentions,
            "last_mentioned_at": company.last_mentioned_at.isoformat() if company.last_mentioned_at else None,
            "is_active": company.is_active,
            "created_at": company.created_at.isoformat(),
            "updated_at": company.updated_at.isoformat(),
            "recent_mentions": recent_mentions,
            "sentiment_stats": sentiment_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기업 상세 조회 실패: {str(e)}")


@router.get("/companies/{company_id}/news", summary="기업 관련 뉴스 조회")
def get_company_news(
    company_id: int,
    limit: int = Query(20, ge=1, le=100, description="조회할 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    sentiment: Optional[str] = Query(None, description="감정 필터 (positive/negative/neutral)")
) -> Dict[str, Any]:
    """
    특정 기업과 관련된 뉴스를 조회합니다.
    
    Parameters
    ----------
    company_id : int
        기업 ID
    limit : int
        조회할 개수
    offset : int
        오프셋
    sentiment : Optional[str]
        감정 필터
        
    Returns
    -------
    Dict[str, Any]
        기업 관련 뉴스 목록
    """
    try:
        db = SessionLocal()
        repo = CompanyRepo(db)
        
        news = repo.get_company_news(
            company_id=company_id,
            limit=limit,
            offset=offset,
            sentiment=sentiment
        )
        
        total = repo.count_company_news(company_id, sentiment=sentiment)
        
        db.close()
        
        return {
            "company_id": company_id,
            "news": news,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
        
    except Exception as e:
        logger.error(f"기업 뉴스 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기업 뉴스 조회 실패: {str(e)}")


@router.post("/companies/{company_id}/follow", summary="기업 팔로잉")
def follow_company(
    company_id: int,
    user_id: str = Query(..., description="사용자 ID"),
    priority: int = Query(1, ge=1, le=5, description="우선순위 (1-5)"),
    notification_enabled: bool = Query(True, description="알림 활성화"),
    auto_summarize: bool = Query(True, description="자동 요약 활성화")
) -> Dict[str, Any]:
    """
    기업을 팔로잉합니다.
    
    Parameters
    ----------
    company_id : int
        기업 ID
    user_id : str
        사용자 ID
    priority : int
        우선순위
    notification_enabled : bool
        알림 활성화
    auto_summarize : bool
        자동 요약 활성화
        
    Returns
    -------
    Dict[str, Any]
        팔로잉 결과
    """
    try:
        db = SessionLocal()
        repo = CompanyRepo(db)
        
        # 기업 존재 확인
        company = repo.get_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="기업을 찾을 수 없습니다")
        
        # 이미 팔로잉 중인지 확인
        existing_following = repo.get_user_following(user_id, company_id)
        if existing_following:
            raise HTTPException(status_code=400, detail="이미 팔로잉 중인 기업입니다")
        
        # 팔로잉 생성
        following = repo.create_user_following(
            user_id=user_id,
            company_id=company_id,
            priority=priority,
            notification_enabled=notification_enabled,
            auto_summarize=auto_summarize
        )
        
        db.close()
        
        return {
            "status": "success",
            "message": f"{company.name}을(를) 팔로잉했습니다",
            "following_id": following.id,
            "company_name": company.name,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 팔로잉 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기업 팔로잉 실패: {str(e)}")


@router.delete("/companies/{company_id}/unfollow", summary="기업 언팔로잉")
def unfollow_company(
    company_id: int,
    user_id: str = Query(..., description="사용자 ID")
) -> Dict[str, Any]:
    """
    기업 팔로잉을 취소합니다.
    
    Parameters
    ----------
    company_id : int
        기업 ID
    user_id : str
        사용자 ID
        
    Returns
    -------
    Dict[str, Any]
        언팔로잉 결과
    """
    try:
        db = SessionLocal()
        repo = CompanyRepo(db)
        
        # 팔로잉 확인
        following = repo.get_user_following(user_id, company_id)
        if not following:
            raise HTTPException(status_code=404, detail="팔로잉 중인 기업이 아닙니다")
        
        # 팔로잉 삭제
        repo.delete_user_following(following.id)
        
        db.close()
        
        return {
            "status": "success",
            "message": "팔로잉을 취소했습니다",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 언팔로잉 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기업 언팔로잉 실패: {str(e)}")


@router.get("/users/{user_id}/following", summary="사용자 팔로잉 기업 목록")
def get_user_following(
    user_id: str,
    limit: int = Query(20, ge=1, le=100, description="조회할 개수"),
    offset: int = Query(0, ge=0, description="오프셋")
) -> Dict[str, Any]:
    """
    사용자가 팔로잉하는 기업 목록을 조회합니다.
    
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
        팔로잉 기업 목록
    """
    try:
        db = SessionLocal()
        repo = CompanyRepo(db)
        
        following = repo.get_user_following_list(user_id, limit=limit, offset=offset)
        total = repo.count_user_following(user_id)
        
        db.close()
        
        return {
            "user_id": user_id,
            "following": following,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
        
    except Exception as e:
        logger.error(f"팔로잉 기업 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"팔로잉 기업 목록 조회 실패: {str(e)}")


@router.post("/companies/extract", summary="기업 추출 실행")
def trigger_company_extraction() -> Dict[str, Any]:
    """
    수집된 뉴스에서 기업명 추출을 실행합니다.
    
    Returns
    -------
    Dict[str, Any]
        추출 실행 결과
    """
    try:
        # 비동기 태스크 실행
        task = process_all_pending_companies_task.delay()
        
        return {
            "status": "queued",
            "task_id": task.id,
            "message": "기업 추출이 시작되었습니다",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"기업 추출 실행 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기업 추출 실행 실패: {str(e)}")


@router.post("/companies/statistics/update", summary="기업 통계 업데이트")
def trigger_statistics_update() -> Dict[str, Any]:
    """
    기업 통계 정보를 업데이트합니다.
    
    Returns
    -------
    Dict[str, Any]
        업데이트 실행 결과
    """
    try:
        # 비동기 태스크 실행
        task = update_company_statistics_task.delay()
        
        return {
            "status": "queued",
            "task_id": task.id,
            "message": "기업 통계 업데이트가 시작되었습니다",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"기업 통계 업데이트 실행 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기업 통계 업데이트 실행 실패: {str(e)}")


@router.get("/companies/analytics/trends", summary="기업 트렌드 분석")
def get_company_trends(
    company_id: Optional[int] = Query(None, description="기업 ID (None이면 전체)"),
    period: str = Query("weekly", description="분석 기간 (daily/weekly/monthly)"),
    days: int = Query(30, ge=1, le=365, description="분석 일수")
) -> Dict[str, Any]:
    """
    기업 트렌드 분석을 조회합니다.
    
    Parameters
    ----------
    company_id : Optional[int]
        기업 ID
    period : str
        분석 기간
    days : int
        분석 일수
        
    Returns
    -------
    Dict[str, Any]
        트렌드 분석 결과
    """
    try:
        db = SessionLocal()
        repo = CompanyRepo(db)
        
        trends = repo.get_company_trends(
            company_id=company_id,
            period=period,
            days=days
        )
        
        db.close()
        
        return {
            "trends": trends,
            "period": period,
            "days": days,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"기업 트렌드 분석 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기업 트렌드 분석 조회 실패: {str(e)}")
