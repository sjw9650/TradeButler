from fastapi import APIRouter, Query, HTTPException, Path
from typing import List, Optional
from ...repo.content import ContentRepo
from ...schemas.content import ContentOut

router = APIRouter(tags=["feed"])

@router.get("/feed", response_model=List[ContentOut])
def get_feed(
    tags: Optional[str] = Query(default=None, description="태그 필터 (쉼표로 구분)"),
    keyword: Optional[str] = Query(default=None, description="키워드 검색"),
    limit: int = Query(default=50, ge=1, le=100, description="조회할 콘텐츠 수"),
    offset: int = Query(default=0, ge=0, description="시작 오프셋")
):
    """
    피드 목록 조회
    
    Parameters
    ----------
    tags : Optional[str]
        태그 필터 (예: "ai,tech")
    keyword : Optional[str] 
        제목, 내용, 태그에서 검색할 키워드
    limit : int
        반환할 최대 콘텐츠 수 (1-100)
    offset : int
        페이징을 위한 시작 오프셋
        
    Returns
    -------
    List[ContentOut]
        콘텐츠 목록
        
    Examples
    --------
    >>> # 모든 콘텐츠 조회
    >>> GET /v1/feed
    >>> 
    >>> # AI 관련 콘텐츠만 조회
    >>> GET /v1/feed?tags=ai&limit=10
    >>> 
    >>> # 키워드 검색
    >>> GET /v1/feed?keyword=OpenAI&limit=20
    """
    # 태그 리스트 파싱
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    
    # 레포지토리를 통해 콘텐츠 조회
    repo = ContentRepo()
    contents = repo.list_contents(
        tags=tag_list, 
        limit=limit, 
        offset=offset, 
        keyword=keyword
    )
    
    return contents

@router.get("/feed/{content_id}", response_model=ContentOut)
def get_content_by_id(
    content_id: int = Path(..., gt=0, description="콘텐츠 ID")
):
    """
    특정 콘텐츠 조회
    
    Parameters
    ----------
    content_id : int
        조회할 콘텐츠의 ID
        
    Returns
    -------
    ContentOut
        콘텐츠 상세 정보
        
    Raises
    ------
    HTTPException
        콘텐츠를 찾을 수 없는 경우 404 에러
        
    Examples
    --------
    >>> GET /v1/feed/123
    """
    repo = ContentRepo()
    content = repo.get_by_id(content_id)
    
    if not content:
        raise HTTPException(status_code=404, detail="콘텐츠를 찾을 수 없습니다")
    
    return content

@router.get("/feed/search/tags", response_model=List[str])
def get_popular_tags(
    limit: int = Query(default=20, ge=1, le=100, description="반환할 태그 수")
):
    """
    인기 태그 목록 조회
    
    Parameters
    ----------
    limit : int
        반환할 최대 태그 수
        
    Returns
    -------
    List[str]
        사용 빈도가 높은 태그 목록
        
    Examples
    --------
    >>> GET /v1/feed/search/tags?limit=10
    """
    repo = ContentRepo()
    return repo.get_popular_tags(limit=limit)
