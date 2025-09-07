#!/usr/bin/env python3
"""
Google OAuth 2.0 설정 및 인증 관리
"""

import os
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import secrets
from datetime import datetime, timedelta

from ..repo.db import get_db
from ..models.user import User, UserSession
from ..core.config import settings

# OAuth 설정
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/callback")

# JWT 설정
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

security = HTTPBearer()

class GoogleOAuth:
    """Google OAuth 2.0 관리 클래스"""
    
    def __init__(self):
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.redirect_uri = GOOGLE_REDIRECT_URI
        
        # OAuth Flow 설정
        self.flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=[
                "openid",
                "email", 
                "profile"
            ]
        )
        self.flow.redirect_uri = self.redirect_uri
    
    def get_authorization_url(self) -> str:
        """Google 로그인 URL 생성"""
        authorization_url, state = self.flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        return authorization_url
    
    def verify_google_token(self, token: str) -> dict:
        """Google ID 토큰 검증"""
        try:
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                self.client_id
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            return {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo['name'],
                'picture': idinfo.get('picture'),
                'locale': idinfo.get('locale', 'ko')
            }
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid token: {str(e)}")
    
    def create_or_update_user(self, db: Session, user_info: dict) -> User:
        """사용자 생성 또는 업데이트"""
        # 기존 사용자 조회
        user = db.query(User).filter(User.google_id == user_info['google_id']).first()
        
        if user:
            # 기존 사용자 업데이트
            user.email = user_info['email']
            user.name = user_info['name']
            user.picture = user_info.get('picture')
            user.locale = user_info.get('locale', 'ko')
            user.last_login = datetime.utcnow()
            user.updated_at = datetime.utcnow()
        else:
            # 새 사용자 생성
            user = User(
                google_id=user_info['google_id'],
                email=user_info['email'],
                name=user_info['name'],
                picture=user_info.get('picture'),
                locale=user_info.get('locale', 'ko'),
                last_login=datetime.utcnow()
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        return user
    
    def create_user_session(self, db: Session, user_id: int, device_info: dict = None) -> str:
        """사용자 세션 생성"""
        # 세션 토큰 생성
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
        
        # 기존 세션 정리 (같은 사용자의 오래된 세션 삭제)
        db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.expires_at < datetime.utcnow()
        ).delete()
        
        # 새 세션 생성
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            device_info=device_info or {}
        )
        
        db.add(session)
        db.commit()
        
        return session_token
    
    def validate_session(self, db: Session, session_token: str) -> Optional[User]:
        """세션 검증"""
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if not session:
            return None
        
        # 세션 활동 시간 업데이트
        session.last_activity = datetime.utcnow()
        db.commit()
        
        # 사용자 정보 반환
        return db.query(User).filter(User.id == session.user_id).first()
    
    def logout_user(self, db: Session, session_token: str) -> bool:
        """사용자 로그아웃"""
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        
        if session:
            db.delete(session)
            db.commit()
            return True
        
        return False

# 전역 OAuth 인스턴스
google_oauth = GoogleOAuth()

# 의존성 주입 함수들
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """현재 로그인한 사용자 정보 반환"""
    token = credentials.credentials
    user = google_oauth.validate_session(db, token)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """현재 로그인한 사용자 정보 반환 (선택적)"""
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None
