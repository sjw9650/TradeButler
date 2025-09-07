from .celery_app import celery
from ..repo.db import SessionLocal
from ..models.content import Content, AICache
from ..models.cost_log import CostLog
from ..core.config import settings
from ..utils.cost_calculator import calculate_openai_cost
from ..services.popular_news_analyzer import PopularNewsAnalyzer
from ..services.social_metrics_collector import SocialMetricsCollector
import json
from openai import OpenAI
from typing import List, Dict, Any
from datetime import datetime

# OpenAI 클라이언트 설정
client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

MODEL_VERSION = "gpt-3.5-turbo"

def get_cached_result(content_hash: str, model_version: str, db: any) -> Dict[str, Any] | None:
    """
    캐시에서 AI 결과 조회
    
    Parameters
    ----------
    content_hash : str
        콘텐츠 해시 값
    model_version : str
        AI 모델 버전 (예: "gpt-3.5-turbo")
    db : any
        데이터베이스 세션 객체
        
    Returns
    -------
    Dict[str, Any] | None
        캐시된 AI 결과 또는 None
        
    Examples
    --------
    >>> cached = get_cached_result("abc123", "gpt-3.5-turbo", db_session)
    >>> if cached:
    ...     print(f"Found cached result: {cached['status']}")
    """
    cached = db.query(AICache).filter_by(
        content_hash=content_hash, 
        model_version=model_version
    ).first()
    
    if cached:
        return {
            "status": "cached",
            "summary_bullets": cached.summary_bullets,
            "tags": cached.tags,
            "insight": cached.insight
        }
    return None

def save_to_cache(content_hash: str, model_version: str, summary_bullets: List[str], 
                  tags: List[str], insight: str, db: any):
    """
    AI 결과를 캐시에 저장
    
    Parameters
    ----------
    content_hash : str
        콘텐츠 해시 값
    model_version : str
        AI 모델 버전
    summary_bullets : List[str]
        생성된 요약 포인트 목록
    tags : List[str]
        생성된 태그 목록
    insight : str
        생성된 인사이트 텍스트
    db : any
        데이터베이스 세션 객체
        
    Examples
    --------
    >>> save_to_cache("abc123", "gpt-3.5-turbo", 
    ...               ["point1", "point2"], ["tag1", "tag2"], 
    ...               "insight text", db_session)
    """
    cache_entry = AICache(
        content_hash=content_hash,
        model_version=model_version,
        summary_bullets=summary_bullets,
        tags=tags,
        insight=insight
    )
    db.add(cache_entry)

