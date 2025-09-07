from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Content(Base):
    __tablename__ = "content"
    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)
    title = Column(String(512), nullable=False)
    author = Column(String(256))
    url = Column(String(1024), nullable=False)
    published_at = Column(DateTime)
    raw_text = Column(Text)
    lang = Column(String(16))
    hash = Column(String(64), nullable=False, unique=True)
    summary_bullets = Column(JSONB)  # 최대 5개 bullet points
    insight = Column(Text)  # 2-3문장
    tags = Column(JSONB)  # 상위 N개 태그
    is_active = Column(String(10), default="active")  # active, inactive, deleted
    ai_summary_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    ai_summarized_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 인기도 메트릭
    view_count = Column(Integer, default=0)  # 조회수
    like_count = Column(Integer, default=0)  # 좋아요 수
    share_count = Column(Integer, default=0)  # 공유 수
    comment_count = Column(Integer, default=0)  # 댓글 수
    engagement_score = Column(String(20), default="low")  # low, medium, high, viral

    __table_args__ = (
        UniqueConstraint("hash", name="uq_content_hash"),
        Index("idx_published_at_desc", "published_at"),
    )

class AICache(Base):
    __tablename__ = "ai_cache"
    id = Column(Integer, primary_key=True)
    content_hash = Column(String(64), nullable=False)
    model_version = Column(String(50), nullable=False, default="gpt-3.5-turbo")
    summary_bullets = Column(JSONB)  # 최대 5개
    insight = Column(Text)  # 2-3문장  
    tags = Column(JSONB)  # 상위 N개 태그
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("content_hash", "model_version", name="uq_ai_cache"),
        Index("idx_content_hash", "content_hash"),
    )
