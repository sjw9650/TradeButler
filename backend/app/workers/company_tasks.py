#!/usr/bin/env python3
"""
기업 추출 관련 Celery 태스크

1단계: 수집된 뉴스에서 기업명 추출
2단계: 팔로잉 기업 관련 뉴스만 AI 요약
"""

from celery import shared_task
from datetime import datetime
from typing import Dict, Any, List
import logging

from ..repo.db import SessionLocal
from ..services.company_extractor import process_all_pending_companies, extract_companies_from_content
# from ..services.company_summarizer import summarize_following_companies  # TODO: 구현 예정
from ..models.company import Company, UserFollowing, CompanyMention
from ..models.content import Content

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="extract_companies_from_content")
def extract_companies_from_content_task(self, content_id: int) -> Dict[str, Any]:
    """
    특정 콘텐츠에서 기업명 추출
    
    Parameters
    ----------
    content_id : int
        콘텐츠 ID
        
    Returns
    -------
    Dict[str, Any]
        추출 결과
    """
    task_id = self.request.id
    logger.info(f"기업 추출 시작 - Content ID: {content_id}, Task ID: {task_id}")
    
    try:
        db = SessionLocal()
        result = extract_companies_from_content(content_id, db)
        db.close()
        
        logger.info(f"기업 추출 완료 - Content ID: {content_id}, Task ID: {task_id}")
        
        return {
            "task_id": task_id,
            "content_id": content_id,
            "status": "success",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"기업 추출 실패 - Content ID: {content_id}, Task ID: {task_id}, Error: {str(e)}")
        
        return {
            "task_id": task_id,
            "content_id": content_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="process_all_pending_companies")
def process_all_pending_companies_task(self) -> Dict[str, Any]:
    """
    처리되지 않은 모든 콘텐츠에서 기업명 추출
    
    Returns
    -------
    Dict[str, Any]
        처리 결과
    """
    task_id = self.request.id
    logger.info(f"일괄 기업 추출 시작 - Task ID: {task_id}")
    
    try:
        db = SessionLocal()
        result = process_all_pending_companies(db)
        db.close()
        
        logger.info(f"일괄 기업 추출 완료 - Task ID: {task_id}, Result: {result}")
        
        return {
            "task_id": task_id,
            "status": "success",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"일괄 기업 추출 실패 - Task ID: {task_id}, Error: {str(e)}")
        
        return {
            "task_id": task_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# @shared_task(bind=True, name="summarize_following_companies")
# def summarize_following_companies_task(self, user_id: str) -> Dict[str, Any]:
#     """
#     사용자가 팔로잉하는 기업 관련 뉴스 요약
#     
#     Parameters
#     ----------
#     user_id : str
#         사용자 ID
#         
#     Returns
#     -------
#     Dict[str, Any]
#         요약 결과
#     """
#     # TODO: 구현 예정
#     pass


@shared_task(bind=True, name="update_company_statistics")
def update_company_statistics_task(self) -> Dict[str, Any]:
    """
    기업 통계 정보 업데이트
    
    Returns
    -------
    Dict[str, Any]
        업데이트 결과
    """
    task_id = self.request.id
    logger.info(f"기업 통계 업데이트 시작 - Task ID: {task_id}")
    
    try:
        db = SessionLocal()
        
        # 각 기업별 통계 업데이트
        companies = db.query(Company).all()
        updated_count = 0
        
        for company in companies:
            # 언급 횟수 업데이트
            mention_count = db.query(CompanyMention).filter(
                CompanyMention.company_id == company.id
            ).count()
            
            company.total_mentions = mention_count
            
            # 마지막 언급일 업데이트
            last_mention = db.query(CompanyMention).filter(
                CompanyMention.company_id == company.id
            ).order_by(CompanyMention.created_at.desc()).first()
            
            if last_mention:
                company.last_mentioned_at = last_mention.created_at
            
            updated_count += 1
        
        db.commit()
        db.close()
        
        logger.info(f"기업 통계 업데이트 완료 - Task ID: {task_id}, Updated: {updated_count}")
        
        return {
            "task_id": task_id,
            "status": "success",
            "updated_companies": updated_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"기업 통계 업데이트 실패 - Task ID: {task_id}, Error: {str(e)}")
        
        return {
            "task_id": task_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(bind=True, name="cleanup_old_mentions")
def cleanup_old_mentions_task(self, days: int = 30) -> Dict[str, Any]:
    """
    오래된 기업 언급 데이터 정리
    
    Parameters
    ----------
    days : int
        보관 기간 (일)
        
    Returns
    -------
    Dict[str, Any]
        정리 결과
    """
    task_id = self.request.id
    logger.info(f"오래된 언급 데이터 정리 시작 - Days: {days}, Task ID: {task_id}")
    
    try:
        from datetime import timedelta
        
        db = SessionLocal()
        
        # 오래된 언급 데이터 삭제
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_mentions = db.query(CompanyMention).filter(
            CompanyMention.created_at < cutoff_date
        ).delete()
        
        db.commit()
        db.close()
        
        logger.info(f"오래된 언급 데이터 정리 완료 - Task ID: {task_id}, Deleted: {deleted_mentions}")
        
        return {
            "task_id": task_id,
            "status": "success",
            "deleted_mentions": deleted_mentions,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"오래된 언급 데이터 정리 실패 - Task ID: {task_id}, Error: {str(e)}")
        
        return {
            "task_id": task_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
