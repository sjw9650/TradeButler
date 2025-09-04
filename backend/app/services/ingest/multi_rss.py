#!/usr/bin/env python3
"""
다중 RSS 피드 수집 서비스

여러 RSS 피드를 한 번에 수집하고 관리하는 기능을 제공합니다.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from .rss import ingest_rss


# RSS 피드 설정
RSS_FEEDS = {
    # 한국 뉴스
    "korean": [
        {
            "name": "한국경제 경제",
            "url": "https://www.hankyung.com/feed/economy",
            "source_name": "rss:hankyung_economy",
            "category": "economy",
            "language": "ko"
        },
        {
            "name": "한국경제 금융",
            "url": "https://www.hankyung.com/feed/finance", 
            "source_name": "rss:hankyung_finance",
            "category": "finance",
            "language": "ko"
        }
    ],
    
    # 미국 뉴스
    "us_news": [
        {
            "name": "Yahoo News",
            "url": "https://news.yahoo.com/rss/",
            "source_name": "rss:yahoo_news",
            "category": "general",
            "language": "en"
        },
        {
            "name": "CNN Top Stories",
            "url": "http://rss.cnn.com/rss/cnn_topstories.rss",
            "source_name": "rss:cnn_topstories",
            "category": "general",
            "language": "en"
        },
        {
            "name": "NYT HomePage",
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "source_name": "rss:nyt_homepage",
            "category": "general",
            "language": "en"
        },
        {
            "name": "MarketWatch",
            "url": "https://feeds.marketwatch.com/marketwatch/topstories/",
            "source_name": "rss:marketwatch_topstories",
            "category": "finance",
            "language": "en"
        },
        {
            "name": "CNBC",
            "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
            "source_name": "rss:cnbc_topstories",
            "category": "finance",
            "language": "en"
        }
    ]
}


def ingest_multiple_feeds(feed_groups: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    여러 RSS 피드 그룹을 수집합니다.
    
    Parameters
    ----------
    feed_groups : Optional[List[str]], optional
        수집할 피드 그룹 목록. None이면 모든 그룹 수집
        가능한 값: "korean", "us_news"
        
    Returns
    -------
    Dict[str, Any]
        수집 결과 통계
        - total_processed: 전체 처리된 기사 수
        - total_saved: 전체 저장된 기사 수
        - total_duplicates: 전체 중복 기사 수
        - total_queued_tasks: 전체 AI 처리 큐잉 수
        - feed_results: 각 피드별 상세 결과
        - start_time: 수집 시작 시간
        - end_time: 수집 완료 시간
        - duration_seconds: 수집 소요 시간(초)
        
    Examples
    --------
    >>> # 모든 피드 수집
    >>> result = ingest_multiple_feeds()
    >>> print(f"총 {result['total_saved']}개 기사 수집")
    
    >>> # 특정 그룹만 수집
    >>> result = ingest_multiple_feeds(['korean'])
    >>> print(f"한국 뉴스 {result['total_saved']}개 수집")
    """
    start_time = datetime.now()
    
    if feed_groups is None:
        feed_groups = list(RSS_FEEDS.keys())
    
    # 전체 통계
    total_processed = 0
    total_saved = 0
    total_duplicates = 0
    total_queued_tasks = 0
    
    # 각 피드별 결과
    feed_results = {}
    
    print(f"=== 다중 RSS 피드 수집 시작 ===")
    print(f"수집 그룹: {', '.join(feed_groups)}")
    print(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    for group in feed_groups:
        if group not in RSS_FEEDS:
            print(f"⚠️  알 수 없는 피드 그룹: {group}")
            continue
            
        print(f"📰 {group.upper()} 그룹 수집 중...")
        group_processed = 0
        group_saved = 0
        group_duplicates = 0
        group_queued = 0
        
        for feed_config in RSS_FEEDS[group]:
            name = feed_config["name"]
            url = feed_config["url"]
            source_name = feed_config["source_name"]
            
            print(f"  🔄 {name} 수집 중...")
            
            try:
                result = ingest_rss(url, source_name=source_name)
                
                print(f"    ✅ 처리: {result['processed']}개, 저장: {result['saved']}개, 중복: {result['duplicates']}개")
                
                # 통계 누적
                group_processed += result['processed']
                group_saved += result['saved']
                group_duplicates += result['duplicates']
                group_queued += result['queued_tasks']
                
                # 개별 피드 결과 저장
                feed_results[source_name] = {
                    "name": name,
                    "url": url,
                    "processed": result['processed'],
                    "saved": result['saved'],
                    "duplicates": result['duplicates'],
                    "queued_tasks": result['queued_tasks'],
                    "status": "success"
                }
                
            except Exception as e:
                print(f"    ❌ 에러: {e}")
                feed_results[source_name] = {
                    "name": name,
                    "url": url,
                    "processed": 0,
                    "saved": 0,
                    "duplicates": 0,
                    "queued_tasks": 0,
                    "status": "error",
                    "error": str(e)
                }
        
        # 그룹별 통계
        print(f"  📊 {group} 그룹 완료: 처리 {group_processed}개, 저장 {group_saved}개")
        print()
        
        # 전체 통계에 누적
        total_processed += group_processed
        total_saved += group_saved
        total_duplicates += group_duplicates
        total_queued_tasks += group_queued
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"=== 수집 완료 ===")
    print(f"총 처리된 기사: {total_processed}개")
    print(f"총 저장된 기사: {total_saved}개")
    print(f"총 중복 기사: {total_duplicates}개")
    print(f"총 AI 처리 큐잉: {total_queued_tasks}개")
    print(f"소요 시간: {duration:.2f}초")
    
    return {
        "total_processed": total_processed,
        "total_saved": total_saved,
        "total_duplicates": total_duplicates,
        "total_queued_tasks": total_queued_tasks,
        "feed_results": feed_results,
        "start_time": start_time,
        "end_time": end_time,
        "duration_seconds": duration,
        "feed_groups": feed_groups
    }


def get_available_feeds() -> Dict[str, List[Dict[str, str]]]:
    """
    사용 가능한 RSS 피드 목록을 반환합니다.
    
    Returns
    -------
    Dict[str, List[Dict[str, str]]]
        피드 그룹별 피드 목록
    """
    return RSS_FEEDS


def add_feed_to_group(group: str, feed_config: Dict[str, str]) -> bool:
    """
    새로운 RSS 피드를 그룹에 추가합니다.
    
    Parameters
    ----------
    group : str
        피드 그룹명
    feed_config : Dict[str, str]
        피드 설정 (name, url, source_name, category, language)
        
    Returns
    -------
    bool
        추가 성공 여부
    """
    if group not in RSS_FEEDS:
        RSS_FEEDS[group] = []
    
    # 필수 필드 확인
    required_fields = ["name", "url", "source_name", "category", "language"]
    if not all(field in feed_config for field in required_fields):
        return False
    
    RSS_FEEDS[group].append(feed_config)
    return True


if __name__ == "__main__":
    # 직접 실행 시 모든 피드 수집
    result = ingest_multiple_feeds()
    print(f"\n최종 결과: {result['total_saved']}개 기사 수집 완료!")
