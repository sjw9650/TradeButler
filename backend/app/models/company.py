#!/usr/bin/env python3
"""
기업 관련 데이터베이스 모델

2단계 AI 처리 시스템을 위한 기업 추출, 팔로잉, 언급 추적 모델
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from ..models.base import Base


class Company(Base):
    """기업 정보 테이블"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True, comment="기업명")
    display_name = Column(String(200), nullable=True, comment="표시명")
    industry = Column(String(100), nullable=True, comment="업종")
    market_cap = Column(String(50), nullable=True, comment="시가총액")
    stock_symbol = Column(String(20), nullable=True, comment="주식 심볼")
    country = Column(String(50), nullable=True, comment="국가")
    website = Column(String(500), nullable=True, comment="웹사이트")
    description = Column(Text, nullable=True, comment="기업 설명")
    
    # AI 추출 관련
    aliases = Column(JSONB, nullable=True, comment="기업 별칭/동의어")
    keywords = Column(JSONB, nullable=True, comment="관련 키워드")
    confidence_score = Column(Float, nullable=True, comment="AI 추출 신뢰도")
    
    # 통계 정보
    total_mentions = Column(Integer, default=0, comment="총 언급 횟수")
    last_mentioned_at = Column(DateTime, nullable=True, comment="마지막 언급일")
    
    # 메타데이터
    is_active = Column(Boolean, default=True, comment="활성 상태")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일")
    
    # 관계
    mentions = relationship("CompanyMention", back_populates="company")
    user_followings = relationship("UserFollowing", back_populates="company")
    
    # 인덱스
    __table_args__ = (
        Index('idx_company_name', 'name'),
        Index('idx_company_industry', 'industry'),
        Index('idx_company_active', 'is_active'),
        Index('idx_company_mentions', 'total_mentions'),
    )


class UserFollowing(Base):
    """사용자 기업 팔로잉 테이블"""
    __tablename__ = "user_followings"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False, comment="사용자 ID (OAuth ID)")
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, comment="기업 ID")
    
    # 팔로잉 설정
    priority = Column(Integer, default=1, comment="우선순위 (1-5)")
    notification_enabled = Column(Boolean, default=True, comment="알림 활성화")
    auto_summarize = Column(Boolean, default=True, comment="자동 요약 활성화")
    
    # 사용자 설정
    keywords_filter = Column(JSONB, nullable=True, comment="키워드 필터")
    sentiment_filter = Column(String(20), nullable=True, comment="감정 필터 (positive/negative/neutral)")
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, comment="팔로잉 시작일")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일")
    
    # 관계
    company = relationship("Company", back_populates="user_followings")
    
    # 인덱스
    __table_args__ = (
        Index('idx_user_following_user', 'user_id'),
        Index('idx_user_following_company', 'company_id'),
        Index('idx_user_following_priority', 'priority'),
        Index('idx_user_following_auto_summarize', 'auto_summarize'),
    )


class CompanyMention(Base):
    """기업 언급 추적 테이블"""
    __tablename__ = "company_mentions"
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, comment="기업 ID")
    content_id = Column(Integer, ForeignKey('content.id'), nullable=False, comment="콘텐츠 ID")
    
    # 언급 정보
    mention_text = Column(Text, nullable=False, comment="언급된 텍스트")
    mention_context = Column(Text, nullable=True, comment="언급 컨텍스트")
    mention_position = Column(Integer, nullable=True, comment="텍스트 내 위치")
    
    # AI 분석 결과
    sentiment = Column(String(20), nullable=True, comment="감정 분석 (positive/negative/neutral)")
    relevance_score = Column(Float, nullable=True, comment="관련도 점수")
    confidence_score = Column(Float, nullable=True, comment="신뢰도 점수")
    
    # 추출 정보
    extraction_method = Column(String(50), nullable=True, comment="추출 방법 (ai/manual)")
    extraction_model = Column(String(100), nullable=True, comment="사용된 AI 모델")
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, comment="언급 추출일")
    
    # 관계
    company = relationship("Company", back_populates="mentions")
    content = relationship("Content", backref="company_mentions")
    
    # 인덱스
    __table_args__ = (
        Index('idx_mention_company', 'company_id'),
        Index('idx_mention_content', 'content_id'),
        Index('idx_mention_sentiment', 'sentiment'),
        Index('idx_mention_relevance', 'relevance_score'),
        Index('idx_mention_created', 'created_at'),
    )


class CompanySummary(Base):
    """기업별 요약 정보 테이블"""
    __tablename__ = "company_summaries"
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, comment="기업 ID")
    content_id = Column(Integer, ForeignKey('content.id'), nullable=False, comment="콘텐츠 ID")
    
    # 요약 정보
    summary_bullets = Column(JSONB, nullable=True, comment="요약 불릿 포인트")
    insight = Column(Text, nullable=True, comment="인사이트")
    key_points = Column(JSONB, nullable=True, comment="핵심 포인트")
    
    # AI 분석 결과
    sentiment_analysis = Column(JSONB, nullable=True, comment="감정 분석 결과")
    impact_score = Column(Float, nullable=True, comment="영향도 점수")
    urgency_score = Column(Float, nullable=True, comment="긴급도 점수")
    
    # 처리 정보
    processing_status = Column(String(20), default="pending", comment="처리 상태 (pending/processing/completed/failed)")
    processing_priority = Column(Integer, default=1, comment="처리 우선순위")
    
    # AI 메타데이터
    model_version = Column(String(50), nullable=True, comment="AI 모델 버전")
    processing_time = Column(Float, nullable=True, comment="처리 시간 (초)")
    token_usage = Column(JSONB, nullable=True, comment="토큰 사용량")
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일")
    
    # 관계
    company = relationship("Company")
    content = relationship("Content")
    
    # 인덱스
    __table_args__ = (
        Index('idx_summary_company', 'company_id'),
        Index('idx_summary_content', 'content_id'),
        Index('idx_summary_status', 'processing_status'),
        Index('idx_summary_priority', 'processing_priority'),
        Index('idx_summary_created', 'created_at'),
    )


class CompanyTrend(Base):
    """기업 트렌드 분석 테이블"""
    __tablename__ = "company_trends"
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, comment="기업 ID")
    
    # 트렌드 정보
    date = Column(DateTime, nullable=False, comment="분석 날짜")
    period = Column(String(20), nullable=False, comment="분석 기간 (daily/weekly/monthly)")
    
    # 언급 통계
    mention_count = Column(Integer, default=0, comment="언급 횟수")
    positive_mentions = Column(Integer, default=0, comment="긍정적 언급")
    negative_mentions = Column(Integer, default=0, comment="부정적 언급")
    neutral_mentions = Column(Integer, default=0, comment="중립적 언급")
    
    # 감정 점수
    sentiment_score = Column(Float, nullable=True, comment="감정 점수 (-1 ~ 1)")
    relevance_score = Column(Float, nullable=True, comment="관련도 점수")
    impact_score = Column(Float, nullable=True, comment="영향도 점수")
    
    # 트렌드 분석
    trend_direction = Column(String(20), nullable=True, comment="트렌드 방향 (up/down/stable)")
    trend_strength = Column(Float, nullable=True, comment="트렌드 강도")
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일")
    
    # 관계
    company = relationship("Company")
    
    # 인덱스
    __table_args__ = (
        Index('idx_trend_company', 'company_id'),
        Index('idx_trend_date', 'date'),
        Index('idx_trend_period', 'period'),
        Index('idx_trend_sentiment', 'sentiment_score'),
    )
