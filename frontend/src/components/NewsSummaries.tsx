import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  RefreshCw, 
  ExternalLink, 
  Calendar,
  User,
  Tag,
  Eye
} from 'lucide-react';
import { api, NewsSummary } from '../services/api';

const NewsSummaries: React.FC = () => {
  const [summaries, setSummaries] = useState<NewsSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedSource, setSelectedSource] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState<NewsSummary | null>(null);

  const limit = 20;

  useEffect(() => {
    fetchSummaries();
  }, [currentPage, searchKeyword, selectedSource]);

  const fetchSummaries = async () => {
    setIsLoading(true);
    try {
      const data = await api.getSummaries({
        limit,
        offset: currentPage * limit,
        keyword: searchKeyword || undefined,
        source: selectedSource || undefined,
        has_ai_summary: true
      });
      setSummaries(data.summaries || []);
      setHasMore(data.has_more || false);
    } catch (error) {
      console.error('요약 목록 조회 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(0);
    fetchSummaries();
  };

  const handleRegenerateSummary = async (contentId: number) => {
    try {
      await api.regenerateSummary(contentId);
      // 성공 메시지 표시
      console.log('요약 재생성 요청 완료');
    } catch (error) {
      console.error('요약 재생성 실패:', error);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getSourceDisplayName = (source: string) => {
    const sourceMap: Record<string, string> = {
      'rss:hankyung_economy': '한국경제 경제',
      'rss:hankyung_finance': '한국경제 금융',
      'rss:yahoo_news': 'Yahoo News',
      'rss:cnn_topstories': 'CNN',
      'rss:nyt_homepage': 'NYT',
      'rss:marketwatch_topstories': 'MarketWatch',
      'rss:cnbc_topstories': 'CNBC'
    };
    return sourceMap[source] || source;
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">뉴스 요약</h1>
        <p className="text-gray-600">AI가 분석한 뉴스 요약을 확인하세요</p>
      </div>

      {/* 검색 및 필터 */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="키워드 검색..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">모든 소스</option>
              <option value="rss:hankyung_economy">한국경제 경제</option>
              <option value="rss:hankyung_finance">한국경제 금융</option>
              <option value="rss:yahoo_news">Yahoo News</option>
              <option value="rss:cnn_topstories">CNN</option>
              <option value="rss:nyt_homepage">NYT</option>
              <option value="rss:marketwatch_topstories">MarketWatch</option>
              <option value="rss:cnbc_topstories">CNBC</option>
            </select>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
            >
              <Search className="h-4 w-4 mr-2" />
              검색
            </button>
          </div>
        </form>
      </div>

      {/* 요약 목록 */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin text-primary-600" />
          </div>
        ) : summaries.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">요약된 뉴스가 없습니다.</p>
          </div>
        ) : (
          summaries.map((summary) => (
            <div key={summary.id} className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {summary.title}
                  </h3>
                  <div className="flex items-center space-x-4 text-sm text-gray-500 mb-3">
                    <div className="flex items-center">
                      <User className="h-4 w-4 mr-1" />
                      {summary.author || 'Unknown'}
                    </div>
                    <div className="flex items-center">
                      <Calendar className="h-4 w-4 mr-1" />
                      {summary.published_at ? formatDate(summary.published_at) : 'N/A'}
                    </div>
                    <div className="flex items-center">
                      <Tag className="h-4 w-4 mr-1" />
                      {getSourceDisplayName(summary.source)}
                    </div>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setSelectedSummary(summary)}
                    className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 flex items-center"
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    상세보기
                  </button>
                  <button
                    onClick={() => handleRegenerateSummary(summary.id)}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 flex items-center"
                  >
                    <RefreshCw className="h-4 w-4 mr-1" />
                    재생성
                  </button>
                  <a
                    href={summary.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 flex items-center"
                  >
                    <ExternalLink className="h-4 w-4 mr-1" />
                    원문보기
                  </a>
                </div>
              </div>

              {/* AI 요약 */}
              {summary.summary_bullets && summary.summary_bullets.length > 0 && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">AI 요약</h4>
                  <ul className="space-y-1">
                    {summary.summary_bullets.map((bullet, index) => (
                      <li key={index} className="text-sm text-gray-600 flex items-start">
                        <span className="text-blue-500 mr-2">•</span>
                        {bullet}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 인사이트 */}
              {summary.insight && (
                <div className="mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">AI 인사이트</h4>
                  <p className="text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">
                    {summary.insight}
                  </p>
                </div>
              )}

              {/* 태그 */}
              {summary.tags && summary.tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {summary.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* 페이지네이션 */}
      {hasMore && (
        <div className="flex justify-center">
          <button
            onClick={() => setCurrentPage(currentPage + 1)}
            disabled={isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            더 보기
          </button>
        </div>
      )}

      {/* 상세보기 모달 */}
      {selectedSummary && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-xl font-bold text-gray-900">{selectedSummary.title}</h2>
                <button
                  onClick={() => setSelectedSummary(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              <div className="space-y-4">
                <div className="text-sm text-gray-600">
                  <p><strong>출처:</strong> {getSourceDisplayName(selectedSummary.source)}</p>
                  <p><strong>작성자:</strong> {selectedSummary.author || 'Unknown'}</p>
                  <p><strong>발행일:</strong> {selectedSummary.published_at ? formatDate(selectedSummary.published_at) : 'N/A'}</p>
                  <p><strong>언어:</strong> {selectedSummary.lang === 'ko' ? '한국어' : '영어'}</p>
                </div>

                {selectedSummary.summary_bullets && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">AI 요약</h3>
                    <ul className="space-y-2">
                      {selectedSummary.summary_bullets.map((bullet, index) => (
                        <li key={index} className="text-gray-700 flex items-start">
                          <span className="text-blue-500 mr-2">•</span>
                          {bullet}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {selectedSummary.insight && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">AI 인사이트</h3>
                    <p className="text-gray-700 bg-blue-50 p-4 rounded-lg">
                      {selectedSummary.insight}
                    </p>
                  </div>
                )}

                <div className="flex justify-end space-x-2">
                  <a
                    href={selectedSummary.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center"
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    원문보기
                  </a>
                  <button
                    onClick={() => handleRegenerateSummary(selectedSummary.id)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
                  >
                    <RefreshCw className="h-4 w-4 mr-2" />
                    요약 재생성
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NewsSummaries;
