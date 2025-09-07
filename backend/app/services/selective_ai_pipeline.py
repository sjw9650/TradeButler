#!/usr/bin/env python3
"""
선택적 AI 파이프라인

팔로잉 기업 관련 뉴스만 자동으로 AI 요약하고, 나머지는 온디맨드로 처리
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ..models.content import Content
from ..models.company import Company, UserFollowing, CompanyMention
from ..services.company_matcher import CompanyMatcher
from ..workers.tasks import summarize_task

logger = logging.getLogger(__name__)


class SelectiveAIPipeline:
    """선택적 AI 파이프라인 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.matcher = CompanyMatcher(db)
    
    def process_new_content(self, content_id: int, user_id: str = "default_user") -> Dict[str, Any]:
        """
        새로운 콘텐츠를 선택적 AI 파이프라인으로 처리합니다.
        
        Parameters
        ----------
        content_id : int
            콘텐츠 ID
        user_id : str
            사용자 ID
            
        Returns
        -------
        Dict[str, Any]
            처리 결과
        """
        try:
            # 기업 매칭 확인
            match_result = self.matcher.should_auto_summarize(content_id, user_id)
            
            if match_result["should_summarize"]:
                # 자동 요약 실행
                return self._auto_summarize(content_id, match_result)
            else:
                # 온디맨드 대기 상태로 설정
                return self._mark_for_on_demand(content_id, match_result)
                
        except Exception as e:
            logger.error(f"선택적 AI 파이프라인 처리 실패 (콘텐츠 {content_id}): {str(e)}")
            return {
                "content_id": content_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _auto_summarize(self, content_id: int, match_result: Dict[str, Any]) -> Dict[str, Any]:
        """자동 요약을 실행합니다."""
        try:
            # AI 요약 태스크 실행
            task_result = summarize_task(content_id)
            
            # 콘텐츠 태그 업데이트
            content = self.db.query(Content).filter(Content.id == content_id).first()
            if content:
                if "pending_summary" in (content.tags or []):
                    content.tags = [tag for tag in (content.tags or []) if tag != "pending_summary"]
                content.tags.append("auto_summarized")
                content.tags.append("following_company")
                self.db.commit()
            
            return {
                "content_id": content_id,
                "status": "auto_summarized",
                "task_result": task_result,
                "matched_companies": match_result["matched_companies"],
                "matched_company_info": match_result["matched_company_info"],
                "reason": match_result["reason"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"자동 요약 실패 (콘텐츠 {content_id}): {str(e)}")
            return {
                "content_id": content_id,
                "status": "auto_summarize_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _mark_for_on_demand(self, content_id: int, match_result: Dict[str, Any]) -> Dict[str, Any]:
        """온디맨드 대기 상태로 설정합니다."""
        try:
            # 콘텐츠 태그 업데이트
            content = self.db.query(Content).filter(Content.id == content_id).first()
            if content:
                if "pending_summary" in (content.tags or []):
                    content.tags = [tag for tag in (content.tags or []) if tag != "pending_summary"]
                content.tags.append("on_demand_available")
                self.db.commit()
            
            return {
                "content_id": content_id,
                "status": "on_demand_available",
                "matched_companies": match_result["matched_companies"],
                "reason": match_result["reason"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"온디맨드 설정 실패 (콘텐츠 {content_id}): {str(e)}")
            return {
                "content_id": content_id,
                "status": "on_demand_setup_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def process_batch_content(self, user_id: str = "default_user", limit: int = 50) -> Dict[str, Any]:
        """
        배치로 콘텐츠를 처리합니다.
        
        Parameters
        ----------
        user_id : str
            사용자 ID
        limit : int
            처리할 최대 개수
            
        Returns
        -------
        Dict[str, Any]
            배치 처리 결과
        """
        try:
            # 처리할 콘텐츠 조회
            contents = self.db.query(Content).filter(
                Content.tags.contains(["pending_summary"])
            ).limit(limit).all()
            
            results = {
                "processed": 0,
                "auto_summarized": 0,
                "on_demand_available": 0,
                "errors": 0,
                "details": []
            }
            
            for content in contents:
                try:
                    result = self.process_new_content(content.id, user_id)
                    results["processed"] += 1
                    results["details"].append(result)
                    
                    if result["status"] == "auto_summarized":
                        results["auto_summarized"] += 1
                    elif result["status"] == "on_demand_available":
                        results["on_demand_available"] += 1
                    elif "error" in result["status"]:
                        results["errors"] += 1
                        
                except Exception as e:
                    logger.error(f"콘텐츠 {content.id} 처리 실패: {str(e)}")
                    results["errors"] += 1
                    results["details"].append({
                        "content_id": content.id,
                        "status": "error",
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"배치 처리 실패: {str(e)}")
            return {
                "processed": 0,
                "auto_summarized": 0,
                "on_demand_available": 0,
                "errors": 1,
                "details": [{"error": str(e)}]
            }
    
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
            # 기본 통계
            stats = self.matcher.get_user_summary_stats(user_id)
            
            # 우선순위 콘텐츠
            priority_content = self.matcher.get_priority_content(user_id, limit=10)
            
            # 최근 자동 요약된 콘텐츠
            recent_auto_summarized = self.db.query(Content).join(
                CompanyMention, Content.id == CompanyMention.content_id
            ).filter(
                Content.tags.contains(["auto_summarized"]),
                Content.insight.isnot(None)
            ).order_by(Content.published_at.desc()).limit(5).all()
            
            recent_summaries = []
            for content in recent_auto_summarized:
                recent_summaries.append({
                    "id": content.id,
                    "title": content.title,
                    "source": content.source,
                    "published_at": content.published_at.isoformat() if content.published_at else None,
                    "summary_bullets": content.summary_bullets,
                    "insight": content.insight,
                    "tags": content.tags
                })
            
            return {
                "stats": stats,
                "priority_content": priority_content,
                "recent_summaries": recent_summaries,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"대시보드 데이터 조회 실패 (사용자 {user_id}): {str(e)}")
            return {
                "stats": {},
                "priority_content": [],
                "recent_summaries": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def trigger_on_demand_summary(self, content_id: int, user_id: str = "default_user") -> Dict[str, Any]:
        """
        온디맨드 요약을 실행합니다.
        
        Parameters
        ----------
        content_id : int
            콘텐츠 ID
        user_id : str
            사용자 ID
            
        Returns
        -------
        Dict[str, Any]
            요약 결과
        """
        try:
            # 콘텐츠 확인
            content = self.db.query(Content).filter(Content.id == content_id).first()
            if not content:
                return {
                    "content_id": content_id,
                    "status": "error",
                    "error": "콘텐츠를 찾을 수 없습니다"
                }
            
            # 이미 요약된 경우
            if content.insight and content.summary_bullets:
                return {
                    "content_id": content_id,
                    "status": "already_summarized",
                    "summary_bullets": content.summary_bullets,
                    "insight": content.insight
                }
            
            # AI 요약 실행
            task_result = summarize_task(content_id)
            
            # 태그 업데이트
            if "on_demand_available" in (content.tags or []):
                content.tags = [tag for tag in (content.tags or []) if tag != "on_demand_available"]
            content.tags.append("on_demand_summarized")
            self.db.commit()
            
            return {
                "content_id": content_id,
                "status": "on_demand_summarized",
                "task_result": task_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"온디맨드 요약 실패 (콘텐츠 {content_id}): {str(e)}")
            return {
                "content_id": content_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


def process_content_with_selective_ai(content_id: int, user_id: str, db: Session) -> Dict[str, Any]:
    """
    선택적 AI로 콘텐츠를 처리합니다. (외부 호출용)
    
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
        처리 결과
    """
    pipeline = SelectiveAIPipeline(db)
    return pipeline.process_new_content(content_id, user_id)


def process_batch_with_selective_ai(user_id: str, limit: int, db: Session) -> Dict[str, Any]:
    """
    선택적 AI로 배치를 처리합니다. (외부 호출용)
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    limit : int
        처리할 최대 개수
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        배치 처리 결과
    """
    pipeline = SelectiveAIPipeline(db)
    return pipeline.process_batch_content(user_id, limit)
