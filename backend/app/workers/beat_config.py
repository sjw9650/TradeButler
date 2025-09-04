#!/usr/bin/env python3
"""
Celery Beat 스케줄 설정

RSS 수집 스케줄을 정의합니다.
"""

from celery.schedules import crontab

# Celery Beat 스케줄 설정
BEAT_SCHEDULE = {
    # 한국 뉴스 수집 (매시간 정각)
    'korean-news-hourly': {
        'task': 'scheduled_korean_news_ingestion',
        'schedule': crontab(minute=0),  # 매시간 정각
        'options': {
            'queue': 'rss_ingestion',
            'priority': 5
        }
    },
    
    # 미국 뉴스 수집 (30분마다)
    'us-news-30min': {
        'task': 'scheduled_us_news_ingestion', 
        'schedule': crontab(minute='*/30'),  # 30분마다
        'options': {
            'queue': 'rss_ingestion',
            'priority': 5
        }
    },
    
    # 전체 뉴스 수집 (매일 새벽 2시)
    'all-news-daily': {
        'task': 'scheduled_all_news_ingestion',
        'schedule': crontab(hour=2, minute=0),  # 매일 새벽 2시
        'options': {
            'queue': 'rss_ingestion',
            'priority': 3
        }
    },
    
    # 헬스 체크 (5분마다)
    'health-check': {
        'task': 'health_check',
        'schedule': crontab(minute='*/5'),  # 5분마다
        'options': {
            'queue': 'default',
            'priority': 1
        }
    }
}

# 타임존 설정
BEAT_TIMEZONE = 'Asia/Seoul'

# 스케줄 설명
SCHEDULE_DESCRIPTIONS = {
    'korean-news-hourly': '한국 뉴스 RSS 수집 (매시간)',
    'us-news-30min': '미국 뉴스 RSS 수집 (30분마다)', 
    'all-news-daily': '전체 뉴스 RSS 수집 (매일 새벽 2시)',
    'health-check': '시스템 상태 확인 (5분마다)'
}
