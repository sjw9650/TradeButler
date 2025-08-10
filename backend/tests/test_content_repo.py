"""
ContentRepo 테스트 모듈

pytest를 사용하여 ContentRepo.list_contents 메서드를 테스트합니다.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from typing import List

from backend.app.repo.content import ContentRepo
from backend.app.models.content import Content


class TestContentRepo:
    """ContentRepo 클래스 테스트"""
    
    @pytest.fixture
    def mock_session(self):
        """가짜 데이터베이스 세션 픽스처"""
        return Mock()
    
    @pytest.fixture
    def sample_contents(self) -> List[Content]:
        """테스트용 샘플 콘텐츠 3건"""
        contents = [
            Content(
                id=1,
                source="rss:techcrunch",
                title="AI Revolutionizes Content Creation",
                author="John Doe",
                url="https://example.com/ai-content",
                published_at=datetime(2025, 1, 1, 12, 0, 0),
                raw_text="This article discusses AI in content creation...",
                lang="en",
                hash="hash1",
                summary_bullets=["AI tools are changing content", "New capabilities emerged"],
                insight="AI is transforming how we create content",
                tags=["ai", "content", "technology"]
            ),
            Content(
                id=2,
                source="rss:techcrunch", 
                title="Tech Trends 2025",
                author="Jane Smith",
                url="https://example.com/tech-trends",
                published_at=datetime(2025, 1, 2, 10, 0, 0),
                raw_text="This year will see major tech developments...",
                lang="en",
                hash="hash2",
                summary_bullets=["Blockchain adoption increases", "AI becomes mainstream"],
                insight="Technology trends are accelerating",
                tags=["tech", "trends", "blockchain", "ai"]
            ),
            Content(
                id=3,
                source="rss:news",
                title="한국 스타트업 생태계",
                author="김철수",
                url="https://example.com/korea-startup",
                published_at=datetime(2025, 1, 3, 14, 30, 0),
                raw_text="한국의 스타트업 생태계가 급성장하고 있습니다...",
                lang="ko",
                hash="hash3",
                summary_bullets=["스타트업 투자 증가", "새로운 기회 창출"],
                insight="한국 스타트업 생태계가 성숙해지고 있습니다",
                tags=["startup", "korea", "investment"]
            )
        ]
        return contents
    
    @pytest.fixture
    def content_repo(self, mock_session):
        """ContentRepo 인스턴스 픽스처"""
        return ContentRepo(db=mock_session)
    
    def test_list_contents_basic(self, content_repo, mock_session, sample_contents):
        """기본 콘텐츠 목록 조회 테스트"""
        # Given: 가짜 쿼리 결과 설정
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_contents
        
        # When: 모든 콘텐츠 조회
        result = content_repo.list_contents(tags=None, limit=10, offset=0)
        
        # Then: 결과 검증
        assert len(result) == 3
        assert result[0].title == "AI Revolutionizes Content Creation"
        assert result[1].title == "Tech Trends 2025"
        assert result[2].title == "한국 스타트업 생태계"
        
        # 쿼리 메서드 호출 검증
        mock_session.query.assert_called_once()
        mock_query.order_by.assert_called_once()
        mock_query.offset.assert_called_with(0)
        mock_query.limit.assert_called_with(10)
    
    def test_list_contents_with_tags_filter(self, content_repo, mock_session, sample_contents):
        """태그 필터링 테스트"""
        # Given: AI 태그가 있는 콘텐츠만 반환하도록 설정
        ai_contents = [content for content in sample_contents if "ai" in content.tags]
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = ai_contents
        
        # When: AI 태그로 필터링
        result = content_repo.list_contents(tags=["ai"], limit=10, offset=0)
        
        # Then: AI 태그가 있는 콘텐츠만 반환되는지 검증
        assert len(result) == 2
        assert all("ai" in content.tags for content in result)
        assert result[0].title == "AI Revolutionizes Content Creation"
        assert result[1].title == "Tech Trends 2025"
        
        # 필터 메서드가 호출되었는지 검증
        mock_query.filter.assert_called_once()
    
    def test_list_contents_with_keyword_search(self, content_repo, mock_session, sample_contents):
        """키워드 검색 테스트"""
        # Given: "AI"가 포함된 콘텐츠만 반환하도록 설정
        ai_contents = [content for content in sample_contents if "AI" in content.title]
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = ai_contents
        
        # When: "AI" 키워드로 검색
        result = content_repo.list_contents(tags=None, limit=10, offset=0, keyword="AI")
        
        # Then: AI가 포함된 제목의 콘텐츠만 반환되는지 검증
        assert len(result) == 1
        assert "AI" in result[0].title
        assert result[0].title == "AI Revolutionizes Content Creation"
        
        # 필터 메서드가 호출되었는지 검증
        mock_query.filter.assert_called_once()
    
    def test_list_contents_with_offset_and_limit(self, content_repo, mock_session, sample_contents):
        """오프셋과 리밋 테스트"""
        # Given: 두 번째 콘텐츠부터 1개만 반환하도록 설정
        paginated_content = [sample_contents[1]]  # 인덱스 1 (두 번째 아이템)
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = paginated_content
        
        # When: offset=1, limit=1로 조회
        result = content_repo.list_contents(tags=None, limit=1, offset=1)
        
        # Then: 두 번째 콘텐츠만 반환되는지 검증
        assert len(result) == 1
        assert result[0].title == "Tech Trends 2025"
        assert result[0].id == 2
        
        # offset과 limit이 올바르게 호출되었는지 검증
        mock_query.offset.assert_called_with(1)
        mock_query.limit.assert_called_with(1)
    
    def test_list_contents_combined_filters(self, content_repo, mock_session, sample_contents):
        """복합 필터 테스트 (태그 + 키워드)"""
        # Given: tech 태그와 "2025" 키워드 모두 만족하는 콘텐츠
        filtered_content = [sample_contents[1]]  # "Tech Trends 2025"
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = filtered_content
        
        # When: tech 태그와 "2025" 키워드로 검색
        result = content_repo.list_contents(tags=["tech"], limit=10, offset=0, keyword="2025")
        
        # Then: 조건에 맞는 콘텐츠만 반환되는지 검증
        assert len(result) == 1
        assert result[0].title == "Tech Trends 2025"
        assert "tech" in result[0].tags
        assert "2025" in result[0].title
        
        # 필터가 두 번 호출되었는지 검증 (태그 + 키워드)
        assert mock_query.filter.call_count == 2
    
    def test_list_contents_empty_result(self, content_repo, mock_session):
        """빈 결과 테스트"""
        # Given: 빈 결과 반환하도록 설정
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # When: 존재하지 않는 태그로 검색
        result = content_repo.list_contents(tags=["nonexistent"], limit=10, offset=0)
        
        # Then: 빈 리스트 반환 검증
        assert result == []
        assert len(result) == 0
    
    def test_list_contents_large_offset(self, content_repo, mock_session):
        """큰 오프셋 테스트"""
        # Given: 큰 오프셋으로 인해 빈 결과 반환
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        # When: 데이터보다 큰 오프셋으로 조회
        result = content_repo.list_contents(tags=None, limit=10, offset=1000)
        
        # Then: 빈 결과 반환 검증
        assert result == []
        mock_query.offset.assert_called_with(1000)
    
    def test_get_by_id_success(self, content_repo, mock_session, sample_contents):
        """ID로 콘텐츠 조회 성공 테스트"""
        # Given: 특정 ID의 콘텐츠 반환하도록 설정
        target_content = sample_contents[0]
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = target_content
        
        # When: ID 1로 콘텐츠 조회
        result = content_repo.get_by_id(1)
        
        # Then: 올바른 콘텐츠 반환 검증
        assert result is not None
        assert result.id == 1
        assert result.title == "AI Revolutionizes Content Creation"
        mock_query.filter_by.assert_called_with(id=1)
    
    def test_get_by_id_not_found(self, content_repo, mock_session):
        """ID로 콘텐츠 조회 실패 테스트"""
        # Given: 존재하지 않는 ID에 대해 None 반환
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = None
        
        # When: 존재하지 않는 ID로 조회
        result = content_repo.get_by_id(999)
        
        # Then: None 반환 검증
        assert result is None
        mock_query.filter_by.assert_called_with(id=999)
    
    def test_get_popular_tags_fallback(self, content_repo, mock_session, sample_contents):
        """인기 태그 조회 폴백 메서드 테스트"""
        # Given: SQL 쿼리 실행 실패로 폴백 메서드 사용
        mock_session.execute.side_effect = Exception("SQL Error")
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_contents
        
        # When: 인기 태그 조회
        result = content_repo.get_popular_tags(5)
        
        # Then: 폴백 메서드로 태그 반환 검증
        assert isinstance(result, list)
        assert len(result) <= 5
        # 가장 많이 사용된 태그들이 포함되어야 함
        assert "ai" in result  # 2번 사용됨
        assert "tech" in result or "technology" in result 