import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  TrendingUp, 
  Search, 
  ExternalLink,
  Calendar,
  BarChart3,
  RefreshCw
} from 'lucide-react';
import { api, Company } from '../services/api';

const CompanyAnalysis: React.FC = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [companyNews, setCompanyNews] = useState<any[]>([]);
  const [isLoadingNews, setIsLoadingNews] = useState(false);

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    setIsLoading(true);
    try {
      const data = await api.getCompanies({
        keyword: searchKeyword || undefined,
        limit: 50
      });
      setCompanies(data.companies || []);
    } catch (error) {
      console.error('기업 목록 조회 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCompanyNews = async (companyName: string) => {
    setIsLoadingNews(true);
    try {
      const data = await api.getCompanyNews(companyName, { limit: 20 });
      setCompanyNews(data.news || []);
    } catch (error) {
      console.error('기업 뉴스 조회 실패:', error);
    } finally {
      setIsLoadingNews(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchCompanies();
  };

  const handleCompanyClick = (company: Company) => {
    setSelectedCompany(company);
    fetchCompanyNews(company.name);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
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
        <h1 className="text-2xl font-bold text-gray-900">기업 분석</h1>
        <p className="text-gray-600">뉴스에서 추출된 기업 정보와 관련 뉴스를 확인하세요</p>
      </div>

      {/* 검색 */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="기업명 검색..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
          >
            <Search className="h-4 w-4 mr-2" />
            검색
          </button>
        </form>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 기업 목록 */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-4 border-b">
              <h3 className="text-lg font-semibold text-gray-900">기업 목록</h3>
              <p className="text-sm text-gray-600">언급 횟수 순으로 정렬</p>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
                </div>
              ) : companies.length === 0 ? (
                <div className="p-4 text-center text-gray-500">
                  기업 정보가 없습니다.
                </div>
              ) : (
                companies.map((company) => (
                  <div
                    key={company.name}
                    onClick={() => handleCompanyClick(company)}
                    className={`p-4 border-b cursor-pointer hover:bg-gray-50 transition-colors ${
                      selectedCompany?.name === company.name ? 'bg-blue-50 border-blue-200' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{company.name}</h4>
                        <p className="text-sm text-gray-600">
                          {company.mention_count}회 언급
                        </p>
                        {company.latest_news && (
                          <p className="text-xs text-gray-500 mt-1">
                            최신: {formatDate(company.latest_news.published_at || '')}
                          </p>
                        )}
                      </div>
                      <TrendingUp className="h-4 w-4 text-gray-400" />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* 기업 상세 정보 및 뉴스 */}
        <div className="lg:col-span-2">
          {selectedCompany ? (
            <div className="space-y-6">
              {/* 기업 정보 */}
              <div className="bg-white p-6 rounded-lg shadow-sm border">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <Building2 className="h-6 w-6 text-blue-600 mr-3" />
                    <h2 className="text-xl font-bold text-gray-900">{selectedCompany.name}</h2>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-blue-600">{selectedCompany.mention_count}</p>
                    <p className="text-sm text-gray-600">언급 횟수</p>
                  </div>
                </div>

                {selectedCompany.latest_news && (
                  <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                    <h3 className="font-medium text-gray-900 mb-2">최신 뉴스</h3>
                    <p className="text-sm text-gray-700 mb-2">{selectedCompany.latest_news.title}</p>
                    <p className="text-xs text-gray-500">
                      {formatDate(selectedCompany.latest_news.published_at || '')}
                    </p>
                  </div>
                )}

                {selectedCompany.related_tags && selectedCompany.related_tags.length > 0 && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">관련 태그</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedCompany.related_tags.slice(0, 10).map((tag, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* 관련 뉴스 */}
              <div className="bg-white rounded-lg shadow-sm border">
                <div className="p-4 border-b">
                  <h3 className="text-lg font-semibold text-gray-900">관련 뉴스</h3>
                  <p className="text-sm text-gray-600">{selectedCompany.name} 관련 뉴스</p>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {isLoadingNews ? (
                    <div className="flex items-center justify-center py-8">
                      <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
                    </div>
                  ) : companyNews.length === 0 ? (
                    <div className="p-4 text-center text-gray-500">
                      관련 뉴스가 없습니다.
                    </div>
                  ) : (
                    companyNews.map((news) => (
                      <div key={news.id} className="p-4 border-b hover:bg-gray-50">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-medium text-gray-900 text-sm">{news.title}</h4>
                          <a
                            href={news.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </div>
                        <div className="flex items-center space-x-4 text-xs text-gray-500 mb-2">
                          <span>{getSourceDisplayName(news.source)}</span>
                          <span>{formatDate(news.published_at || '')}</span>
                        </div>
                        {news.summary_bullets && news.summary_bullets.length > 0 && (
                          <div className="text-xs text-gray-600">
                            <p className="line-clamp-2">{news.summary_bullets[0]}</p>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white p-12 rounded-lg shadow-sm border text-center">
              <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">기업을 선택하세요</h3>
              <p className="text-gray-600">왼쪽 목록에서 기업을 선택하면 상세 정보를 확인할 수 있습니다.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CompanyAnalysis;
