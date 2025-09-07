#!/usr/bin/env python3
"""
팔로잉 상태 캐시 관리 서비스

Redis를 사용하여 팔로잉 상태를 빠르게 관리합니다.
"""

import redis
import json
from typing import Set, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FollowingCacheService:
    """팔로잉 상태 캐시 관리 서비스"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.following_key_prefix = "following:"
        self.following_info_key_prefix = "following_info:"
        self.cache_ttl = 3600  # 1시간
    
    def get_following_companies(self, user_id: str) -> Set[int]:
        """
        사용자가 팔로잉하는 기업 ID 목록을 조회합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
            
        Returns
        -------
        Set[int]
            팔로잉 기업 ID 목록
        """
        try:
            key = f"{self.following_key_prefix}{user_id}"
            company_ids = self.redis.smembers(key)
            return {int(company_id) for company_id in company_ids} if company_ids else set()
        except Exception as e:
            logger.error(f"팔로잉 기업 조회 실패: {str(e)}")
            return set()
    
    def add_following(self, user_id: str, company_id: int, priority: int = 1, 
                     notification_enabled: bool = True, auto_summarize: bool = True) -> bool:
        """
        팔로잉을 추가합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
        company_id : int
            기업 ID
        priority : int
            우선순위
        notification_enabled : bool
            알림 활성화
        auto_summarize : bool
            자동 요약 활성화
            
        Returns
        -------
        bool
            성공 여부
        """
        try:
            # 팔로잉 기업 목록에 추가
            following_key = f"{self.following_key_prefix}{user_id}"
            self.redis.sadd(following_key, company_id)
            self.redis.expire(following_key, self.cache_ttl)
            
            # 팔로잉 상세 정보 저장
            following_info = {
                "priority": priority,
                "notification_enabled": notification_enabled,
                "auto_summarize": auto_summarize,
                "followed_at": datetime.utcnow().isoformat()
            }
            info_key = f"{self.following_info_key_prefix}{user_id}:{company_id}"
            self.redis.setex(info_key, self.cache_ttl, json.dumps(following_info))
            
            return True
        except Exception as e:
            logger.error(f"팔로잉 추가 실패: {str(e)}")
            return False
    
    def remove_following(self, user_id: str, company_id: int) -> bool:
        """
        팔로잉을 제거합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
        company_id : int
            기업 ID
            
        Returns
        -------
        bool
            성공 여부
        """
        try:
            # 팔로잉 기업 목록에서 제거
            following_key = f"{self.following_key_prefix}{user_id}"
            self.redis.srem(following_key, company_id)
            
            # 팔로잉 상세 정보 제거
            info_key = f"{self.following_info_key_prefix}{user_id}:{company_id}"
            self.redis.delete(info_key)
            
            return True
        except Exception as e:
            logger.error(f"팔로잉 제거 실패: {str(e)}")
            return False
    
    def get_following_info(self, user_id: str, company_id: int) -> Optional[Dict[str, Any]]:
        """
        팔로잉 상세 정보를 조회합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
        company_id : int
            기업 ID
            
        Returns
        -------
        Optional[Dict[str, Any]]
            팔로잉 상세 정보
        """
        try:
            info_key = f"{self.following_info_key_prefix}{user_id}:{company_id}"
            info_data = self.redis.get(info_key)
            return json.loads(info_data) if info_data else None
        except Exception as e:
            logger.error(f"팔로잉 정보 조회 실패: {str(e)}")
            return None
    
    def is_following(self, user_id: str, company_id: int) -> bool:
        """
        팔로잉 여부를 확인합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
        company_id : int
            기업 ID
            
        Returns
        -------
        bool
            팔로잉 여부
        """
        try:
            following_key = f"{self.following_key_prefix}{user_id}"
            return self.redis.sismember(following_key, company_id)
        except Exception as e:
            logger.error(f"팔로잉 확인 실패: {str(e)}")
            return False
    
    def get_all_following_info(self, user_id: str) -> Dict[int, Dict[str, Any]]:
        """
        사용자의 모든 팔로잉 정보를 조회합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
            
        Returns
        -------
        Dict[int, Dict[str, Any]]
            팔로잉 정보 (기업 ID -> 상세 정보)
        """
        try:
            following_companies = self.get_following_companies(user_id)
            following_info = {}
            
            for company_id in following_companies:
                info = self.get_following_info(user_id, company_id)
                if info:
                    following_info[company_id] = info
            
            return following_info
        except Exception as e:
            logger.error(f"전체 팔로잉 정보 조회 실패: {str(e)}")
            return {}
    
    def sync_from_db(self, user_id: str, db_following_data: Dict[int, Dict[str, Any]]) -> bool:
        """
        DB에서 팔로잉 데이터를 동기화합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
        db_following_data : Dict[int, Dict[str, Any]]
            DB에서 조회한 팔로잉 데이터
            
        Returns
        -------
        bool
            성공 여부
        """
        try:
            # 기존 캐시 삭제
            following_key = f"{self.following_key_prefix}{user_id}"
            self.redis.delete(following_key)
            
            # 새 데이터로 캐시 업데이트
            for company_id, info in db_following_data.items():
                self.redis.sadd(following_key, company_id)
                
                info_key = f"{self.following_info_key_prefix}{user_id}:{company_id}"
                self.redis.setex(info_key, self.cache_ttl, json.dumps(info))
            
            self.redis.expire(following_key, self.cache_ttl)
            return True
        except Exception as e:
            logger.error(f"DB 동기화 실패: {str(e)}")
            return False
