#!/usr/bin/env python3
"""
인증 관련 API 엔드포인트

Google OAuth 2.0 로그인, 로그아웃, 사용자 정보 관리
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import logging

from ...repo.db import get_db
from ...core.oauth import google_oauth, get_current_user, get_current_user_optional
from ...models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/auth/google/login", summary="Google 로그인 URL 생성")
def get_google_login_url() -> Dict[str, Any]:
    """
    Google OAuth 2.0 로그인 URL을 생성합니다.
    
    Returns
    -------
    Dict[str, Any]
        로그인 URL과 상태 정보
    """
    try:
        auth_url = google_oauth.get_authorization_url()
        
        return {
            "auth_url": auth_url,
            "message": "Google 로그인 URL이 생성되었습니다.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Google 로그인 URL 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="로그인 URL 생성에 실패했습니다.")

@router.post("/auth/google/callback", summary="Google 로그인 콜백 처리")
def handle_google_callback(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Google OAuth 2.0 콜백을 처리합니다.
    
    Parameters
    ----------
    request : Request
        FastAPI 요청 객체
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        로그인 결과 및 사용자 정보
    """
    try:
        # 요청에서 토큰 추출 (실제로는 프론트엔드에서 전달)
        body = request.json()
        google_token = body.get("token")
        
        if not google_token:
            raise HTTPException(status_code=400, detail="Google 토큰이 필요합니다.")
        
        # Google 토큰 검증
        user_info = google_oauth.verify_google_token(google_token)
        
        # 사용자 생성 또는 업데이트
        user = google_oauth.create_or_update_user(db, user_info)
        
        # 세션 생성
        device_info = {
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host
        }
        session_token = google_oauth.create_user_session(db, user.id, device_info)
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "is_premium": user.is_premium,
                "subscription_tier": user.subscription_tier
            },
            "session_token": session_token,
            "message": "로그인이 완료되었습니다.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google 로그인 콜백 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="로그인 처리에 실패했습니다.")

@router.get("/auth/me", summary="현재 사용자 정보 조회")
def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    현재 로그인한 사용자의 정보를 조회합니다.
    
    Parameters
    ----------
    current_user : User
        현재 로그인한 사용자
        
    Returns
    -------
    Dict[str, Any]
        사용자 정보
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture,
        "locale": current_user.locale,
        "is_premium": current_user.is_premium,
        "subscription_tier": current_user.subscription_tier,
        "preferences": current_user.preferences or {},
        "notification_settings": current_user.notification_settings or {},
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
        "created_at": current_user.created_at.isoformat()
    }

@router.post("/auth/logout", summary="로그아웃")
def logout_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용자를 로그아웃합니다.
    
    Parameters
    ----------
    request : Request
        FastAPI 요청 객체
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        로그아웃 결과
    """
    try:
        # Authorization 헤더에서 토큰 추출
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")
        
        session_token = auth_header.split(" ")[1]
        
        # 세션 삭제
        success = google_oauth.logout_user(db, session_token)
        
        if success:
            return {
                "success": True,
                "message": "로그아웃이 완료되었습니다.",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="로그아웃에 실패했습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"로그아웃 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="로그아웃 처리에 실패했습니다.")

@router.put("/auth/preferences", summary="사용자 설정 업데이트")
def update_user_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용자의 개인 설정을 업데이트합니다.
    
    Parameters
    ----------
    preferences : Dict[str, Any]
        업데이트할 설정
    current_user : User
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        업데이트 결과
    """
    try:
        # 기존 설정과 병합
        current_preferences = current_user.preferences or {}
        current_preferences.update(preferences)
        
        # 데이터베이스 업데이트
        current_user.preferences = current_preferences
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "preferences": current_preferences,
            "message": "설정이 업데이트되었습니다.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"사용자 설정 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="설정 업데이트에 실패했습니다.")

@router.put("/auth/notification-settings", summary="알림 설정 업데이트")
def update_notification_settings(
    notification_settings: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용자의 알림 설정을 업데이트합니다.
    
    Parameters
    ----------
    notification_settings : Dict[str, Any]
        업데이트할 알림 설정
    current_user : User
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        업데이트 결과
    """
    try:
        # 기존 설정과 병합
        current_settings = current_user.notification_settings or {}
        current_settings.update(notification_settings)
        
        # 데이터베이스 업데이트
        current_user.notification_settings = current_settings
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "notification_settings": current_settings,
            "message": "알림 설정이 업데이트되었습니다.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"알림 설정 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="알림 설정 업데이트에 실패했습니다.")
