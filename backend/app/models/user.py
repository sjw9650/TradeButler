from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    google_id = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    picture = Column(String(500))  # 프로필 이미지 URL
    locale = Column(String(10), default="ko")
    
    # 계정 상태
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 사용자 설정
    preferences = Column(JSONB, default={})  # 사용자 개인 설정
    notification_settings = Column(JSONB, default={
        "email_notifications": True,
        "push_notifications": True,
        "newsletter": False,
        "market_alerts": True
    })
    
    # 구독 정보
    subscription_tier = Column(String(20), default="free")  # free, premium, enterprise
    subscription_expires_at = Column(DateTime)

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    refresh_token = Column(String(255))
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # 세션 메타데이터
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_info = Column(JSONB)