"""브리핑 관련 API 엔드포인트"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import json
from datetime import datetime, timedelta
import redis
from ...core.config import settings

router = APIRouter(tags=["brief"])

# Redis 연결
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

@router.get("/v1/brief/daily")
async def get_daily_brief() -> Dict[str, Any]:
    """
    일일 브리핑 조회 (Redis 캐시 5분)
    
    Returns:
        Dict[str, Any]: 일일 브리핑 정보
        
    Examples:
        >>> GET /v1/brief/daily
        {
            "date": "2024-01-15",
            "summary": "오늘의 주요 콘텐츠 요약...",
            "topics": ["AI", "Tech", "Finance"],
            "cached": true
        }
    """
    cache_key = f"daily_brief:{datetime.now().strftime('%Y-%m-%d')}"
    
    # Redis 캐시 확인 (5분)
    cached_brief = redis_client.get(cache_key)
    if cached_brief:
        return {
            **json.loads(cached_brief),
            "cached": True,
            "cache_expires": "5분"
        }
    
    # 캐시가 없으면 새로 생성 (스텁 데이터)
    daily_brief = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "summary": "오늘의 주요 콘텐츠 요약이 준비되었습니다.",
        "topics": ["AI", "Tech", "Finance", "Startup"],
        "content_count": 0,
        "ai_processed": 0,
        "generated_at": datetime.now().isoformat()
    }
    
    # Redis에 5분간 캐시
    redis_client.setex(cache_key, 300, json.dumps(daily_brief))
    
    return {
        **daily_brief,
        "cached": False,
        "cache_expires": "5분"
    } 