#!/usr/bin/env python3
"""
최적화된 기업 관련 API 엔드포인트

Redis 캐시를 사용하여 성능을 최적화합니다.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ...repo.db import SessionLocal, get_db
from ...repo.company import CompanyRepo
from ...models.company import Company, UserFollowing, CompanyMention
from ...services.following_cache import FollowingCacheService
from ...repo.redis_client import get_redis_client

router = APIRouter()
logger = logging.getLogger(__name__)


def get_following_cache() -> FollowingCacheService:
    """팔로잉 캐시 서비스 의존성 주입"""
    redis_client = get_redis_client()
    return FollowingCacheService(redis_client)


@router.get("/companies/fast", summary="최적화된 기업 목록 조회")
def get_companies_fast(
    limit: int = Query(20, ge=1, le=100, description="조회할 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    search: Optional[str] = Query(None, description="기업명 검색"),
    industry: Optional[str] = Query(None, description="업종 필터"),
    sort_by: str = Query("mentions", description="정렬 기준 (mentions/name/created)"),
    order: str = Query("desc", description="정렬 순서 (asc/desc)"),
    user_id: Optional[str] = Query(None, description="사용자 ID (팔로잉 상태 포함)"),
    db: SessionLocal = Depends(get_db),
    following_cache: FollowingCacheService = Depends(get_following_cache)
) -> Dict[str, Any]:
    """
    최적화된 기업 목록을 조회합니다.
    Redis 캐시를 사용하여 팔로잉 상태를 빠르게 조회합니다.
    """
    try:
        repo = CompanyRepo(db)
        
        # 기업 목록 조회 (팔로잉 상태 제외)
        companies = repo.list_companies(
            limit=limit,
            offset=offset,
            search=search,
            industry=industry,
            sort_by=sort_by
        )
        
        total = repo.count_companies(search=search, industry=industry)
        
        # 팔로잉 상태 조회 (Redis에서 빠르게 조회)
        following_companies = set()
        following_info_map = {}
        
        if user_id:
            following_companies = following_cache.get_following_companies(user_id)
            following_info_map = following_cache.get_all_following_info(user_id)
        
        # 응답 데이터 구성
        company_list = []
        for company in companies:
            is_following = company.id in following_companies if user_id else False
            following_info = following_info_map.get(company.id) if is_following else None
            
            company_list.append({
                "id": company.id,
                "name": company.name,
                "display_name": company.display_name,
                "industry": company.industry,
                "stock_symbol": company.stock_symbol,
                "stock_market": company.stock_market,
                "country": company.country,
                "total_mentions": company.total_mentions,
                "last_mentioned_at": company.last_mentioned_at.isoformat() if company.last_mentioned_at else None,
                "confidence_score": company.confidence_score,
                "is_active": company.is_active,
                "created_at": company.created_at.isoformat(),
                "is_following": is_following,
                "following_info": following_info
            })
        
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


@router.get("/companies/following", summary="팔로잉 기업 목록 조회")
def get_following_companies(
    user_id: str = Query(..., description="사용자 ID"),
    limit: int = Query(20, ge=1, le=100, description="조회할 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    db: SessionLocal = Depends(get_db),
    following_cache: FollowingCacheService = Depends(get_following_cache)
) -> Dict[str, Any]:
    """
    사용자가 팔로잉하는 기업 목록을 조회합니다.
    Redis에서 팔로잉 기업 ID를 조회한 후 DB에서 기업 정보를 조회합니다.
    """
    try:
        # Redis에서 팔로잉 기업 ID 조회
        following_company_ids = following_cache.get_following_companies(user_id)
        
        if not following_company_ids:
            return {
                "companies": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False
            }
        
        # DB에서 기업 정보 조회
        repo = CompanyRepo(db)
        companies = repo.get_companies_by_ids(list(following_company_ids))
        
        # 팔로잉 정보 조회
        following_info_map = following_cache.get_all_following_info(user_id)
        
        # 응답 데이터 구성
        company_list = []
        for company in companies:
            following_info = following_info_map.get(company.id)
            
            company_list.append({
                "id": company.id,
                "name": company.name,
                "display_name": company.display_name,
                "industry": company.industry,
                "stock_symbol": company.stock_symbol,
                "stock_market": company.stock_market,
                "country": company.country,
                "total_mentions": company.total_mentions,
                "last_mentioned_at": company.last_mentioned_at.isoformat() if company.last_mentioned_at else None,
                "confidence_score": company.confidence_score,
                "is_active": company.is_active,
                "created_at": company.created_at.isoformat(),
                "is_following": True,
                "following_info": following_info
            })
        
        # 정렬 (팔로잉 우선순위 기준)
        company_list.sort(key=lambda x: x["following_info"]["priority"] if x["following_info"] else 0, reverse=True)
        
        # 페이징 적용
        total = len(company_list)
        start_idx = offset
        end_idx = offset + limit
        paginated_companies = company_list[start_idx:end_idx]
        
        return {
            "companies": paginated_companies,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": end_idx < total
        }
        
    except Exception as e:
        logger.error(f"팔로잉 기업 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"팔로잉 기업 조회 실패: {str(e)}")


@router.post("/companies/{company_id}/follow/fast", summary="최적화된 기업 팔로잉")
def follow_company_fast(
    company_id: int,
    user_id: str = Query(..., description="사용자 ID"),
    priority: int = Query(1, ge=1, le=5, description="우선순위 (1-5)"),
    notification_enabled: bool = Query(True, description="알림 활성화"),
    auto_summarize: bool = Query(True, description="자동 요약 활성화"),
    db: SessionLocal = Depends(get_db),
    following_cache: FollowingCacheService = Depends(get_following_cache)
) -> Dict[str, Any]:
    """
    최적화된 기업 팔로잉을 수행합니다.
    Redis 캐시와 DB를 모두 업데이트합니다.
    """
    try:
        # 기업 존재 여부 확인
        repo = CompanyRepo(db)
        company = repo.get_by_id(company_id)
        if not company:
            raise HTTPException(status_code=404, detail="기업을 찾을 수 없습니다")
        
        # 이미 팔로잉 중인지 확인
        if following_cache.is_following(user_id, company_id):
            raise HTTPException(status_code=400, detail="이미 팔로잉 중인 기업입니다")
        
        # DB에 팔로잉 정보 저장
        following_record = UserFollowing(
            user_id=user_id,
            company_id=company_id,
            priority=priority,
            notification_enabled=notification_enabled,
            auto_summarize=auto_summarize
        )
        db.add(following_record)
        db.commit()
        
        # Redis 캐시 업데이트
        following_cache.add_following(
            user_id=user_id,
            company_id=company_id,
            priority=priority,
            notification_enabled=notification_enabled,
            auto_summarize=auto_summarize
        )
        
        return {
            "success": True,
            "message": f"{company.name} 팔로잉을 시작했습니다",
            "company_id": company_id,
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 팔로잉 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기업 팔로잉 실패: {str(e)}")


@router.delete("/companies/{company_id}/unfollow/fast", summary="최적화된 기업 언팔로잉")
def unfollow_company_fast(
    company_id: int,
    user_id: str = Query(..., description="사용자 ID"),
    db: SessionLocal = Depends(get_db),
    following_cache: FollowingCacheService = Depends(get_following_cache)
) -> Dict[str, Any]:
    """
    최적화된 기업 언팔로잉을 수행합니다.
    Redis 캐시와 DB를 모두 업데이트합니다.
    """
    try:
        # 팔로잉 상태 확인
        if not following_cache.is_following(user_id, company_id):
            raise HTTPException(status_code=400, detail="팔로잉 중이 아닌 기업입니다")
        
        # DB에서 팔로잉 정보 삭제
        following_record = db.query(UserFollowing).filter(
            UserFollowing.user_id == user_id,
            UserFollowing.company_id == company_id
        ).first()
        
        if following_record:
            db.delete(following_record)
            db.commit()
        
        # Redis 캐시에서 제거
        following_cache.remove_following(user_id, company_id)
        
        return {
            "success": True,
            "message": "팔로잉을 해제했습니다",
            "company_id": company_id,
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 언팔로잉 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기업 언팔로잉 실패: {str(e)}")


@router.post("/companies/sync-cache", summary="팔로잉 캐시 동기화")
def sync_following_cache(
    user_id: str = Query(..., description="사용자 ID"),
    db: SessionLocal = Depends(get_db),
    following_cache: FollowingCacheService = Depends(get_following_cache)
) -> Dict[str, Any]:
    """
    DB의 팔로잉 데이터를 Redis 캐시에 동기화합니다.
    """
    try:
        # DB에서 팔로잉 데이터 조회
        following_records = db.query(UserFollowing).filter(
            UserFollowing.user_id == user_id
        ).all()
        
        # 캐시용 데이터 구성
        db_following_data = {}
        for record in following_records:
            db_following_data[record.company_id] = {
                "priority": record.priority,
                "notification_enabled": record.notification_enabled,
                "auto_summarize": record.auto_summarize,
                "followed_at": record.created_at.isoformat()
            }
        
        # Redis 캐시 동기화
        success = following_cache.sync_from_db(user_id, db_following_data)
        
        if success:
            return {
                "success": True,
                "message": f"캐시 동기화 완료: {len(db_following_data)}개 기업",
                "synced_count": len(db_following_data)
            }
        else:
            raise HTTPException(status_code=500, detail="캐시 동기화 실패")
        
    except Exception as e:
        logger.error(f"캐시 동기화 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"캐시 동기화 실패: {str(e)}")
