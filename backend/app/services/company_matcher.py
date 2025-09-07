#!/usr/bin/env python3
"""
기업 매칭 엔진

팔로잉 기업과 뉴스에서 추출된 기업을 매칭하여 선택적 AI 처리 결정
"""

from typing import List, Dict, Any, Set, Optional
from sqlalchemy.orm import Session
from ..models.company import Company, UserFollowing, CompanyMention
from ..models.content import Content
import logging

logger = logging.getLogger(__name__)


class CompanyMatcher:
    """기업 매칭 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
    
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
        followings = self.db.query(UserFollowing).filter(
            UserFollowing.user_id == user_id,
            UserFollowing.auto_summarize == True  # 자동 요약 활성화된 것만
        ).all()
        
        return {following.company_id for following in followings}
    
    def get_content_companies(self, content_id: int) -> Set[int]:
        """
        콘텐츠에서 추출된 기업 ID 목록을 조회합니다.
        
        Parameters
        ----------
        content_id : int
            콘텐츠 ID
            
        Returns
        -------
        Set[int]
            추출된 기업 ID 목록
        """
        mentions = self.db.query(CompanyMention).filter(
            CompanyMention.content_id == content_id
        ).all()
        
        return {mention.company_id for mention in mentions}
    
    def should_auto_summarize(self, content_id: int, user_id: str) -> Dict[str, Any]:
        """
        콘텐츠를 자동으로 요약할지 결정합니다.
        
        Parameters
        ----------
        content_id : int
            콘텐츠 ID
        user_id : str
            사용자 ID
            
        Returns
        -------
        Dict[str, Any]
            매칭 결과 및 결정 사항
        """
        try:
            # 팔로잉 기업 조회
            following_companies = self.get_following_companies(user_id)
            
            # 콘텐츠 기업 조회
            content_companies = self.get_content_companies(content_id)
            
            # 교집합 계산
            matched_companies = following_companies.intersection(content_companies)
            
            # 매칭된 기업 정보 조회
            matched_company_info = []
            if matched_companies:
                companies = self.db.query(Company).filter(
                    Company.id.in_(matched_companies)
                ).all()
                
                matched_company_info = [
                    {
                        "id": company.id,
                        "name": company.name,
                        "industry": company.industry,
                        "priority": self._get_company_priority(user_id, company.id)
                    }
                    for company in companies
                ]
            
            # 자동 요약 여부 결정
            should_summarize = len(matched_companies) > 0
            
            # 우선순위 계산 (매칭된 기업의 최고 우선순위)
            max_priority = max(
                [info["priority"] for info in matched_company_info], 
                default=0
            ) if matched_company_info else 0
            
            return {
                "should_summarize": should_summarize,
                "matched_companies": list(matched_companies),
                "matched_company_info": matched_company_info,
                "total_following": len(following_companies),
                "total_content_companies": len(content_companies),
                "match_ratio": len(matched_companies) / len(content_companies) if content_companies else 0,
                "max_priority": max_priority,
                "reason": self._get_decision_reason(should_summarize, matched_companies, content_companies)
            }
            
        except Exception as e:
            logger.error(f"기업 매칭 실패 (콘텐츠 {content_id}, 사용자 {user_id}): {str(e)}")
            return {
                "should_summarize": False,
                "matched_companies": [],
                "matched_company_info": [],
                "total_following": 0,
                "total_content_companies": 0,
                "match_ratio": 0,
                "max_priority": 0,
                "reason": f"오류 발생: {str(e)}"
            }
    
    def _get_company_priority(self, user_id: str, company_id: int) -> int:
        """기업의 사용자별 우선순위를 조회합니다."""
        following = self.db.query(UserFollowing).filter(
            UserFollowing.user_id == user_id,
            UserFollowing.company_id == company_id
        ).first()
        
        return following.priority if following else 0
    
    def _get_decision_reason(self, should_summarize: bool, matched: Set[int], content_companies: Set[int]) -> str:
        """결정 이유를 설명합니다."""
        if should_summarize:
            return f"팔로잉 기업 {len(matched)}개가 언급됨 (총 {len(content_companies)}개 기업 중)"
        else:
            if not content_companies:
                return "언급된 기업이 없음"
            else:
                return f"팔로잉 기업이 언급되지 않음 (총 {len(content_companies)}개 기업 중)"
    
    def get_priority_content(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        사용자에게 우선순위가 높은 콘텐츠 목록을 조회합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
        limit : int
            조회할 개수
            
        Returns
        -------
        List[Dict[str, Any]]
            우선순위 콘텐츠 목록
        """
        try:
            # 팔로잉 기업 조회
            following_companies = self.get_following_companies(user_id)
            
            if not following_companies:
                return []
            
            # 매칭된 콘텐츠 조회
            contents = self.db.query(Content).join(
                CompanyMention, Content.id == CompanyMention.content_id
            ).filter(
                CompanyMention.company_id.in_(following_companies)
            ).distinct().limit(limit).all()
            
            priority_contents = []
            for content in contents:
                match_result = self.should_auto_summarize(content.id, user_id)
                
                priority_contents.append({
                    "content_id": content.id,
                    "title": content.title,
                    "source": content.source,
                    "published_at": content.published_at.isoformat() if content.published_at else None,
                    "matched_companies": match_result["matched_companies"],
                    "matched_company_info": match_result["matched_company_info"],
                    "max_priority": match_result["max_priority"],
                    "match_ratio": match_result["match_ratio"],
                    "has_ai_summary": bool(content.insight and content.summary_bullets)
                })
            
            # 우선순위별 정렬 (max_priority 내림차순, match_ratio 내림차순)
            priority_contents.sort(
                key=lambda x: (x["max_priority"], x["match_ratio"]), 
                reverse=True
            )
            
            return priority_contents
            
        except Exception as e:
            logger.error(f"우선순위 콘텐츠 조회 실패 (사용자 {user_id}): {str(e)}")
            return []
    
    def get_user_summary_stats(self, user_id: str) -> Dict[str, Any]:
        """
        사용자의 요약 통계를 조회합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
            
        Returns
        -------
        Dict[str, Any]
            요약 통계
        """
        try:
            following_companies = self.get_following_companies(user_id)
            
            if not following_companies:
                return {
                    "following_companies": 0,
                    "total_content": 0,
                    "matched_content": 0,
                    "auto_summarized": 0,
                    "pending_summary": 0,
                    "match_rate": 0
                }
            
            # 전체 콘텐츠 수
            total_content = self.db.query(Content).count()
            
            # 매칭된 콘텐츠 수
            matched_content = self.db.query(Content).join(
                CompanyMention, Content.id == CompanyMention.content_id
            ).filter(
                CompanyMention.company_id.in_(following_companies)
            ).distinct().count()
            
            # 자동 요약된 콘텐츠 수
            auto_summarized = self.db.query(Content).join(
                CompanyMention, Content.id == CompanyMention.content_id
            ).filter(
                CompanyMention.company_id.in_(following_companies),
                Content.insight.isnot(None),
                Content.summary_bullets.isnot(None)
            ).distinct().count()
            
            # 대기 중인 콘텐츠 수
            pending_summary = self.db.query(Content).join(
                CompanyMention, Content.id == CompanyMention.content_id
            ).filter(
                CompanyMention.company_id.in_(following_companies),
                Content.insight.is_(None)
            ).distinct().count()
            
            return {
                "following_companies": len(following_companies),
                "total_content": total_content,
                "matched_content": matched_content,
                "auto_summarized": auto_summarized,
                "pending_summary": pending_summary,
                "match_rate": matched_content / total_content if total_content > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"사용자 통계 조회 실패 (사용자 {user_id}): {str(e)}")
            return {
                "following_companies": 0,
                "total_content": 0,
                "matched_content": 0,
                "auto_summarized": 0,
                "pending_summary": 0,
                "match_rate": 0
            }


def should_auto_summarize_content(content_id: int, user_id: str, db: Session) -> Dict[str, Any]:
    """
    콘텐츠 자동 요약 여부를 결정합니다. (외부 호출용)
    
    Parameters
    ----------
    content_id : int
        콘텐츠 ID
    user_id : str
        사용자 ID
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        매칭 결과
    """
    matcher = CompanyMatcher(db)
    return matcher.should_auto_summarize(content_id, user_id)


def get_user_priority_content(user_id: str, limit: int, db: Session) -> List[Dict[str, Any]]:
    """
    사용자 우선순위 콘텐츠를 조회합니다. (외부 호출용)
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    limit : int
        조회할 개수
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    List[Dict[str, Any]]
        우선순위 콘텐츠 목록
    """
    matcher = CompanyMatcher(db)
    return matcher.get_priority_content(user_id, limit)
