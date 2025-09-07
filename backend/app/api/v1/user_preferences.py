#!/usr/bin/env python3
"""
사용자 설정 API 엔드포인트

팔로잉 기업 관리, 알림 설정, 필터링 옵션을 제공합니다.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from ...repo.db import get_db
from ...core.oauth import get_current_user_optional
from ...models.user import User
from ...services.user_preferences import UserPreferencesService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/user/preferences", summary="사용자 설정 조회")
def get_user_preferences(
    user_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용자 설정을 조회합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        사용자 설정 정보
    """
    try:
        preferences_service = UserPreferencesService(db)
        result = preferences_service.get_user_preferences(user_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 설정 조회 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="사용자 설정 조회에 실패했습니다.")

@router.put("/user/preferences", summary="사용자 설정 업데이트")
def update_user_preferences(
    user_id: str,
    preferences: Dict[str, Any] = Body(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용자 설정을 업데이트합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    preferences : Dict[str, Any]
        업데이트할 설정
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        업데이트 결과
    """
    try:
        preferences_service = UserPreferencesService(db)
        result = preferences_service.update_user_preferences(user_id, preferences)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 설정 업데이트 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="사용자 설정 업데이트에 실패했습니다.")

@router.get("/user/following", summary="팔로잉 기업 목록 조회")
def get_following_companies(
    user_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    팔로잉한 기업 목록을 조회합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        팔로잉 기업 목록
    """
    try:
        preferences_service = UserPreferencesService(db)
        result = preferences_service.get_following_companies(user_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"팔로잉 기업 목록 조회 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="팔로잉 기업 목록 조회에 실패했습니다.")

@router.post("/user/following", summary="기업 팔로잉")
def add_following_company(
    user_id: str,
    company_id: int,
    priority: int = 0,
    notes: str = "",
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    기업을 팔로잉합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    company_id : int
        기업 ID
    priority : int
        우선순위 (0-10)
    notes : str
        메모
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        팔로잉 결과
    """
    try:
        preferences_service = UserPreferencesService(db)
        result = preferences_service.add_following_company(user_id, company_id, priority, notes)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 팔로잉 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="기업 팔로잉에 실패했습니다.")

@router.delete("/user/following/{company_id}", summary="기업 팔로잉 해제")
def remove_following_company(
    user_id: str,
    company_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    기업 팔로잉을 해제합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    company_id : int
        기업 ID
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        팔로잉 해제 결과
    """
    try:
        preferences_service = UserPreferencesService(db)
        result = preferences_service.remove_following_company(user_id, company_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기업 팔로잉 해제 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="기업 팔로잉 해제에 실패했습니다.")

@router.put("/user/following/{company_id}/priority", summary="팔로잉 기업 우선순위 업데이트")
def update_following_priority(
    user_id: str,
    company_id: int,
    priority: int = Body(..., ge=0, le=10),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    팔로잉 기업의 우선순위를 업데이트합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    company_id : int
        기업 ID
    priority : int
        새로운 우선순위 (0-10)
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        우선순위 업데이트 결과
    """
    try:
        preferences_service = UserPreferencesService(db)
        result = preferences_service.update_following_priority(user_id, company_id, priority)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"우선순위 업데이트 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="우선순위 업데이트에 실패했습니다.")

@router.get("/user/notifications", summary="알림 설정 조회")
def get_notification_settings(
    user_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    알림 설정을 조회합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        알림 설정 정보
    """
    try:
        preferences_service = UserPreferencesService(db)
        result = preferences_service.get_notification_settings(user_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 설정 조회 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="알림 설정 조회에 실패했습니다.")

@router.put("/user/notifications", summary="알림 설정 업데이트")
def update_notification_settings(
    user_id: str,
    settings: Dict[str, Any] = Body(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    알림 설정을 업데이트합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    settings : Dict[str, Any]
        업데이트할 알림 설정
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        업데이트 결과
    """
    try:
        preferences_service = UserPreferencesService(db)
        result = preferences_service.update_notification_settings(user_id, settings)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"알림 설정 업데이트 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="알림 설정 업데이트에 실패했습니다.")

@router.get("/user/dashboard", summary="사용자 대시보드 데이터 조회")
def get_user_dashboard_data(
    user_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    사용자 대시보드 데이터를 조회합니다.
    
    Parameters
    ----------
    user_id : str
        사용자 ID
    current_user : Optional[User]
        현재 로그인한 사용자
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Dict[str, Any]
        대시보드 데이터
    """
    try:
        preferences_service = UserPreferencesService(db)
        result = preferences_service.get_user_dashboard_data(user_id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 대시보드 데이터 조회 API 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="사용자 대시보드 데이터 조회에 실패했습니다.")