def call_openai_summary(content: Content) -> Dict[str, Any]:
    """
    OpenAI API를 호출하여 콘텐츠 요약 및 태그 생성
    
    Parameters
    ----------
    content : Content
        분석할 콘텐츠 객체
        
    Returns
    -------
    Dict[str, Any]
        AI 분석 결과
        - status: 처리 상태 ("success", "api_error", "json_error")
        - summary_bullets: 요약 포인트 목록 (최대 5개)
        - tags: 태그 목록 (최대 8개)
        - insight: 인사이트 텍스트 (최대 500자)
        - error: 오류 메시지 (오류 시에만)
        
    Examples
    --------
    >>> content = Content(title="AI News", raw_text="AI is advancing...")
    >>> result = call_openai_summary(content)
    >>> if result["status"] == "success":
    ...     print(f"Generated {len(result['summary_bullets'])} summaries")
    """
    try:
        if not client:
            raise Exception("OpenAI API key not configured")
            
        # 콘텐츠 텍스트 준비 (제목 + 본문)
        text_to_analyze = f"제목: {content.title}\n\n본문: {content.raw_text[:3000]}"  # 3000자 제한
        
        # 개선된 프롬프트
        system_prompt = """당신은 뉴스 기사를 분석하는 전문 AI 어시스턴트입니다. 
주어진 기사를 분석하여 정확히 다음 형식의 JSON으로 응답해주세요:

{
    "summary_bullets": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
    "tags": ["태그1", "태그2", "태그3", "태그4", "태그5"],
    "insight": "이 기사의 주요 인사이트나 의미를 2-3문장으로 설명"
}

엄격한 요구사항:
- summary_bullets: 정확히 3-5개의 핵심 포인트 (각각 한 문장, 구체적이고 명확하게)
- tags: 정확히 5-8개의 관련 태그 (소문자, 영문, 구체적인 키워드)
- insight: 정확히 2-3문장으로 기사의 의미와 중요성 분석

JSON 형식을 정확히 준수하고, 다른 텍스트는 포함하지 마세요."""

        # OpenAI API 호출
        response = client.chat.completions.create(
            model=MODEL_VERSION,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_to_analyze}
            ],
            max_tokens=1200,
            temperature=0.3,  # 더 일관된 결과를 위해 낮춤
            response_format={"type": "json_object"}  # JSON 응답 강제
        )
        
        # 토큰 사용량 및 비용 계산
        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens
        cost_usd, cost_breakdown = calculate_openai_cost(MODEL_VERSION, tokens_in, tokens_out)
        
        # 응답 파싱
        result = json.loads(response.choices[0].message.content)
        
        # 결과 검증 및 정제
        summary_bullets = result.get("summary_bullets", [])[:5]  # 최대 5개
        tags = result.get("tags", [])[:8]  # 최대 8개
        insight = result.get("insight", "")[:500]  # 최대 500자
        
        return {
            "status": "success",
            "summary_bullets": summary_bullets,
            "tags": tags,
            "insight": insight,
            "cost_info": {
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": cost_usd,
                "cost_breakdown": cost_breakdown
            }
        }
        
    except json.JSONDecodeError:
        # JSON 파싱 실패 시 fallback
        return {
            "status": "json_error",
            "summary_bullets": [
                f"기사 분석: {content.title}",
                f"출처: {content.source}",
                "AI 분석 중 JSON 파싱 오류 발생"
            ],
            "tags": ["ai_processed", "json_error"],
            "insight": "AI 분석 중 JSON 파싱 오류가 발생했습니다. 콘텐츠는 수집되었으나 상세 분석이 제한됩니다."
        }
    except Exception as e:
        # API 호출 실패 시 fallback
        return {
            "status": "api_error",
            "error": str(e),
            "summary_bullets": [
                f"📰 {content.title}",
                f"📅 발행일: {content.published_at.strftime('%Y-%m-%d') if content.published_at else 'N/A'}",
                f"🔗 출처: {content.source}",
                "⚠️ OpenAI API 호출 실패로 fallback 요약 사용"
            ][:5],
            "tags": ["fallback", "api_error"],
            "insight": f"OpenAI API 호출 중 오류가 발생했습니다: {str(e)[:200]}. 기본 요약을 제공합니다."
        }

@celery.task(name="tasks.summarize")
def summarize_task(content_id: int):
    """
    콘텐츠를 요약하고 태그를 생성하는 Celery 태스크 (캐시 포함)
    
    Parameters
    ----------
    content_id : int
        처리할 콘텐츠의 ID
        
    Returns
    -------
    Dict[str, Any]
        태스크 실행 결과
        - content_id: 처리된 콘텐츠 ID
        - status: 실행 상태 ("success", "not_found", "error")
        - ai_status: AI 처리 상태 ("success", "cached", "api_error", "json_error")
        - summary_length: 생성된 요약 포인트 수
        - tags_count: 최종 태그 수
        - cached: 캐시 사용 여부
        - error: 오류 메시지 (오류 시에만)
        
    Examples
    --------
    >>> # Celery를 통해 비동기 실행
    >>> task = summarize_task.delay(123)
    >>> result = task.get()
    >>> print(f"Processed content {result['content_id']}")ㄴ
    
    >>> # 직접 실행 (테스트용)
    >>> result = summarize_task(123)
    >>> if result["status"] == "success":
    ...     print(f"AI status: {result['ai_status']}")
    """
    db = SessionLocal()
    try:
        # 콘텐츠 조회
        content = db.query(Content).filter_by(id=content_id).first()
        if not content:
            return {"content_id": content_id, "status": "not_found"}
        
        # 캐시 확인
        cached_result = get_cached_result(content.hash, MODEL_VERSION, db)
        if cached_result:
            # 캐시된 결과 사용
            ai_result = cached_result
        else:
            # OpenAI API 호출
            ai_result = call_openai_summary(content)
            
            # 성공한 경우만 캐시에 저장
            if ai_result.get("status") == "success":
                save_to_cache(
                    content.hash, MODEL_VERSION,
                    ai_result.get("summary_bullets", []),
                    ai_result.get("tags", []),
                    ai_result.get("insight", ""),
                    db
                )
        
        # 기존 태그와 병합
        existing_tags = content.tags or []
        if "pending_summary" in existing_tags:
            existing_tags.remove("pending_summary")
        
        # AI가 생성한 태그와 기존 태그 병합
        ai_tags = ai_result.get("tags", [])
        improved_tags = list(set(existing_tags + ai_tags + ["ai_summarized", "processed"]))
        
        # 언어별 태그 추가
        if content.lang == "ko":
            improved_tags.append("korean")
        else:
            improved_tags.append("english")
        
        # 제목에서 키워드 태그 추가 (기존 로직 유지)
        title_lower = content.title.lower()
        if any(word in title_lower for word in ["ai", "artificial", "intelligence"]):
            improved_tags.append("ai")
        if any(word in title_lower for word in ["tech", "technology"]):
            improved_tags.append("technology")
        if any(word in title_lower for word in ["crypto", "bitcoin", "blockchain"]):
            improved_tags.append("cryptocurrency")
        
        # 중복 제거 및 상위 N개 선택
        improved_tags = list(set(improved_tags))[:15]  # 최대 15개 태그
        
        # 데이터베이스 업데이트
        content.summary_bullets = ai_result.get("summary_bullets", [])
        content.tags = improved_tags
        content.insight = ai_result.get("insight", f"AI 분석: {content.title}")
        
        db.commit()
        
        return {
            "content_id": content_id, 
            "status": "success",
            "ai_status": ai_result.get("status", "unknown"),
            "summary_length": len(content.summary_bullets),
            "tags_count": len(improved_tags),
            "cached": cached_result is not None
        }
        
    except Exception as e:
        db.rollback()
        return {"content_id": content_id, "status": "error", "error": str(e)}
    finally:
        db.close()


