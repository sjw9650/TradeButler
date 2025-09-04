import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import feedparser
import httpx
from bs4 import BeautifulSoup
from readability import Document
from sqlalchemy.orm import Session
from ...repo.db import SessionLocal
from ...models.content import Content
from ...workers.tasks import summarize_task

def normalize_url(url: str) -> str:
    """
    URL 정규화
    
    Parameters
    ----------
    url : str
        정규화할 URL
        
    Returns
    -------
    str
        정규화된 URL
        
    Examples
    --------
    >>> normalize_url("  https://example.com  ")
    'https://example.com'
    """
    return url.strip()

def text_hash(text: str) -> str:
    """
    텍스트의 SHA256 해시 생성
    
    Parameters
    ----------
    text : str
        해시할 텍스트
        
    Returns
    -------
    str
        SHA256 해시 문자열
        
    Examples
    --------
    >>> text_hash("hello world")
    'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def extract_readable_with_fallback(html: str, fallback_text: str = "") -> Tuple[str, str]:
    """
    HTML에서 읽기 가능한 텍스트 추출 (2단계 폴백 전략)
    
    Parameters
    ----------
    html : str
        파싱할 HTML 문자열
    fallback_text : str, optional
        최종 폴백 텍스트
        
    Returns
    -------
    Tuple[str, str]
        (추출된 텍스트, 사용된 전략)
        전략: "readability", "beautifulsoup", "fallback"
        
    Examples
    --------
    >>> text, strategy = extract_readable_with_fallback("<p>Hello world</p>")
    >>> print(f"Text: {text}, Strategy: {strategy}")
    Text: Hello world, Strategy: readability
    """
    # 1단계: readability-lxml 사용 (가장 정확)
    try:
        doc = Document(html)
        content_html = doc.summary()
        soup = BeautifulSoup(content_html, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        if text and len(text.strip()) > 10:  # 최소 길이 체크
            return text, "readability"
    except Exception:
        pass
    
    # 2단계: BeautifulSoup만 사용 (심플한 파싱)
    try:
        soup = BeautifulSoup(html, "html.parser")
        # 스크립트, 스타일 태그 제거
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        text = soup.get_text(separator=" ", strip=True)
        if text and len(text.strip()) > 10:
            return text, "beautifulsoup"
    except Exception:
        pass
    
    # 3단계: 폴백 텍스트 사용
    return fallback_text, "fallback"

def fetch_content_text(url: str, fallback_summary: str = "") -> Tuple[str, str]:
    """
    URL에서 콘텐츠 텍스트 가져오기 (I/O 분리)
    
    Parameters
    ----------
    url : str
        가져올 URL
    fallback_summary : str, optional
        HTTP 요청 실패 시 사용할 폴백 텍스트
        
    Returns
    -------
    Tuple[str, str]
        (추출된 텍스트, 사용된 방법)
        방법: "http_readability", "http_beautifulsoup", "fallback"
        
    Examples
    --------
    >>> text, method = fetch_content_text("https://example.com", "fallback text")
    >>> print(f"Method: {method}")
    """
    try:
        resp = httpx.get(url, timeout=10, follow_redirects=True)
        resp.raise_for_status()
        
        text, strategy = extract_readable_with_fallback(resp.text, fallback_summary)
        return text, f"http_{strategy}"
        
    except Exception:
        return fallback_summary, "fallback"

def create_content_data(entry: Any, source_name: str, raw_text: str) -> Dict[str, Any]:
    """
    RSS 엔트리에서 콘텐츠 데이터 생성 (Pure Function)
    
    Parameters
    ----------
    entry : Any
        RSS 피드 엔트리 객체
    source_name : str
        소스 이름
    raw_text : str
        추출된 텍스트
        
    Returns
    -------
    Dict[str, Any]
        콘텐츠 데이터 딕셔너리
        
    Examples
    --------
    >>> entry = {"title": "Test", "link": "https://example.com"}
    >>> data = create_content_data(entry, "test_source", "content text")
    >>> print(data["title"])
    Test
    """
    url = normalize_url(entry.link)
    content_hash = text_hash(raw_text or url)
    
    # 언어 감지 (한국어 포함 여부)
    lang = "ko" if any(c in raw_text for c in "가나다라마바사아자차카타파하") else "en"
    
    # 임시 요약 및 태그 생성
    temp_summary = [
        f"기사 제목: {entry.title}",
        f"출처: {source_name}",
        f"발행일: {entry.get('published', 'N/A')}",
        "요약 작업 대기 중..."
    ]
    
    temp_tags = ["rss", source_name.replace("rss:", ""), "pending_summary"]
    
    # 발행일 파싱
    published_at = None
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        try:
            published_at = datetime(*entry.published_parsed[:6])
        except (TypeError, ValueError):
            pass
    
    return {
        "source": source_name,
        "title": entry.title[:512],
        "author": getattr(entry, "author", None),
        "url": url,
        "published_at": published_at,
        "raw_text": raw_text,
        "lang": lang,
        "hash": content_hash,
        "summary_bullets": temp_summary,
        "insight": None,
        "tags": temp_tags,
    }

def save_content_to_db(content_data: Dict[str, Any], db: Session) -> Optional[int]:
    """
    콘텐츠 데이터를 데이터베이스에 저장 (I/O)
    
    Parameters
    ----------
    content_data : Dict[str, Any]
        저장할 콘텐츠 데이터
    db : Session
        데이터베이스 세션
        
    Returns
    -------
    Optional[int]
        저장된 콘텐츠의 ID, 중복인 경우 None
        
    Examples
    --------
    >>> content_id = save_content_to_db(content_data, db_session)
    >>> if content_id:
    ...     print(f"Saved with ID: {content_id}")
    """
    # 중복 체크
    existing = db.query(Content).filter_by(hash=content_data["hash"]).first()
    if existing:
        return None
    
    # 새 콘텐츠 생성
    content = Content(**content_data)
    db.add(content)
    db.flush()  # ID를 얻기 위해 flush
    
    return content.id

def ingest_rss(feed_url: str, source_name: str = "rss", db: Session | None = None) -> Dict[str, Any]:
    """
    RSS 피드에서 콘텐츠 수집 및 저장
    
    Parameters
    ----------
    feed_url : str
        RSS 피드 URL
    source_name : str, optional
        소스 이름, 기본값 "rss"
    db : Session | None, optional
        데이터베이스 세션, None이면 새 세션 생성
        
    Returns
    -------
    Dict[str, Any]
        수집 결과 통계
        - processed: 처리된 엔트리 수
        - saved: 저장된 콘텐츠 수
        - duplicates: 중복된 콘텐츠 수
        - queued_tasks: 큐잉된 태스크 수
        
    Examples
    --------
    >>> result = ingest_rss("https://example.com/feed.xml", "example_source")
    >>> print(f"Saved {result['saved']} new contents")
    """
    try:
        print(f"ingest_rss 시작 - feed_url: {feed_url}, source_name: {source_name}")
        
        db = db or SessionLocal()
        print(f"데이터베이스 세션 생성 완료")
        
        # RSS 피드 파싱
        feed = feedparser.parse(feed_url)
        print(f"RSS 피드 파싱 완료 - 엔트리 수: {len(feed.entries)}")
        
        processed = 0
        saved = 0
        duplicates = 0
        queued_tasks = 0
        
        for entry in feed.entries:
            processed += 1
            
            # 콘텐츠 텍스트 가져오기 (I/O)
            fallback_summary = entry.get("summary", "") or ""
            raw_text, fetch_method = fetch_content_text(entry.link, fallback_summary)
            
            # 콘텐츠 데이터 생성 (Pure Function)
            content_data = create_content_data(entry, source_name, raw_text)
            
            # 데이터베이스 저장 (I/O)
            content_id = save_content_to_db(content_data, db)
            
            if content_id:
                saved += 1
                # Celery 태스크 큐잉 (I/O)
                summarize_task.delay(content_id)
                queued_tasks += 1
            else:
                duplicates += 1
        
        # 트랜잭션 커밋
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"RSS 수집 중 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    print(f"RSS 수집 완료 - processed: {processed}, saved: {saved}, duplicates: {duplicates}")
    
    return {
        "processed": processed,
        "saved": saved,
        "duplicates": duplicates,
        "queued_tasks": queued_tasks,
        "feed_url": feed_url,
        "source_name": source_name
    }
