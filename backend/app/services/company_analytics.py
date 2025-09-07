#!/usr/bin/env python3
"""
기업 분석 서비스

기업의 언급 횟수, 감정 분석, 트렌드 분석을 제공합니다.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, asc
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..models.company import Company, CompanyMention, CompanySummary, CompanyTrend
from ..models.content import Content

logger = logging.getLogger(__name__)


class CompanyAnalyticsService:
    """기업 분석 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_company_mentions_trend(self, company_id: int, days: int = 30) -> Dict[str, Any]:
        """
        기업 언급 트렌드를 분석합니다.
        
        Parameters
        ----------
        company_id : int
            기업 ID
        days : int
            분석 기간 (일)
            
        Returns
        -------
        Dict[str, Any]
            언급 트렌드 분석 결과
        """
        try:
            # 기업 정보 조회
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return {"error": "기업을 찾을 수 없습니다."}
            
            # 분석 기간 설정
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 일별 언급 횟수 조회
            daily_mentions = self.db.query(
                func.date(CompanyMention.created_at).label('date'),
                func.count(CompanyMention.id).label('count')
            ).filter(
                and_(
                    CompanyMention.company_id == company_id,
                    CompanyMention.created_at >= start_date,
                    CompanyMention.created_at <= end_date
                )
            ).group_by(
                func.date(CompanyMention.created_at)
            ).order_by(
                func.date(CompanyMention.created_at)
            ).all()
            
            # 트렌드 계산
            if len(daily_mentions) >= 2:
                first_half = daily_mentions[:len(daily_mentions)//2]
                second_half = daily_mentions[len(daily_mentions)//2:]
                
                first_avg = sum(day.count for day in first_half) / len(first_half)
                second_avg = sum(day.count for day in second_half) / len(second_half)
                
                if second_avg > first_avg * 1.1:
                    trend_direction = "increasing"
                elif second_avg < first_avg * 0.9:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
                
                trend_strength = abs(second_avg - first_avg) / first_avg if first_avg > 0 else 0
            else:
                trend_direction = "insufficient_data"
                trend_strength = 0
            
            # 최근 7일 평균
            recent_7_days = daily_mentions[-7:] if len(daily_mentions) >= 7 else daily_mentions
            recent_avg = sum(day.count for day in recent_7_days) / len(recent_7_days) if recent_7_days else 0
            
            return {
                "company_id": company_id,
                "company_name": company.name,
                "analysis_period": f"{days}일",
                "total_mentions": sum(day.count for day in daily_mentions),
                "daily_mentions": [
                    {
                        "date": day.date.isoformat(),
                        "count": day.count
                    } for day in daily_mentions
                ],
                "trend_direction": trend_direction,
                "trend_strength": round(trend_strength, 3),
                "recent_7day_avg": round(recent_avg, 2),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"기업 언급 트렌드 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    def get_company_sentiment_analysis(self, company_id: int, days: int = 30) -> Dict[str, Any]:
        """
        기업 감정 분석을 수행합니다.
        
        Parameters
        ----------
        company_id : int
            기업 ID
        days : int
            분석 기간 (일)
            
        Returns
        -------
        Dict[str, Any]
            감정 분석 결과
        """
        try:
            # 기업 정보 조회
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return {"error": "기업을 찾을 수 없습니다."}
            
            # 분석 기간 설정
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 관련 뉴스 조회
            news_articles = self.db.query(Content).join(
                CompanyMention, Content.id == CompanyMention.content_id
            ).filter(
                and_(
                    CompanyMention.company_id == company_id,
                    Content.published_at >= start_date,
                    Content.published_at <= end_date,
                    Content.is_active == "active"
                )
            ).all()
            
            if not news_articles:
                return {
                    "company_id": company_id,
                    "company_name": company.name,
                    "analysis_period": f"{days}일",
                    "total_articles": 0,
                    "sentiment_breakdown": {
                        "positive": 0,
                        "negative": 0,
                        "neutral": 0
                    },
                    "sentiment_score": 0.0,
                    "message": "분석할 뉴스가 없습니다."
                }
            
            # 간단한 감정 분석 (키워드 기반)
            positive_keywords = [
                '상승', '증가', '성장', '호조', '긍정', '좋은', '우수', '성공', '돌파', '신고가',
                'up', 'increase', 'growth', 'positive', 'good', 'excellent', 'success', 'breakthrough'
            ]
            
            negative_keywords = [
                '하락', '감소', '부진', '악화', '부정', '나쁜', '우려', '실패', '손실', '신저가',
                'down', 'decrease', 'decline', 'negative', 'bad', 'concern', 'failure', 'loss'
            ]
            
            sentiment_scores = []
            
            for article in news_articles:
                title_lower = article.title.lower()
                content_lower = (article.raw_text or "").lower()
                
                positive_count = sum(1 for keyword in positive_keywords if keyword in title_lower or keyword in content_lower)
                negative_count = sum(1 for keyword in negative_keywords if keyword in title_lower or keyword in content_lower)
                
                if positive_count > negative_count:
                    sentiment_scores.append(1)  # 긍정
                elif negative_count > positive_count:
                    sentiment_scores.append(-1)  # 부정
                else:
                    sentiment_scores.append(0)  # 중립
            
            # 감정 분석 결과 계산
            total_articles = len(sentiment_scores)
            positive_count = sum(1 for score in sentiment_scores if score > 0)
            negative_count = sum(1 for score in sentiment_scores if score < 0)
            neutral_count = sum(1 for score in sentiment_scores if score == 0)
            
            sentiment_score = sum(sentiment_scores) / total_articles if total_articles > 0 else 0
            
            return {
                "company_id": company_id,
                "company_name": company.name,
                "analysis_period": f"{days}일",
                "total_articles": total_articles,
                "sentiment_breakdown": {
                    "positive": positive_count,
                    "negative": negative_count,
                    "neutral": neutral_count
                },
                "sentiment_score": round(sentiment_score, 3),
                "sentiment_label": self._get_sentiment_label(sentiment_score),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"기업 감정 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    def _get_sentiment_label(self, score: float) -> str:
        """감정 점수를 라벨로 변환"""
        if score > 0.3:
            return "매우 긍정적"
        elif score > 0.1:
            return "긍정적"
        elif score > -0.1:
            return "중립적"
        elif score > -0.3:
            return "부정적"
        else:
            return "매우 부정적"
    
    def get_company_competitor_analysis(self, company_id: int, days: int = 30) -> Dict[str, Any]:
        """
        기업 경쟁사 분석을 수행합니다.
        
        Parameters
        ----------
        company_id : int
            기업 ID
        days : int
            분석 기간 (일)
            
        Returns
        -------
        Dict[str, Any]
            경쟁사 분석 결과
        """
        try:
            # 기업 정보 조회
            company = self.db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return {"error": "기업을 찾을 수 없습니다."}
            
            # 분석 기간 설정
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 같은 업종의 다른 기업들 조회
            competitors = self.db.query(Company).filter(
                and_(
                    Company.id != company_id,
                    Company.industry == company.industry,
                    Company.is_active == True
                )
            ).all()
            
            if not competitors:
                return {
                    "company_id": company_id,
                    "company_name": company.name,
                    "analysis_period": f"{days}일",
                    "competitors": [],
                    "message": "경쟁사 정보가 없습니다."
                }
            
            # 각 경쟁사의 언급 횟수 조회
            competitor_mentions = []
            
            for competitor in competitors:
                mention_count = self.db.query(CompanyMention).join(
                    Content, CompanyMention.content_id == Content.id
                ).filter(
                    and_(
                        CompanyMention.company_id == competitor.id,
                        Content.published_at >= start_date,
                        Content.published_at <= end_date,
                        Content.is_active == "active"
                    )
                ).count()
                
                competitor_mentions.append({
                    "company_id": competitor.id,
                    "company_name": competitor.name,
                    "mention_count": mention_count
                })
            
            # 언급 횟수 기준 정렬
            competitor_mentions.sort(key=lambda x: x["mention_count"], reverse=True)
            
            # 현재 기업의 언급 횟수
            current_company_mentions = self.db.query(CompanyMention).join(
                Content, CompanyMention.content_id == Content.id
            ).filter(
                and_(
                    CompanyMention.company_id == company_id,
                    Content.published_at >= start_date,
                    Content.published_at <= end_date,
                    Content.is_active == "active"
                )
            ).count()
            
            return {
                "company_id": company_id,
                "company_name": company.name,
                "analysis_period": f"{days}일",
                "current_company_mentions": current_company_mentions,
                "competitors": competitor_mentions[:10],  # 상위 10개만
                "market_share_rank": self._calculate_market_share_rank(
                    current_company_mentions, 
                    [c["mention_count"] for c in competitor_mentions]
                ),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"기업 경쟁사 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_market_share_rank(self, current_mentions: int, competitor_mentions: List[int]) -> int:
        """시장 점유율 순위 계산"""
        all_mentions = [current_mentions] + competitor_mentions
        all_mentions.sort(reverse=True)
        
        try:
            return all_mentions.index(current_mentions) + 1
        except ValueError:
            return len(all_mentions)
    
    def get_company_comprehensive_analysis(self, company_id: int, days: int = 30) -> Dict[str, Any]:
        """
        기업 종합 분석을 수행합니다.
        
        Parameters
        ----------
        company_id : int
            기업 ID
        days : int
            분석 기간 (일)
            
        Returns
        -------
        Dict[str, Any]
            종합 분석 결과
        """
        try:
            # 각 분석 수행
            mentions_trend = self.get_company_mentions_trend(company_id, days)
            sentiment_analysis = self.get_company_sentiment_analysis(company_id, days)
            competitor_analysis = self.get_company_competitor_analysis(company_id, days)
            
            # 종합 점수 계산
            trend_score = 0.3 if mentions_trend.get("trend_direction") == "increasing" else -0.3 if mentions_trend.get("trend_direction") == "decreasing" else 0
            sentiment_score = sentiment_analysis.get("sentiment_score", 0)
            market_position_score = 1.0 - (competitor_analysis.get("market_share_rank", 1) - 1) / 10.0  # 1위면 1.0, 10위면 0.1
            
            overall_score = (trend_score + sentiment_score + market_position_score) / 3
            
            return {
                "company_id": company_id,
                "company_name": mentions_trend.get("company_name", "Unknown"),
                "analysis_period": f"{days}일",
                "overall_score": round(overall_score, 3),
                "overall_rating": self._get_overall_rating(overall_score),
                "mentions_trend": mentions_trend,
                "sentiment_analysis": sentiment_analysis,
                "competitor_analysis": competitor_analysis,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"기업 종합 분석 실패: {str(e)}")
            return {"error": str(e)}
    
    def _get_overall_rating(self, score: float) -> str:
        """종합 점수를 등급으로 변환"""
        if score > 0.6:
            return "A+ (매우 우수)"
        elif score > 0.4:
            return "A (우수)"
        elif score > 0.2:
            return "B+ (양호)"
        elif score > 0.0:
            return "B (보통)"
        elif score > -0.2:
            return "C (주의)"
        elif score > -0.4:
            return "D (위험)"
        else:
            return "F (매우 위험)"
