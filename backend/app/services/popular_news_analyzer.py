#!/usr/bin/env python3
"""
인기 뉴스 분석 서비스

수집된 뉴스 중에서 인기 있는 기사 10개를 선별하고 AI 요약을 생성합니다.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from ..models.content import Content, AICache
from ..models.cost_log import CostLog
from ..utils.cost_calculator import calculate_openai_cost
from ..core.config import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

# OpenAI 클라이언트 설정
client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
MODEL_VERSION = "gpt-3.5-turbo"


class PopularNewsAnalyzer:
    """인기 뉴스 분석기"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_popular_news(self, limit: int = 10, hours: int = 24) -> List[Content]:
        """
        인기 뉴스 목록을 조회합니다.
        
        Parameters
        ----------
        limit : int
            조회할 개수 (기본값: 10)
        hours : int
            최근 몇 시간 내의 뉴스 (기본값: 24)
            
        Returns
        -------
        List[Content]
            인기 뉴스 목록
        """
        # 최근 24시간 내의 뉴스
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 인기도 점수 계산 (언급 횟수, 최신성, 소스 신뢰도 등)
        popular_news = self.db.query(Content).filter(
            and_(
                Content.published_at >= cutoff_time,
                Content.is_active == True
            )
        ).order_by(
            # 최신성 (최근 1시간 내는 가중치 2배)
            func.case(
                (Content.published_at >= datetime.utcnow() - timedelta(hours=1), 2),
                else_=1
            ) * func.extract('epoch', Content.published_at).desc(),
            # 제목 길이 (적절한 길이의 제목 선호)
            func.length(Content.title).desc(),
            # 소스별 가중치
            func.case(
                (Content.source.like('%hankyung%'), 1.5),
                (Content.source.like('%yahoo%'), 1.2),
                (Content.source.like('%coindesk%'), 1.1),
                else_=1.0
            ).desc()
        ).limit(limit).all()
        
        return popular_news
    
    def analyze_popularity_score(self, content: Content) -> float:
        """
        뉴스의 인기도 점수를 계산합니다. (소셜 미디어 메트릭 기반)
        
        Parameters
        ----------
        content : Content
            뉴스 콘텐츠
            
        Returns
        -------
        float
            인기도 점수 (0-100)
        """
        score = 0.0
        
        # 1. 소셜 미디어 참여도 (가장 중요) - 50점
        engagement_score = self._calculate_engagement_score(content)
        score += engagement_score
        
        # 2. 조회수 기반 점수 - 25점
        view_score = self._calculate_view_score(content.view_count or 0)
        score += view_score
        
        # 3. 시간 가중치 (최신성) - 15점
        time_score = self._calculate_time_score(content.published_at)
        score += time_score
        
        # 4. 소스 신뢰도 - 10점
        source_score = self._calculate_source_score(content.source)
        score += source_score
        
        return min(score, 100.0)  # 최대 100점
    
    def _calculate_engagement_score(self, content: Content) -> float:
        """참여도 점수 계산 (50점 만점)"""
        if not content.view_count or content.view_count == 0:
            return 0.0
        
        # 참여율 계산: (좋아요 + 공유 + 댓글) / 조회수
        total_engagement = (content.like_count or 0) + (content.share_count or 0) + (content.comment_count or 0)
        engagement_rate = total_engagement / content.view_count
        
        # 참여율에 따른 점수 계산
        if engagement_rate >= 0.1:  # 10% 이상 - 바이럴
            return 50.0
        elif engagement_rate >= 0.05:  # 5% 이상 - 높음
            return 40.0
        elif engagement_rate >= 0.02:  # 2% 이상 - 보통
            return 30.0
        elif engagement_rate >= 0.01:  # 1% 이상 - 낮음
            return 20.0
        else:
            return 10.0
    
    def _calculate_view_score(self, view_count: int) -> float:
        """조회수 기반 점수 계산 (25점 만점)"""
        if view_count == 0:
            return 0.0
        
        # 조회수 구간별 점수
        if view_count >= 10000:
            return 25.0  # 1만 이상
        elif view_count >= 5000:
            return 20.0  # 5천 이상
        elif view_count >= 2000:
            return 15.0  # 2천 이상
        elif view_count >= 1000:
            return 10.0  # 1천 이상
        elif view_count >= 500:
            return 5.0   # 5백 이상
        else:
            return 2.0   # 그 외
    
    def _calculate_time_score(self, published_at: datetime) -> float:
        """시간 가중치 점수 계산 (15점 만점)"""
        if not published_at:
            return 0.0
        
        hours_ago = (datetime.utcnow() - published_at).total_seconds() / 3600
        
        if hours_ago <= 1:
            return 15.0  # 최근 1시간 내
        elif hours_ago <= 6:
            return 12.0  # 최근 6시간 내
        elif hours_ago <= 24:
            return 8.0   # 최근 24시간 내
        elif hours_ago <= 72:
            return 4.0   # 최근 3일 내
        else:
            return 1.0   # 그 외
    
    def _calculate_source_score(self, source: str) -> float:
        """소스 신뢰도 점수 계산 (10점 만점)"""
        if not source:
            return 0.0
        
        source_lower = source.lower()
        
        if 'hankyung' in source_lower:
            return 10.0  # 한국경제
        elif 'yahoo' in source_lower:
            return 8.0   # Yahoo Finance
        elif 'coindesk' in source_lower:
            return 7.0   # CoinDesk
        elif 'bloomberg' in source_lower:
            return 9.0   # Bloomberg
        elif 'reuters' in source_lower:
            return 8.5   # Reuters
        else:
            return 5.0   # 기타
    
    def generate_ai_summary(self, content: Content) -> Dict[str, Any]:
        """
        뉴스에 대한 AI 요약을 생성합니다.
        
        Parameters
        ----------
        content : Content
            뉴스 콘텐츠
            
        Returns
        -------
        Dict[str, Any]
            AI 요약 결과
        """
        if not client:
            logger.error("OpenAI 클라이언트가 설정되지 않았습니다.")
            return {"error": "OpenAI 클라이언트 설정 오류"}
        
        try:
            # 기존 캐시 확인
            cached = self.db.query(AICache).filter_by(
                content_hash=content.hash,
                model_version=MODEL_VERSION
            ).first()
            
            if cached:
                logger.info(f"캐시된 결과 사용: {content.id}")
                return {
                    "status": "cached",
                    "summary_bullets": cached.summary_bullets,
                    "tags": cached.tags,
                    "insight": cached.insight
                }
            
            # AI 요약 생성
            prompt = f"""
다음 뉴스 기사를 분석하여 요약해주세요:

제목: {content.title}
내용: {content.content[:2000]}  # 처음 2000자만 사용
언어: {content.lang}
출처: {content.source}

다음 JSON 형식으로 응답해주세요:
{{
    "summary_bullets": [
        "핵심 내용 1",
        "핵심 내용 2", 
        "핵심 내용 3",
        "핵심 내용 4",
        "핵심 내용 5"
    ],
    "tags": ["태그1", "태그2", "태그3", "태그4", "태그5"],
    "insight": "이 뉴스가 시장에 미칠 영향과 투자 관점에서의 분석 (2-3문장)"
}}

주의사항:
- summary_bullets는 최대 5개까지
- tags는 관련 키워드 5개까지
- insight는 구체적이고 실용적인 분석
- JSON 형식으로만 응답
"""

            response = client.chat.completions.create(
                model=MODEL_VERSION,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            ai_data = eval(result) if isinstance(result, str) else result
            
            # 캐시 저장
            cache_entry = AICache(
                content_hash=content.hash,
                model_version=MODEL_VERSION,
                summary_bullets=ai_data.get("summary_bullets", []),
                tags=ai_data.get("tags", []),
                insight=ai_data.get("insight", ""),
                tokens_used=response.usage.total_tokens,
                cost=calculate_openai_cost(
                    model_name=MODEL_VERSION,
                    tokens_in=response.usage.prompt_tokens,
                    tokens_out=response.usage.completion_tokens
                )
            )
            
            self.db.add(cache_entry)
            
            # 비용 로깅
            cost_log = CostLog(
                model_name=MODEL_VERSION,
                tokens_in=response.usage.prompt_tokens,
                tokens_out=response.usage.completion_tokens,
                cost=cache_entry.cost,
                operation="popular_news_summary"
            )
            self.db.add(cost_log)
            
            # 콘텐츠 상태 업데이트
            content.ai_summary_status = "completed"
            content.ai_summarized_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"인기 뉴스 AI 요약 완료: {content.id}")
            
            return {
                "status": "success",
                "summary_bullets": ai_data.get("summary_bullets", []),
                "tags": ai_data.get("tags", []),
                "insight": ai_data.get("insight", ""),
                "tokens_used": response.usage.total_tokens,
                "cost": cache_entry.cost
            }
            
        except Exception as e:
            logger.error(f"AI 요약 생성 실패: {str(e)}")
            return {"error": str(e)}
    
    def process_popular_news(self, limit: int = 10) -> Dict[str, Any]:
        """
        인기 뉴스 10개를 선별하고 AI 요약을 생성합니다.
        
        Parameters
        ----------
        limit : int
            처리할 뉴스 개수
            
        Returns
        -------
        Dict[str, Any]
            처리 결과
        """
        try:
            # 인기 뉴스 조회
            popular_news = self.get_popular_news(limit)
            
            if not popular_news:
                return {
                    "status": "no_news",
                    "message": "처리할 인기 뉴스가 없습니다.",
                    "processed_count": 0
                }
            
            processed_count = 0
            results = []
            
            for content in popular_news:
                # 인기도 점수 계산
                popularity_score = self.analyze_popularity_score(content)
                
                # AI 요약 생성
                summary_result = self.generate_ai_summary(content)
                
                if summary_result.get("status") == "success":
                    processed_count += 1
                    results.append({
                        "content_id": content.id,
                        "title": content.title,
                        "source": content.source,
                        "popularity_score": popularity_score,
                        "summary": summary_result
                    })
            
            logger.info(f"인기 뉴스 처리 완료: {processed_count}/{len(popular_news)}")
            
            return {
                "status": "success",
                "processed_count": processed_count,
                "total_found": len(popular_news),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"인기 뉴스 처리 실패: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "processed_count": 0
            }
