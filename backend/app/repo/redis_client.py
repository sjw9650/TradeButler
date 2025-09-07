#!/usr/bin/env python3
"""
Redis 클라이언트 설정

Redis 연결을 관리합니다.
"""

import redis
import os
from typing import Optional

# Redis 연결 설정
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Redis 클라이언트 인스턴스
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """
    Redis 클라이언트를 반환합니다.
    
    Returns
    -------
    redis.Redis
        Redis 클라이언트 인스턴스
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
    
    return _redis_client


def close_redis_client():
    """Redis 클라이언트 연결을 닫습니다."""
    global _redis_client
    
    if _redis_client:
        _redis_client.close()
        _redis_client = None