@celery.task
def process_popular_news_task(limit: int = 10):
    """
    인기 뉴스 10개를 선별하고 AI 요약을 생성하는 태스크
    
    Parameters
    ----------
    limit : int
        처리할 뉴스 개수 (기본값: 10)
        
    Returns
    -------
    Dict[str, Any]
        처리 결과
    """
    db = SessionLocal()
    try:
        analyzer = PopularNewsAnalyzer(db)
        result = analyzer.process_popular_news(limit)
        
        logger.info(f"인기 뉴스 처리 태스크 완료: {result}")
        return result
        
    except Exception as e:
        logger.error(f"인기 뉴스 처리 태스크 실패: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery.task
def collect_social_metrics_task():
    """
    소셜 미디어 메트릭을 수집하는 태스크
    
    Returns
    -------
    Dict[str, Any]
        수집 결과
    """
    db = SessionLocal()
    try:
        # 최근 24시간 내의 뉴스 중 메트릭이 없는 것들 조회
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        contents = db.query(Content).filter(
            and_(
                Content.published_at >= cutoff_time,
                Content.is_active == "active",
                Content.view_count == 0  # 메트릭이 없는 것들
            )
        ).limit(50).all()  # 한 번에 50개씩 처리
        
        if not contents:
            return {
                "status": "no_content",
                "message": "수집할 메트릭이 없습니다.",
                "processed_count": 0
            }
        
        # 소셜 미디어 메트릭 수집기 초기화
        collector = SocialMetricsCollector()
        
        processed_count = 0
        results = []
        
        for content in contents:
            try:
                # 메트릭 수집
                metrics = collector.collect_metrics(content.url, content.source)
                
                # 데이터베이스 업데이트
                content.view_count = metrics.get('view_count', 0)
                content.like_count = metrics.get('like_count', 0)
                content.share_count = metrics.get('share_count', 0)
                content.comment_count = metrics.get('comment_count', 0)
                content.engagement_score = metrics.get('engagement_score', 'low')
                
                processed_count += 1
                results.append({
                    "content_id": content.id,
                    "title": content.title[:50] + "...",
                    "view_count": content.view_count,
                    "engagement_score": content.engagement_score
                })
                
            except Exception as e:
                logger.error(f"메트릭 수집 실패 (콘텐츠 {content.id}): {str(e)}")
                continue
        
        # 데이터베이스 커밋
        db.commit()
        
        logger.info(f"소셜 미디어 메트릭 수집 완료: {processed_count}/{len(contents)}")
        
        return {
            "status": "success",
            "processed_count": processed_count,
            "total_found": len(contents),
            "results": results
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"소셜 미디어 메트릭 수집 태스크 실패: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
