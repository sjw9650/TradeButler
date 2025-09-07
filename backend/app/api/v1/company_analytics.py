#!/usr/bin/env python3
"""
기업 분석 API 엔드포인트

기업의 언급 횟수, 감정 분석, 트렌드 분석을 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from ...repo.db import get_db
from ...core.oauth import get_current_user_optional
from ...models.user import User
from ...services.company_analytics import CompanyAnalyticsService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/companies/{company_id}/analytics/mentions-trend", summary="기업 언급 트렌드 분석")
def get_company_mentions_trend(
    company_id: int,
    days: int = Query(30, ge=1, le=365, description="분석 기간 (일)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    기업의 언급 트렌드를 분석합니다.
    
    Parameters
    ----------
    company_id : int
        기업 ID
    days : int
        분석 기간 (일)
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        언급 트렌드 분석 결과
    """
    try:
        analytics_service = CompanyAnalyticsService(db)
        result = analytics_service.get_company_mentions_trend(company_id, days)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 언급 트렌드 분석 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="언급 트렌드 분석에 실패했습니다.")

@router.get("/companies/{company_id}/analytics/sentiment", summary="기업 감정 분석")
def get_company_sentiment_analysis(
    company_id: int,
    days: int = Query(30, ge=1, le=365, description="분석 기간 (일)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    기업의 감정 분석을 수행합니다.
    
    Parameters
    ----------
    company_id : int
        기업 ID
    days : int
        분석 기간 (일)
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        감정 분석 결과
    """
    try:
        analytics_service = CompanyAnalyticsService(db)
        result = analytics_service.get_company_sentiment_analysis(company_id, days)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 감정 분석 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="감정 분석에 실패했습니다.")

@router.get("/companies/{company_id}/analytics/competitors", summary="기업 경쟁사 분석")
def get_company_competitor_analysis(
    company_id: int,
    days: int = Query(30, ge=1, le=365, description="분석 기간 (일)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    기업의 경쟁사 분석을 수행합니다.
    
    Parameters
    ----------
    company_id : int
        기업 ID
    days : int
        분석 기간 (일)
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        경쟁사 분석 결과
    """
    try:
        analytics_service = CompanyAnalyticsService(db)
        result = analytics_service.get_company_competitor_analysis(company_id, days)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 경쟁사 분석 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="경쟁사 분석에 실패했습니다.")

@router.get("/companies/{company_id}/analytics/comprehensive", summary="기업 종합 분석")
def get_company_comprehensive_analysis(
    company_id: int,
    days: int = Query(30, ge=1, le=365, description="분석 기간 (일)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    기업의 종합 분석을 수행합니다.
    
    Parameters
    ----------
    company_id : int
        기업 ID
    days : int
        분석 기간 (일)
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        종합 분석 결과
    """
    try:
        analytics_service = CompanyAnalyticsService(db)
        result = analytics_service.get_company_comprehensive_analysis(company_id, days)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 종합 분석 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="종합 분석에 실패했습니다.")

@router.get("/companies/analytics/leaderboard", summary="기업 언급 순위")
def get_company_leaderboard(
    days: int = Query(7, ge=1, le=365, description="분석 기간 (일)"),
    limit: int = Query(20, ge=1, le=100, description="조회할 개수"),
    industry: Optional[str] = Query(None, description="업종 필터"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    기업 언급 순위를 조회합니다.
    
    Parameters
    ----------
    days : int
        분석 기간 (일)
    limit : int
        조회할 개수
    industry : Optional[str]
        업종 필터
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        기업 언급 순위
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func, and_
        from ...models.company import Company, CompanyMention
        from ...models.content import Content
        
        # 분석 기간 설정
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 기본 쿼리
        query = db.query(
            Company.id,
            Company.name,
            Company.symbol,
            Company.stock_market,
            Company.industry,
            func.count(CompanyMention.id).label('mention_count')
        ).join(
            CompanyMention, Company.id == CompanyMention.company_id
        ).join(
            Content, CompanyMention.content_id == Content.id
        ).filter(
            and_(
                Content.published_at >= start_date,
                Content.published_at <= end_date,
                Content.is_active == "active",
                Company.is_active == True
            )
        )
        
        # 업종 필터 적용
        if industry:
            query = query.filter(Company.industry == industry)
        
        # 결과 조회
        results = query.group_by(
            Company.id,
            Company.name,
            Company.symbol,
            Company.stock_market,
            Company.industry
        ).order_by(
            func.count(CompanyMention.id).desc()
        ).limit(limit).all()
        
        leaderboard = []
        for rank, result in enumerate(results, 1):
            leaderboard.append({
                "rank": rank,
                "company_id": result.id,
                "company_name": result.name,
                "symbol": result.symbol,
                "stock_market": result.stock_market,
                "industry": result.industry,
                "mention_count": result.mention_count
            })
        
        return {
            "analysis_period": f"{days}일",
            "industry_filter": industry,
            "total_companies": len(leaderboard),
            "leaderboard": leaderboard,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"기업 언급 순위 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="기업 언급 순위 조회에 실패했습니다.")

@router.get("/companies/analytics/industry-trends", summary="업종별 트렌드 분석")
def get_industry_trends(
    days: int = Query(30, ge=1, le=365, description="분석 기간 (일)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    업종별 트렌드를 분석합니다.
    
    Parameters
    ----------
    days : int
        분석 기간 (일)
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        업종별 트렌드 분석 결과
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func, and_
        from ...models.company import Company, CompanyMention
        from ...models.content import Content
        
        # 분석 기간 설정
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 업종별 언급 횟수 조회
        industry_mentions = db.query(
            Company.industry,
            func.count(CompanyMention.id).label('mention_count'),
            func.count(func.distinct(Company.id)).label('company_count')
        ).join(
            CompanyMention, Company.id == CompanyMention.company_id
        ).join(
            Content, CompanyMention.content_id == Content.id
        ).filter(
            and_(
                Content.published_at >= start_date,
                Content.published_at <= end_date,
                Content.is_active == "active",
                Company.is_active == True,
                Company.industry.isnot(None)
            )
        ).group_by(
            Company.industry
        ).order_by(
            func.count(CompanyMention.id).desc()
        ).all()
        
        industry_trends = []
        for result in industry_mentions:
            industry_trends.append({
                "industry": result.industry,
                "mention_count": result.mention_count,
                "company_count": result.company_count,
                "avg_mentions_per_company": round(result.mention_count / result.company_count, 2)
            })
        
        return {
            "analysis_period": f"{days}일",
            "total_industries": len(industry_trends),
            "industry_trends": industry_trends,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"업종별 트렌드 분석 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="업종별 트렌드 분석에 실패했습니다.")
