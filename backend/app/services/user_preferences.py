#!/usr/bin/env python3
"""
사용자 설정 서비스

팔로잉 기업 관리, 알림 설정, 필터링 옵션을 제공합니다.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import json

from ..models.user import User, UserSession
from ..models.company import Company, UserFollowing
from ..repo.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class UserPreferencesService:
    """사용자 설정 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = get_redis_client()
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 설정을 조회합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
            
        Returns
        -------
        Dict[str, Any]
            사용자 설정 정보
        """
        try:
            # 사용자 정보 조회
            user = self.db.query(User).filter(User.google_id == user_id).first()
            if not user:
                return {"error": "사용자를 찾을 수 없습니다."}
            
            # 기본 설정값
            default_preferences = {
                "notifications": {
                    "email_notifications": True,
                    "push_notifications": True,
                    "newsletter": False,
                    "market_alerts": True,
                    "company_mentions": True,
                    "price_alerts": False,
                    "news_digest": True
                },
                "display": {
                    "theme": "light",
                    "language": "ko",
                    "timezone": "Asia/Seoul",
                    "date_format": "YYYY-MM-DD",
                    "currency": "KRW"
                },
                "filtering": {
                    "min_confidence_score": 0.5,
                    "max_articles_per_day": 50,
                    "excluded_sources": [],
                    "included_keywords": [],
                    "excluded_keywords": []
                },
                "ai_settings": {
                    "summary_length": "medium",  # short, medium, long
                    "include_sentiment": True,
                    "include_insights": True,
                    "auto_tagging": True
                }
            }
            
            # 사용자 설정과 기본값 병합
            user_preferences = user.preferences or {}
            merged_preferences = self._merge_preferences(default_preferences, user_preferences)
            
            return {
                "user_id": user_id,
                "preferences": merged_preferences,
                "last_updated": user.updated_at.isoformat() if user.updated_at else None,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"사용자 설정 조회 실패: {str(e)}")
            return {"error": str(e)}
    
    def _merge_preferences(self, default: Dict, user: Dict) -> Dict:
        """설정값을 병합합니다."""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_preferences(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        사용자 설정을 업데이트합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
        preferences : Dict[str, Any]
            업데이트할 설정
            
        Returns
        -------
        Dict[str, Any]
            업데이트 결과
        """
        try:
            # 사용자 정보 조회
            user = self.db.query(User).filter(User.google_id == user_id).first()
            if not user:
                return {"error": "사용자를 찾을 수 없습니다."}
            
            # 기존 설정과 병합
            current_preferences = user.preferences or {}
            updated_preferences = self._merge_preferences(current_preferences, preferences)
            
            # 데이터베이스 업데이트
            user.preferences = updated_preferences
            user.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Redis 캐시 업데이트
            cache_key = f"user_preferences:{user_id}"
            self.redis_client.setex(
                cache_key, 
                3600,  # 1시간 TTL
                json.dumps(updated_preferences)
            )
            
            return {
                "user_id": user_id,
                "preferences": updated_preferences,
                "updated_at": user.updated_at.isoformat(),
                "message": "설정이 성공적으로 업데이트되었습니다."
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"사용자 설정 업데이트 실패: {str(e)}")
            return {"error": str(e)}
    
    def get_following_companies(self, user_id: str) -> Dict[str, Any]:
        """
        팔로잉한 기업 목록을 조회합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
            
        Returns
        -------
        Dict[str, Any]
            팔로잉 기업 목록
        """
        try:
            # 팔로잉 기업 조회
            following_companies = self.db.query(
                Company.id,
                Company.name,
                Company.symbol,
                Company.stock_market,
                Company.industry,
                UserFollowing.priority,
                UserFollowing.created_at,
                UserFollowing.notes
            ).join(
                UserFollowing, Company.id == UserFollowing.company_id
            ).filter(
                and_(
                    UserFollowing.user_id == user_id,
                    Company.is_active == True
                )
            ).order_by(
                desc(UserFollowing.priority),
                asc(Company.name)
            ).all()
            
            companies = []
            for company in following_companies:
                companies.append({
                    "company_id": company.id,
                    "name": company.name,
                    "symbol": company.symbol,
                    "stock_market": company.stock_market,
                    "industry": company.industry,
                    "priority": company.priority,
                    "followed_at": company.created_at.isoformat(),
                    "notes": company.notes
                })
            
            return {
                "user_id": user_id,
                "total_companies": len(companies),
                "companies": companies,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"팔로잉 기업 조회 실패: {str(e)}")
            return {"error": str(e)}
    
    def add_following_company(self, user_id: str, company_id: int, priority: int = 0, notes: str = "") -> Dict[str, Any]:
        """
        기업을 팔로잉합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
        company_id : int
            기업 ID
        priority : int
            우선순위 (0-10)
        notes : str
            메모
            
        Returns
        -------
        Dict[str, Any]
            팔로잉 결과
        """
        try:
            # 기업 존재 확인
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return {"error": "기업을 찾을 수 없습니다."}
            
            # 이미 팔로잉 중인지 확인
            existing_following = self.db.query(UserFollowing).filter(
                and_(
                    UserFollowing.user_id == user_id,
                    UserFollowing.company_id == company_id
                )
            ).first()
            
            if existing_following:
                return {"error": "이미 팔로잉 중인 기업입니다."}
            
            # 팔로잉 추가
            new_following = UserFollowing(
                user_id=user_id,
                company_id=company_id,
                priority=priority,
                notes=notes,
                created_at=datetime.utcnow()
            )
            
            self.db.add(new_following)
            self.db.commit()
            
            # Redis 캐시 업데이트
            self._update_following_cache(user_id)
            
            return {
                "user_id": user_id,
                "company_id": company_id,
                "company_name": company.name,
                "priority": priority,
                "notes": notes,
                "followed_at": new_following.created_at.isoformat(),
                "message": "기업을 성공적으로 팔로잉했습니다."
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"기업 팔로잉 실패: {str(e)}")
            return {"error": str(e)}
    
    def remove_following_company(self, user_id: str, company_id: int) -> Dict[str, Any]:
        """
        기업 팔로잉을 해제합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
        company_id : int
            기업 ID
            
        Returns
        -------
        Dict[str, Any]
            팔로잉 해제 결과
        """
        try:
            # 팔로잉 정보 조회
            following = self.db.query(UserFollowing).filter(
                and_(
                    UserFollowing.user_id == user_id,
                    UserFollowing.company_id == company_id
                )
            ).first()
            
            if not following:
                return {"error": "팔로잉 중인 기업이 아닙니다."}
            
            # 팔로잉 해제
            self.db.delete(following)
            self.db.commit()
            
            # Redis 캐시 업데이트
            self._update_following_cache(user_id)
            
            return {
                "user_id": user_id,
                "company_id": company_id,
                "message": "기업 팔로잉을 해제했습니다."
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"기업 팔로잉 해제 실패: {str(e)}")
            return {"error": str(e)}
    
    def update_following_priority(self, user_id: str, company_id: int, priority: int) -> Dict[str, Any]:
        """
        팔로잉 기업의 우선순위를 업데이트합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
        company_id : int
            기업 ID
        priority : int
            새로운 우선순위 (0-10)
            
        Returns
        -------
        Dict[str, Any]
            우선순위 업데이트 결과
        """
        try:
            # 팔로잉 정보 조회
            following = self.db.query(UserFollowing).filter(
                and_(
                    UserFollowing.user_id == user_id,
                    UserFollowing.company_id == company_id
                )
            ).first()
            
            if not following:
                return {"error": "팔로잉 중인 기업이 아닙니다."}
            
            # 우선순위 업데이트
            following.priority = priority
            following.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Redis 캐시 업데이트
            self._update_following_cache(user_id)
            
            return {
                "user_id": user_id,
                "company_id": company_id,
                "priority": priority,
                "message": "우선순위가 업데이트되었습니다."
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"우선순위 업데이트 실패: {str(e)}")
            return {"error": str(e)}
    
    def _update_following_cache(self, user_id: str):
        """팔로잉 캐시를 업데이트합니다."""
        try:
            # 팔로잉 기업 ID 목록 조회
            following_ids = self.db.query(UserFollowing.company_id).filter(
                UserFollowing.user_id == user_id
            ).all()
            
            # Redis에 저장
            cache_key = f"following:{user_id}"
            self.redis_client.delete(cache_key)
            
            if following_ids:
                company_ids = [str(company_id[0]) for company_id in following_ids]
                self.redis_client.sadd(cache_key, *company_ids)
                self.redis_client.expire(cache_key, 3600)  # 1시간 TTL
            
        except Exception as e:
            logger.error(f"팔로잉 캐시 업데이트 실패: {str(e)}")
    
    def get_notification_settings(self, user_id: str) -> Dict[str, Any]:
        """
        알림 설정을 조회합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
            
        Returns
        -------
        Dict[str, Any]
            알림 설정 정보
        """
        try:
            # 사용자 정보 조회
            user = self.db.query(User).filter(User.google_id == user_id).first()
            if not user:
                return {"error": "사용자를 찾을 수 없습니다."}
            
            # 알림 설정 조회
            notification_settings = user.notification_settings or {}
            
            # 기본 알림 설정
            default_notifications = {
                "email_notifications": True,
                "push_notifications": True,
                "newsletter": False,
                "market_alerts": True,
                "company_mentions": True,
                "price_alerts": False,
                "news_digest": True,
                "digest_frequency": "daily",  # daily, weekly, monthly
                "digest_time": "09:00",
                "quiet_hours": {
                    "enabled": False,
                    "start_time": "22:00",
                    "end_time": "08:00"
                }
            }
            
            # 사용자 설정과 기본값 병합
            merged_settings = self._merge_preferences(default_notifications, notification_settings)
            
            return {
                "user_id": user_id,
                "notification_settings": merged_settings,
                "last_updated": user.updated_at.isoformat() if user.updated_at else None,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"알림 설정 조회 실패: {str(e)}")
            return {"error": str(e)}
    
    def update_notification_settings(self, user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        알림 설정을 업데이트합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
        settings : Dict[str, Any]
            업데이트할 알림 설정
            
        Returns
        -------
        Dict[str, Any]
            업데이트 결과
        """
        try:
            # 사용자 정보 조회
            user = self.db.query(User).filter(User.google_id == user_id).first()
            if not user:
                return {"error": "사용자를 찾을 수 없습니다."}
            
            # 기존 설정과 병합
            current_settings = user.notification_settings or {}
            updated_settings = self._merge_preferences(current_settings, settings)
            
            # 데이터베이스 업데이트
            user.notification_settings = updated_settings
            user.updated_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "user_id": user_id,
                "notification_settings": updated_settings,
                "updated_at": user.updated_at.isoformat(),
                "message": "알림 설정이 업데이트되었습니다."
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"알림 설정 업데이트 실패: {str(e)}")
            return {"error": str(e)}
    
    def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 대시보드 데이터를 조회합니다.
        
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
            # 사용자 정보 조회
            user = self.db.query(User).filter(User.google_id == user_id).first()
            if not user:
                return {"error": "사용자를 찾을 수 없습니다."}
            
            # 팔로잉 기업 수
            following_count = self.db.query(UserFollowing).filter(
                UserFollowing.user_id == user_id
            ).count()
            
            # 최근 활동 (최근 7일)
            recent_activity = self.db.query(UserFollowing).filter(
                and_(
                    UserFollowing.user_id == user_id,
                    UserFollowing.created_at >= datetime.utcnow() - timedelta(days=7)
                )
            ).count()
            
            # 사용자 설정
            preferences = self.get_user_preferences(user_id)
            notification_settings = self.get_notification_settings(user_id)
            
            return {
                "user_id": user_id,
                "user_name": user.name,
                "user_email": user.email,
                "user_picture": user.picture,
                "following_count": following_count,
                "recent_activity": recent_activity,
                "preferences": preferences.get("preferences", {}),
                "notification_settings": notification_settings.get("notification_settings", {}),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat(),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"사용자 대시보드 데이터 조회 실패: {str(e)}")
            return {"error": str(e)}
