#!/usr/bin/env python3
"""
기업 관련 데이터베이스 리포지토리

기업 추출, 팔로잉, 분석 관련 데이터베이스 작업을 처리합니다.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..models.company import Company, UserFollowing, CompanyMention, CompanySummary, CompanyTrend
from ..models.content import Content


class CompanyRepo:
    """기업 관련 데이터베이스 리포지토리"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def list_companies(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        industry: Optional[str] = None,
        sort_by: str = "mentions"
    ) -> List[Company]:
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
        List[Company]
            기업 목록
        """
        query = self.db.query(Company).filter(Company.is_active == True)
        
        # 검색 조건
        if search:
            query = query.filter(
                or_(
                    Company.name.ilike(f"%{search}%"),
                    Company.display_name.ilike(f"%{search}%"),
                    Company.aliases.contains([search])
                )
            )
        
        # 업종 필터
        if industry:
            query = query.filter(Company.industry == industry)
        
        # 정렬
        if sort_by == "mentions":
            query = query.order_by(desc(Company.total_mentions))
        elif sort_by == "name":
            query = query.order_by(asc(Company.name))
        elif sort_by == "created":
            query = query.order_by(desc(Company.created_at))
        
        return query.offset(offset).limit(limit).all()
    
    def count_companies(
        self,
        search: Optional[str] = None,
        industry: Optional[str] = None
    ) -> int:
        """
        기업 수를 조회합니다.
        
        Parameters
        ----------
        search : Optional[str]
            기업명 검색
        industry : Optional[str]
            업종 필터
            
        Returns
        -------
        int
            기업 수
        """
        query = self.db.query(Company).filter(Company.is_active == True)
        
        if search:
            query = query.filter(
                or_(
                    Company.name.ilike(f"%{search}%"),
                    Company.display_name.ilike(f"%{search}%"),
                    Company.aliases.contains([search])
                )
            )
        
        if industry:
            query = query.filter(Company.industry == industry)
        
        return query.count()
    
    def get_by_id(self, company_id: int) -> Optional[Company]:
        """
        ID로 기업을 조회합니다.
        
        Parameters
        ----------
        company_id : int
            기업 ID
            
        Returns
        -------
        Optional[Company]
            기업 객체 또는 None
        """
        return self.db.query(Company).filter(Company.id == company_id).first()
    
    def get_by_name(self, name: str) -> Optional[Company]:
        """
        이름으로 기업을 조회합니다.
        
        Parameters
        ----------
        name : str
            기업명
            
        Returns
        -------
        Optional[Company]
            기업 객체 또는 None
        """
        return self.db.query(Company).filter(Company.name == name).first()
    
    def create_company(self, **kwargs) -> Company:
        """
        새 기업을 생성합니다.
        
        Parameters
        ----------
        **kwargs
            기업 속성
            
        Returns
        -------
        Company
            생성된 기업 객체
        """
        company = Company(**kwargs)
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company
    
    def update_company(self, company_id: int, **kwargs) -> Optional[Company]:
        """
        기업 정보를 업데이트합니다.
        
        Parameters
        ----------
        company_id : int
            기업 ID
        **kwargs
            업데이트할 속성
            
        Returns
        -------
        Optional[Company]
            업데이트된 기업 객체 또는 None
        """
        company = self.get_by_id(company_id)
        if not company:
            return None
        
        for key, value in kwargs.items():
            setattr(company, key, value)
        
        company.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(company)
        return company
    
    def get_recent_mentions(self, company_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        기업의 최근 언급을 조회합니다.
        
        Parameters
        ----------
        company_id : int
            기업 ID
        limit : int
            조회할 개수
            
        Returns
        -------
        List[Dict[str, Any]]
            언급 목록
        """
        mentions = self.db.query(CompanyMention).filter(
            CompanyMention.company_id == company_id
        ).order_by(desc(CompanyMention.created_at)).limit(limit).all()
        
        result = []
        for mention in mentions:
            result.append({
                "id": mention.id,
                "content_id": mention.content_id,
                "mention_text": mention.mention_text,
                "mention_context": mention.mention_context,
                "sentiment": mention.sentiment,
                "relevance_score": mention.relevance_score,
                "confidence_score": mention.confidence_score,
                "created_at": mention.created_at.isoformat()
            })
        
        return result
    
    def get_sentiment_stats(self, company_id: int) -> Dict[str, Any]:
        """
        기업의 감정 분석 통계를 조회합니다.
        
        Parameters
        ----------
        company_id : int
            기업 ID
            
        Returns
        -------
        Dict[str, Any]
            감정 분석 통계
        """
        # 감정별 언급 수
        sentiment_counts = self.db.query(
            CompanyMention.sentiment,
            func.count(CompanyMention.id).label('count')
        ).filter(
            CompanyMention.company_id == company_id
        ).group_by(CompanyMention.sentiment).all()
        
        stats = {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "total": 0
        }
        
        for sentiment, count in sentiment_counts:
            if sentiment in stats:
                stats[sentiment] = count
            stats["total"] += count
        
        # 평균 관련도 점수
        avg_relevance = self.db.query(
            func.avg(CompanyMention.relevance_score)
        ).filter(
            CompanyMention.company_id == company_id
        ).scalar() or 0
        
        stats["avg_relevance_score"] = round(avg_relevance, 3)
        
        return stats
    
    def get_company_news(
        self,
        company_id: int,
        limit: int = 20,
        offset: int = 0,
        sentiment: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        기업 관련 뉴스를 조회합니다.
        
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
        List[Dict[str, Any]]
            뉴스 목록
        """
        query = self.db.query(Content).join(
            CompanyMention, Content.id == CompanyMention.content_id
        ).filter(CompanyMention.company_id == company_id)
        
        if sentiment:
            query = query.filter(CompanyMention.sentiment == sentiment)
        
        contents = query.order_by(desc(Content.published_at)).offset(offset).limit(limit).all()
        
        result = []
        for content in contents:
            # 해당 기업의 언급 정보
            mention = self.db.query(CompanyMention).filter(
                and_(
                    CompanyMention.company_id == company_id,
                    CompanyMention.content_id == content.id
                )
            ).first()
            
            result.append({
                "id": content.id,
                "title": content.title,
                "author": content.author,
                "url": content.url,
                "source": content.source,
                "published_at": content.published_at.isoformat() if content.published_at else None,
                "summary_bullets": content.summary_bullets,
                "insight": content.insight,
                "tags": content.tags,
                "lang": content.lang,
                "mention_sentiment": mention.sentiment if mention else None,
                "mention_relevance": mention.relevance_score if mention else None,
                "mention_confidence": mention.confidence_score if mention else None
            })
        
        return result
    
    def count_company_news(
        self,
        company_id: int,
        sentiment: Optional[str] = None
    ) -> int:
        """
        기업 관련 뉴스 수를 조회합니다.
        
        Parameters
        ----------
        company_id : int
            기업 ID
        sentiment : Optional[str]
            감정 필터
            
        Returns
        -------
        int
            뉴스 수
        """
        query = self.db.query(Content).join(
            CompanyMention, Content.id == CompanyMention.content_id
        ).filter(CompanyMention.company_id == company_id)
        
        if sentiment:
            query = query.filter(CompanyMention.sentiment == sentiment)
        
        return query.count()
    
    def create_user_following(
        self,
        user_id: str,
        company_id: int,
        priority: int = 1,
        notification_enabled: bool = True,
        auto_summarize: bool = True,
        **kwargs
    ) -> UserFollowing:
        """
        사용자 기업 팔로잉을 생성합니다.
        
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
        **kwargs
            추가 속성
            
        Returns
        -------
        UserFollowing
            생성된 팔로잉 객체
        """
        following = UserFollowing(
            user_id=user_id,
            company_id=company_id,
            priority=priority,
            notification_enabled=notification_enabled,
            auto_summarize=auto_summarize,
            **kwargs
        )
        
        self.db.add(following)
        self.db.commit()
        self.db.refresh(following)
        return following
    
    def get_user_following(self, user_id: str, company_id: int) -> Optional[UserFollowing]:
        """
        사용자의 특정 기업 팔로잉을 조회합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
        company_id : int
            기업 ID
            
        Returns
        -------
        Optional[UserFollowing]
            팔로잉 객체 또는 None
        """
        return self.db.query(UserFollowing).filter(
            and_(
                UserFollowing.user_id == user_id,
                UserFollowing.company_id == company_id
            )
        ).first()
    
    def get_user_following_list(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        사용자의 팔로잉 기업 목록을 조회합니다.
        
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
        List[Dict[str, Any]]
            팔로잉 기업 목록
        """
        followings = self.db.query(UserFollowing, Company).join(
            Company, UserFollowing.company_id == Company.id
        ).filter(
            UserFollowing.user_id == user_id
        ).order_by(desc(UserFollowing.priority), desc(Company.total_mentions)).offset(offset).limit(limit).all()
        
        result = []
        for following, company in followings:
            result.append({
                "following_id": following.id,
                "company_id": company.id,
                "company_name": company.name,
                "company_display_name": company.display_name,
                "industry": company.industry,
                "total_mentions": company.total_mentions,
                "last_mentioned_at": company.last_mentioned_at.isoformat() if company.last_mentioned_at else None,
                "priority": following.priority,
                "notification_enabled": following.notification_enabled,
                "auto_summarize": following.auto_summarize,
                "created_at": following.created_at.isoformat()
            })
        
        return result
    
    def count_user_following(self, user_id: str) -> int:
        """
        사용자의 팔로잉 기업 수를 조회합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
            
        Returns
        -------
        int
            팔로잉 기업 수
        """
        return self.db.query(UserFollowing).filter(UserFollowing.user_id == user_id).count()
    
    def delete_user_following(self, following_id: int) -> bool:
        """
        사용자 기업 팔로잉을 삭제합니다.
        
        Parameters
        ----------
        following_id : int
            팔로잉 ID
            
        Returns
        -------
        bool
            삭제 성공 여부
        """
        following = self.db.query(UserFollowing).filter(UserFollowing.id == following_id).first()
        if not following:
            return False
        
        self.db.delete(following)
        self.db.commit()
        return True
    
    def get_company_trends(
        self,
        company_id: Optional[int] = None,
        period: str = "weekly",
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        기업 트렌드를 조회합니다.
        
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
        List[Dict[str, Any]]
            트렌드 데이터
        """
        # 실제 구현에서는 CompanyTrend 테이블을 사용하지만,
        # 여기서는 CompanyMention을 기반으로 간단한 트렌드 생성
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(CompanyMention).filter(
            CompanyMention.created_at >= cutoff_date
        )
        
        if company_id:
            query = query.filter(CompanyMention.company_id == company_id)
        
        # 일별 그룹화
        if period == "daily":
            group_by = func.date(CompanyMention.created_at)
        elif period == "weekly":
            group_by = func.date_trunc('week', CompanyMention.created_at)
        else:  # monthly
            group_by = func.date_trunc('month', CompanyMention.created_at)
        
        trends = query.group_by(group_by).with_entities(
            group_by.label('date'),
            func.count(CompanyMention.id).label('mention_count'),
            func.avg(CompanyMention.relevance_score).label('avg_relevance'),
            func.avg(CompanyMention.confidence_score).label('avg_confidence')
        ).order_by(group_by).all()
        
        result = []
        for trend in trends:
            result.append({
                "date": trend.date.isoformat() if trend.date else None,
                "mention_count": trend.mention_count,
                "avg_relevance": round(trend.avg_relevance or 0, 3),
                "avg_confidence": round(trend.avg_confidence or 0, 3)
            })
        
        return result
    
    def get_companies_by_ids(self, company_ids: List[int]) -> List[Company]:
        """
        ID 목록으로 기업들을 조회합니다.
        
        Parameters
        ----------
        company_ids : List[int]
            기업 ID 목록
            
        Returns
        -------
        List[Company]
            기업 목록
        """
        if not company_ids:
            return []
        
        return self.db.query(Company).filter(Company.id.in_(company_ids)).all()
    
    def get_following_data_for_cache(self, user_id: str) -> Dict[int, Dict[str, Any]]:
        """
        캐시 동기화를 위한 팔로잉 데이터를 조회합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
            
        Returns
        -------
        Dict[int, Dict[str, Any]]
            팔로잉 데이터 (기업 ID -> 상세 정보)
        """
        following_records = self.db.query(UserFollowing).filter(
            UserFollowing.user_id == user_id
        ).all()
        
        following_data = {}
        for record in following_records:
            following_data[record.company_id] = {
                "priority": record.priority,
                "notification_enabled": record.notification_enabled,
                "auto_summarize": record.auto_summarize,
                "followed_at": record.created_at.isoformat()
            }
        
        return following_data
