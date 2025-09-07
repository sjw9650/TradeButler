#!/usr/bin/env python3
"""
AI 요약 및 기업 정보 추출 API

수집된 뉴스를 AI로 분석하여 요약, 태그, 기업 정보를 추출합니다.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ...repo.content import ContentRepo
from ...repo.db import SessionLocal
from ...workers.tasks import summarize_task

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/summaries", summary="AI 요약 목록 조회")
def get_summaries(
    limit: int = Query(20, ge=1, le=100, description="조회할 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    source: Optional[str] = Query(None, description="소스 필터"),
    keyword: Optional[str] = Query(None, description="키워드 검색"),
    has_ai_summary: bool = Query(True, description="AI 요약이 있는 것만")
) -> Dict[str, Any]:
    """
    AI 요약된 뉴스 목록을 조회합니다.
    
    Parameters
    ----------
    limit : int
        조회할 개수 (1-100)
    offset : int
        오프셋
    source : Optional[str]
        소스 필터 (rss:hankyung_economy 등)
    keyword : Optional[str]
        키워드 검색
    has_ai_summary : bool
        AI 요약이 있는 것만 조회
        
    Returns
    -------
    Dict[str, Any]
        요약 목록과 메타데이터
    """
    try:
        db = SessionLocal()
        repo = ContentRepo(db)
        
        # 콘텐츠 조회
        contents = repo.list_contents(
            tags=[source] if source else None,
            limit=limit,
            offset=offset,
            keyword=keyword
        )
        
        # AI 요약이 있는 것만 필터링
        if has_ai_summary:
            contents = [c for c in contents if c.insight and c.summary_bullets]
        
        # 응답 데이터 구성
        summaries = []
        for content in contents:
            summaries.append({
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
                "created_at": content.published_at.isoformat() if content.published_at else None
            })
        
        db.close()
        
        return {
            "summaries": summaries,
            "total": len(summaries),
            "limit": limit,
            "offset": offset,
            "has_more": len(contents) == limit
        }
        
    except Exception as e:
        logger.error(f"요약 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"요약 목록 조회 실패: {str(e)}")


@router.get("/summaries/{content_id}", summary="특정 뉴스 AI 요약 조회")
def get_summary(content_id: int) -> Dict[str, Any]:
    """
    특정 뉴스의 AI 요약을 조회합니다.
    
    Parameters
    ----------
    content_id : int
        콘텐츠 ID
        
    Returns
    -------
    Dict[str, Any]
        AI 요약 정보
    """
    try:
        db = SessionLocal()
        repo = ContentRepo(db)
        
        content = repo.get_by_id(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다")
        
        db.close()
        
        return {
            "id": content.id,
            "title": content.title,
            "author": content.author,
            "url": content.url,
            "source": content.source,
            "published_at": content.published_at.isoformat() if content.published_at else None,
            "raw_text": content.raw_text,
            "summary_bullets": content.summary_bullets,
            "insight": content.insight,
            "tags": content.tags,
            "lang": content.lang,
            "created_at": content.published_at.isoformat() if content.published_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"요약 조회 실패: {str(e)}")


@router.post("/summaries/{content_id}/regenerate", summary="AI 요약 재생성")
def regenerate_summary(content_id: int) -> Dict[str, Any]:
    """
    특정 뉴스의 AI 요약을 재생성합니다.
    
    Parameters
    ----------
    content_id : int
        콘텐츠 ID
        
    Returns
    -------
    Dict[str, Any]
        재생성 요청 결과
    """
    try:
        db = SessionLocal()
        repo = ContentRepo(db)
        
        content = repo.get_by_id(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다")
        
        # AI 요약 태스크 큐잉
        task = summarize_task.delay(content_id)
        
        db.close()
        
        return {
            "status": "queued",
            "task_id": task.id,
            "message": f"콘텐츠 ID {content_id}의 AI 요약 재생성이 시작되었습니다.",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"요약 재생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"요약 재생성 실패: {str(e)}")


@router.get("/companies", summary="기업 정보 목록 조회")
def get_companies(
    limit: int = Query(20, ge=1, le=100, description="조회할 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    keyword: Optional[str] = Query(None, description="기업명 검색")
) -> Dict[str, Any]:
    """
    뉴스에서 추출된 기업 정보 목록을 조회합니다.
    
    Parameters
    ----------
    limit : int
        조회할 개수
    offset : int
        오프셋
    keyword : Optional[str]
        기업명 검색
        
    Returns
    -------
    Dict[str, Any]
        기업 정보 목록
    """
    try:
        db = SessionLocal()
        repo = ContentRepo(db)
        
        # 태그에서 기업 관련 키워드 추출 (간단한 구현)
        contents = repo.list_contents(tags=None, limit=1000, offset=0)
        
        # 기업명 추출 (실제로는 더 정교한 NLP 처리가 필요)
        companies = {}
        for content in contents:
            if content.tags:
                for tag in content.tags:
                    # 대문자로 시작하는 태그를 기업명으로 간주
                    if tag and tag[0].isupper() and len(tag) > 2:
                        if tag not in companies:
                            companies[tag] = {
                                "name": tag,
                                "mention_count": 0,
                                "latest_news": None,
                                "related_tags": set()
                            }
                        companies[tag]["mention_count"] += 1
                        companies[tag]["related_tags"].update(content.tags)
                        
                        # 최신 뉴스 업데이트
                        if not companies[tag]["latest_news"] or \
                           (content.published_at and companies[tag]["latest_news"]["published_at"] < content.published_at):
                            companies[tag]["latest_news"] = {
                                "id": content.id,
                                "title": content.title,
                                "published_at": content.published_at.isoformat() if content.published_at else None
                            }
        
        # 키워드 필터링
        if keyword:
            companies = {k: v for k, v in companies.items() if keyword.lower() in k.lower()}
        
        # 정렬 (언급 횟수 기준)
        sorted_companies = sorted(companies.values(), key=lambda x: x["mention_count"], reverse=True)
        
        # 관련 태그를 리스트로 변환
        for company in sorted_companies:
            company["related_tags"] = list(company["related_tags"])
        
        # 페이지네이션
        total = len(sorted_companies)
        companies_page = sorted_companies[offset:offset + limit]
        
        db.close()
        
        return {
            "companies": companies_page,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
        
    except Exception as e:
        logger.error(f"기업 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기업 정보 조회 실패: {str(e)}")


@router.get("/companies/{company_name}/news", summary="특정 기업 관련 뉴스 조회")
def get_company_news(
    company_name: str,
    limit: int = Query(20, ge=1, le=100, description="조회할 개수"),
    offset: int = Query(0, ge=0, description="오프셋")
) -> Dict[str, Any]:
    """
    특정 기업과 관련된 뉴스를 조회합니다.
    
    Parameters
    ----------
    company_name : str
        기업명
    limit : int
        조회할 개수
    offset : int
        오프셋
        
    Returns
    -------
    Dict[str, Any]
        기업 관련 뉴스 목록
    """
    try:
        db = SessionLocal()
        repo = ContentRepo(db)
        
        # 기업명으로 키워드 검색
        contents = repo.list_contents(
            tags=None,
            limit=limit,
            offset=offset,
            keyword=company_name
        )
        
        # 응답 데이터 구성
        news = []
        for content in contents:
            news.append({
                "id": content.id,
                "title": content.title,
                "author": content.author,
                "url": content.url,
                "source": content.source,
                "published_at": content.published_at.isoformat() if content.published_at else None,
                "summary_bullets": content.summary_bullets,
                "insight": content.insight,
                "tags": content.tags,
                "lang": content.lang
            })
        
        db.close()
        
        return {
            "company_name": company_name,
            "news": news,
            "total": len(news),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"기업 뉴스 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기업 뉴스 조회 실패: {str(e)}")


@router.get("/stats", summary="AI 분석 통계")
def get_ai_stats() -> Dict[str, Any]:
    """
    AI 분석 통계를 조회합니다.
    
    Returns
    -------
    Dict[str, Any]
        AI 분석 통계
    """
    try:
        db = SessionLocal()
        repo = ContentRepo(db)
        
        # 전체 콘텐츠 수
        all_contents = repo.list_contents(tags=None, limit=10000, offset=0)
        total_contents = len(all_contents)
        
        # AI 요약이 있는 콘텐츠 수
        ai_summarized = len([c for c in all_contents if c.insight and c.summary_bullets])
        
        # 소스별 통계
        source_stats = {}
        for content in all_contents:
            source = content.source
            if source not in source_stats:
                source_stats[source] = {
                    "total": 0,
                    "ai_summarized": 0
                }
            source_stats[source]["total"] += 1
            if content.insight and content.summary_bullets:
                source_stats[source]["ai_summarized"] += 1
        
        # 언어별 통계
        lang_stats = {}
        for content in all_contents:
            lang = content.lang or "unknown"
            if lang not in lang_stats:
                lang_stats[lang] = 0
            lang_stats[lang] += 1
        
        db.close()
        
        return {
            "total_contents": total_contents,
            "ai_summarized": ai_summarized,
            "ai_summary_rate": round(ai_summarized / total_contents * 100, 2) if total_contents > 0 else 0,
            "source_stats": source_stats,
            "language_stats": lang_stats,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI 통계 조회 실패: {str(e)}")
