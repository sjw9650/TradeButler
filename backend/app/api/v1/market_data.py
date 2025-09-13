#!/usr/bin/env python3
"""
시장 데이터 API 엔드포인트

실제 금융 데이터를 제공하는 API
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging

from ...repo.db import get_db
from ...services.market_data import MarketDataService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/market/indices", summary="주요 지수 데이터 조회")
async def get_market_indices(
    market: Optional[str] = Query(None, description="시장 필터 (KOR, USA, GLOBAL)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    주요 지수 데이터를 조회합니다.
    
    Parameters
    ----------
    market : Optional[str]
        시장 필터 (KOR, USA, GLOBAL)
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        지수 데이터 목록
    """
    try:
        market_service = MarketDataService()
        
        if market == 'KOR':
            indices = await market_service.get_korean_indices()
        elif market == 'USA':
            indices = await market_service.get_us_indices()
        elif market == 'GLOBAL':
            indices = await market_service.get_global_indices()
        else:
            indices = await market_service.get_all_indices()
        
        return {
            "market": market or "ALL",
            "indices": indices,
            "total_count": len(indices),
            "generated_at": market_service.get_market_status()["last_updated"]
        }
        
    except Exception as e:
        logger.error(f"지수 데이터 조회 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="지수 데이터 조회에 실패했습니다.")

@router.get("/market/indices/{symbol}", summary="특정 지수 데이터 조회")
async def get_index_data(
    symbol: str,
    period: str = Query("1D", description="기간 (1D, 1W, 1M, YTD, 1Y)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    특정 지수의 데이터를 조회합니다.
    
    Parameters
    ----------
    symbol : str
        지수 심볼 (KOSPI, SPX, NDX 등)
    period : str
        조회 기간
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        지수 데이터
    """
    try:
        market_service = MarketDataService()
        index_data = await market_service.get_index_by_period(symbol, period)
        
        if not index_data:
            raise HTTPException(status_code=404, detail="지수를 찾을 수 없습니다.")
        
        return index_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"지수 데이터 조회 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="지수 데이터 조회에 실패했습니다.")

@router.get("/market/status", summary="시장 상태 조회")
async def get_market_status(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    시장 상태 정보를 조회합니다.
    
    Parameters
    ----------
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        시장 상태 정보
    """
    try:
        market_service = MarketDataService()
        status = market_service.get_market_status()
        
        return status
        
    except Exception as e:
        logger.error(f"시장 상태 조회 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="시장 상태 조회에 실패했습니다.")

@router.get("/market/summary", summary="시장 요약 정보 조회")
async def get_market_summary(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    시장 요약 정보를 조회합니다.
    
    Parameters
    ----------
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        시장 요약 정보
    """
    try:
        market_service = MarketDataService()
        
        # 모든 지수 데이터 조회
        all_indices = await market_service.get_all_indices()
        
        # 요약 통계 계산
        total_indices = len(all_indices)
        rising_indices = len([idx for idx in all_indices if idx.get('change', 0) > 0])
        falling_indices = len([idx for idx in all_indices if idx.get('change', 0) < 0])
        flat_indices = total_indices - rising_indices - falling_indices
        
        # 시장별 통계
        market_stats = {}
        for index in all_indices:
            market = index.get('market', 'UNKNOWN')
            if market not in market_stats:
                market_stats[market] = {
                    'total': 0,
                    'rising': 0,
                    'falling': 0,
                    'flat': 0
                }
            
            market_stats[market]['total'] += 1
            if index.get('change', 0) > 0:
                market_stats[market]['rising'] += 1
            elif index.get('change', 0) < 0:
                market_stats[market]['falling'] += 1
            else:
                market_stats[market]['flat'] += 1
        
        return {
            "total_indices": total_indices,
            "rising_indices": rising_indices,
            "falling_indices": falling_indices,
            "flat_indices": flat_indices,
            "market_stats": market_stats,
            "market_status": market_service.get_market_status(),
            "generated_at": market_service.get_market_status()["last_updated"]
        }
        
    except Exception as e:
        logger.error(f"시장 요약 조회 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="시장 요약 조회에 실패했습니다.")
