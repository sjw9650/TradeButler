"""비용 로깅 모델"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import Base

class CostLog(Base):
    """OpenAI API 호출 비용 로깅 테이블"""
    __tablename__ = "cost_log"
    
    id = Column(Integer, primary_key=True)
    content_id = Column(Integer, nullable=True)  # 연결된 콘텐츠 ID
    model_name = Column(String(100), nullable=False)  # 사용된 모델 (gpt-3.5-turbo 등)
    tokens_in = Column(Integer, nullable=False)  # 입력 토큰 수
    tokens_out = Column(Integer, nullable=False)  # 출력 토큰 수
    cost_usd = Column(Float, nullable=False)  # 비용 (USD)
    request_type = Column(String(50), nullable=False)  # 요청 유형 (summarize, tag 등)
    status = Column(String(20), nullable=False, default="success")  # 성공/실패 상태
    error_message = Column(Text, nullable=True)  # 오류 메시지
    metadata = Column(JSONB, nullable=True)  # 추가 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_cost_log_content_id", "content_id"),
        Index("idx_cost_log_model", "model_name"),
        Index("idx_cost_log_date", "created_at"),
        Index("idx_cost_log_type", "request_type"),
    )
    
    def __repr__(self):
        return f"<CostLog(id={self.id}, model={self.model_name}, cost=${self.cost_usd:.4f})>" 