from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String, func
from .db import SessionLocal
from ..models.content import Content

class ContentRepo:
    """콘텐츠 저장소 클래스
    
    데이터베이스에서 콘텐츠를 조회, 생성, 수정하는 기능을 제공합니다.
    """
    
    def __init__(self, db: Session | None = None):
        """
        ContentRepo 초기화
        
        Parameters
        ----------
        db : Session | None, optional
            데이터베이스 세션. None이면 새 세션 생성
        """
        self.db = db or SessionLocal()

    def list_contents(self, tags: Optional[List[str]], limit: int, offset: int, keyword: Optional[str] = None):
        """
        콘텐츠 목록 조회
        
        Parameters
        ----------
        tags : Optional[List[str]]
            필터링할 태그 목록
        limit : int
            반환할 최대 콘텐츠 수
        offset : int
            시작 오프셋
        keyword : Optional[str], optional
            검색 키워드
            
        Returns
        -------
        List[Content]
            조건에 맞는 콘텐츠 목록
            
        Examples
        --------
        >>> repo = ContentRepo()
        >>> # 모든 콘텐츠 조회
        >>> contents = repo.list_contents(tags=None, limit=10, offset=0)
        >>> 
        >>> # AI 태그 필터링
        >>> ai_contents = repo.list_contents(tags=["ai"], limit=5, offset=0)
        >>> 
        >>> # 키워드 검색
        >>> search_results = repo.list_contents(tags=None, limit=10, offset=0, keyword="OpenAI")
        """
        q = self.db.query(Content).order_by(Content.published_at.desc().nullslast())
        
        # 태그 필터링
        if tags:
            tag_text = cast(Content.tags, String)
            tag_conds = [tag_text.ilike(f"%{t}%") for t in tags if t]
            if tag_conds:
                q = q.filter(or_(*tag_conds))
                
        # 키워드 검색
        if keyword:
            kw = f"%{keyword}%"
            q = q.filter(
                or_(
                    Content.title.ilike(kw),
                    Content.author.ilike(kw),
                    Content.url.ilike(kw),
                    Content.raw_text.ilike(kw),
                    cast(Content.tags, String).ilike(kw),
                    cast(Content.summary_bullets, String).ilike(kw),
                    cast(Content.insight, String).ilike(kw),
                )
            )
            
        rows = q.offset(offset).limit(limit).all()
        return rows
    
    def get_by_id(self, content_id: int) -> Optional[Content]:
        """
        ID로 콘텐츠 조회
        
        Parameters
        ----------
        content_id : int
            조회할 콘텐츠 ID
            
        Returns
        -------
        Optional[Content]
            찾은 콘텐츠 또는 None
            
        Examples
        --------
        >>> repo = ContentRepo()
        >>> content = repo.get_by_id(123)
        >>> if content:
        ...     print(content.title)
        """
        return self.db.query(Content).filter_by(id=content_id).first()
    
    def get_popular_tags(self, limit: int = 20) -> List[str]:
        """
        인기 태그 목록 조회
        
        Parameters
        ----------
        limit : int, optional
            반환할 최대 태그 수, 기본값 20
            
        Returns
        -------
        List[str]
            사용 빈도가 높은 태그 목록
            
        Examples
        --------
        >>> repo = ContentRepo()
        >>> popular_tags = repo.get_popular_tags(10)
        >>> print(popular_tags[:5])  # 상위 5개 태그
        """
        # PostgreSQL JSON 배열에서 태그 추출 및 빈도 계산
        # 실제 구현에서는 더 복잡한 쿼리가 필요할 수 있음
        try:
            # JSONB 배열을 unnest하여 개별 태그로 분리하고 빈도 계산
            query = """
            SELECT tag, COUNT(*) as count
            FROM (
                SELECT jsonb_array_elements_text(tags) as tag
                FROM content 
                WHERE tags IS NOT NULL
            ) t
            GROUP BY tag
            ORDER BY count DESC
            LIMIT :limit
            """
            result = self.db.execute(query, {"limit": limit})
            return [row[0] for row in result.fetchall()]
        except Exception:
            # 폴백: 간단한 방법으로 태그 추출
            contents = self.db.query(Content).filter(Content.tags.isnot(None)).all()
            tag_counts = {}
            for content in contents:
                if content.tags:
                    for tag in content.tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # 빈도순 정렬하여 상위 N개 반환
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            return [tag for tag, count in sorted_tags[:limit]]
