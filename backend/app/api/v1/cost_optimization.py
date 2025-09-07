#!/usr/bin/env python3
"""
비용 최적화 API 엔드포인트

AI 호출 최소화 및 캐싱 전략을 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from ...repo.db import get_db
from ...core.oauth import get_current_user_optional
from ...models.user import User
from ...services.cost_optimizer import CostOptimizerService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/cost/summary", summary="비용 요약 조회")
def get_cost_summary(
    days: int = Query(30, ge=1, le=365, description="분석 기간 (일)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    비용 요약을 조회합니다.
    
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
        비용 요약 정보
    """
    try:
        optimizer_service = CostOptimizerService(db)
        result = optimizer_service.get_cost_summary(days)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"비용 요약 조회 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="비용 요약 조회에 실패했습니다.")

@router.get("/cost/cache-hit-rate", summary="캐시 적중률 조회")
def get_cache_hit_rate(
    days: int = Query(7, ge=1, le=30, description="분석 기간 (일)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    캐시 적중률을 조회합니다.
    
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
        캐시 적중률 정보
    """
    try:
        optimizer_service = CostOptimizerService(db)
        result = optimizer_service.get_cache_hit_rate(days)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"캐시 적중률 조회 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="캐시 적중률 조회에 실패했습니다.")

@router.post("/cost/optimize-content/{content_id}", summary="콘텐츠 처리 최적화")
def optimize_content_processing(
    content_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    콘텐츠 처리 최적화를 수행합니다.
    
    Parameters
    ----------
    content_id : int
        콘텐츠 ID
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        최적화 결과
    """
    try:
        optimizer_service = CostOptimizerService(db)
        result = optimizer_service.optimize_content_processing(content_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"콘텐츠 처리 최적화 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="콘텐츠 처리 최적화에 실패했습니다.")

@router.get("/cost/duplicate-detection", summary="중복 콘텐츠 감지")
def get_duplicate_content_detection(
    days: int = Query(7, ge=1, le=30, description="분석 기간 (일)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    중복 콘텐츠 감지를 수행합니다.
    
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
        중복 콘텐츠 감지 결과
    """
    try:
        optimizer_service = CostOptimizerService(db)
        result = optimizer_service.get_duplicate_content_detection(days)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"중복 콘텐츠 감지 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="중복 콘텐츠 감지에 실패했습니다.")

@router.get("/cost/processing-efficiency", summary="처리 효율성 분석")
def get_processing_efficiency(
    days: int = Query(7, ge=1, le=30, description="분석 기간 (일)"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    처리 효율성을 분석합니다.
    
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
        처리 효율성 분석 결과
    """
    try:
        optimizer_service = CostOptimizerService(db)
        result = optimizer_service.get_processing_efficiency(days)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"처리 효율성 분석 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="처리 효율성 분석에 실패했습니다.")

@router.get("/cost/recommendations", summary="비용 최적화 권장사항")
def get_cost_optimization_recommendations(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    비용 최적화 권장사항을 조회합니다.
    
    Parameters
    ----------
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        비용 최적화 권장사항
    """
    try:
        optimizer_service = CostOptimizerService(db)
        
        # 다양한 분석 수행
        cost_summary = optimizer_service.get_cost_summary(30)
        cache_hit_rate = optimizer_service.get_cache_hit_rate(7)
        duplicate_detection = optimizer_service.get_duplicate_content_detection(7)
        processing_efficiency = optimizer_service.get_processing_efficiency(7)
        
        # 종합 권장사항 생성
        recommendations = []
        
        # 비용 요약에서 권장사항 추출
        if "optimization_suggestions" in cost_summary:
            recommendations.extend(cost_summary["optimization_suggestions"])
        
        # 캐시 적중률 기반 권장사항
        if cache_hit_rate.get("cache_hit_rate", 0) < 50:
            recommendations.append({
                "type": "cache_improvement",
                "priority": "high",
                "title": "캐시 적중률 개선",
                "description": f"현재 캐시 적중률이 {cache_hit_rate.get('cache_hit_rate', 0)}%입니다.",
                "suggestion": "캐시 전략을 개선하여 중복 요청을 줄이세요.",
                "potential_savings": f"${cost_summary.get('total_cost', 0) * 0.3:.2f}/월"
            })
        
        # 중복 콘텐츠 기반 권장사항
        if duplicate_detection.get("duplicate_rate", 0) > 5:
            recommendations.append({
                "type": "duplicate_prevention",
                "priority": "medium",
                "title": "중복 콘텐츠 방지",
                "description": f"중복 콘텐츠 비율이 {duplicate_detection.get('duplicate_rate', 0)}%입니다.",
                "suggestion": "중복 콘텐츠를 사전에 필터링하여 처리 비용을 절약하세요.",
                "potential_savings": f"${duplicate_detection.get('duplicates_found', 0) * 0.01:.2f}/월"
            })
        
        # 처리 효율성 기반 권장사항
        if processing_efficiency.get("failure_rate", 0) > 5:
            recommendations.append({
                "type": "error_handling",
                "priority": "high",
                "title": "에러 처리 개선",
                "description": f"처리 실패율이 {processing_efficiency.get('failure_rate', 0)}%입니다.",
                "suggestion": "에러 로그를 분석하고 재시도 로직을 개선하세요.",
                "potential_improvement": "처리 성공률 15% 향상"
            })
        
        # 우선순위별 정렬
        priority_order = {"high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))
        
        return {
            "total_recommendations": len(recommendations),
            "recommendations": recommendations,
            "cost_summary": cost_summary,
            "cache_performance": cache_hit_rate,
            "duplicate_analysis": duplicate_detection,
            "efficiency_analysis": processing_efficiency,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"비용 최적화 권장사항 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="비용 최적화 권장사항 조회에 실패했습니다.")
