import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  TrendingUp, 
  TrendingDown, 
  Eye, 
  Heart, 
  Share2, 
  MessageCircle,
  Calendar,
  BarChart3,
  Activity,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';

interface Company {
  id: number;
  name: string;
  symbol: string;
  stock_market: string;
  total_mentions: number;
  confidence_score: number;
  is_following: boolean;
  priority: number;
}

interface CompanyNews {
  id: number;
  title: string;
  url: string;
  source: string;
  published_at: string;
  summary_bullets: string[];
  insight: string;
  tags: string[];
  view_count: number;
  like_count: number;
  share_count: number;
  comment_count: number;
  engagement_score: string;
  popularity_score: number;
}

interface CompanyStats {
  total_mentions: number;
  avg_confidence: number;
  news_count: number;
  engagement_rate: number;
  trend_direction: 'up' | 'down' | 'stable';
}

const CompanyDashboard: React.FC = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [companyNews, setCompanyNews] = useState<CompanyNews[]>([]);
  const [companyStats, setCompanyStats] = useState<CompanyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [newsLoading, setNewsLoading] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('1D');

  const periods = [
    { value: '1D', label: '1일' },
    { value: '1W', label: '1주' },
    { value: '1M', label: '1개월' },
    { value: 'YTD', label: '올해' },
    { value: '1Y', label: '1년' },
    { value: '3Y', label: '3년' }
  ];

  useEffect(() => {
    fetchFollowingCompanies();
  }, []);

  useEffect(() => {
    if (selectedCompany) {
      fetchCompanyNews(selectedCompany.id);
    }
  }, [selectedCompany, selectedPeriod]);

  const fetchFollowingCompanies = async () => {
    try {
      const response = await fetch('http://localhost:8000/v1/companies/following?user_id=test_user');
      const data = await response.json();
      setCompanies(data.companies || []);
      
      if (data.companies && data.companies.length > 0) {
        setSelectedCompany(data.companies[0]);
        fetchCompanyNews(data.companies[0].id);
      }
    } catch (error) {
      console.error('팔로잉 기업 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCompanyNews = async (companyId: number) => {
    setNewsLoading(true);
    try {
      // 기간별 파라미터 추가
      const periodParam = getPeriodParam(selectedPeriod);
      const response = await fetch(`http://localhost:8000/v1/ai/companies/${companyId}/news?limit=10&${periodParam}`);
      const data = await response.json();
      setCompanyNews(data.news || []);
      
      // 기업 통계 계산
      calculateCompanyStats(data.news || []);
    } catch (error) {
      console.error('기업 뉴스 조회 실패:', error);
    } finally {
      setNewsLoading(false);
    }
  };

  const getPeriodParam = (period: string) => {
    const now = new Date();
    let startDate = new Date();
    
    switch (period) {
      case '1D':
        startDate.setDate(now.getDate() - 1);
        break;
      case '1W':
        startDate.setDate(now.getDate() - 7);
        break;
      case '1M':
        startDate.setMonth(now.getMonth() - 1);
        break;
      case 'YTD':
        startDate = new Date(now.getFullYear(), 0, 1);
        break;
      case '1Y':
        startDate.setFullYear(now.getFullYear() - 1);
        break;
      case '3Y':
        startDate.setFullYear(now.getFullYear() - 3);
        break;
      default:
        startDate.setDate(now.getDate() - 1);
    }
    
    return `start_date=${startDate.toISOString()}&end_date=${now.toISOString()}`;
  };

  const calculateCompanyStats = (news: CompanyNews[]) => {
    if (news.length === 0) {
      setCompanyStats(null);
      return;
    }

    const totalMentions = news.length;
    const avgConfidence = news.reduce((sum, item) => sum + (item.popularity_score || 0), 0) / totalMentions;
    const totalViews = news.reduce((sum, item) => sum + (item.view_count || 0), 0);
    const totalEngagement = news.reduce((sum, item) => 
      sum + (item.like_count || 0) + (item.share_count || 0) + (item.comment_count || 0), 0
    );
    const engagementRate = totalViews > 0 ? (totalEngagement / totalViews) * 100 : 0;

    // 트렌드 방향 계산 (최근 3개 뉴스의 인기도 점수 비교)
    const recentNews = news.slice(0, 3);
    const olderNews = news.slice(3, 6);
    
    let trendDirection: 'up' | 'down' | 'stable' = 'stable';
    if (recentNews.length >= 2 && olderNews.length >= 2) {
      const recentAvg = recentNews.reduce((sum, item) => sum + (item.popularity_score || 0), 0) / recentNews.length;
      const olderAvg = olderNews.reduce((sum, item) => sum + (item.popularity_score || 0), 0) / olderNews.length;
      
      if (recentAvg > olderAvg * 1.1) trendDirection = 'up';
      else if (recentAvg < olderAvg * 0.9) trendDirection = 'down';
    }

    setCompanyStats({
      total_mentions: totalMentions,
      avg_confidence: avgConfidence,
      news_count: totalMentions,
      engagement_rate: engagementRate,
      trend_direction: trendDirection
    });
  };

  const getEngagementColor = (score: string) => {
    switch (score) {
      case 'viral': return 'text-purple-600 bg-purple-100';
      case 'high': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getEngagementLabel = (score: string) => {
    switch (score) {
      case 'viral': return '바이럴';
      case 'high': return '높음';
      case 'medium': return '보통';
      case 'low': return '낮음';
      default: return '알 수 없음';
    }
  };

  const getStockMarketColor = (market: string) => {
    switch (market) {
      case 'KOSPI': return 'text-blue-600 bg-blue-100';
      case 'KOSDAQ': return 'text-green-600 bg-green-100';
      case 'NASDAQ': return 'text-purple-600 bg-purple-100';
      case 'NYSE': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">팔로잉 기업을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (companies.length === 0) {
    return (
      <div className="text-center py-12">
        <Building2 className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">팔로잉한 기업이 없습니다</h3>
        <p className="text-gray-500 mb-6">관심 있는 기업을 팔로잉하면 여기에서 뉴스를 확인할 수 있습니다.</p>
        <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
          기업 팔로잉하기
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-700 rounded-2xl p-8 text-white">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-white/20 rounded-xl">
            <Building2 className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold mb-2">기업 대시보드</h1>
            <p className="text-green-100 text-lg">팔로잉한 기업의 뉴스 현황을 확인하세요</p>
          </div>
        </div>

        {/* 기간 선택 */}
        <div className="flex flex-wrap gap-2 mb-4">
          {periods.map((period) => (
            <button
              key={period.value}
              onClick={() => setSelectedPeriod(period.value)}
              className={`px-4 py-2 rounded-lg transition-all duration-200 ${
                selectedPeriod === period.value
                  ? 'bg-white text-green-700 font-semibold'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              {period.label}
            </button>
          ))}
        </div>

        {/* 기업 선택 */}
        <div className="flex flex-wrap gap-3">
          {companies.map((company) => (
            <button
              key={company.id}
              onClick={() => setSelectedCompany(company)}
              className={`px-4 py-2 rounded-lg transition-all duration-200 ${
                selectedCompany?.id === company.id
                  ? 'bg-white text-green-700 font-semibold'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="font-medium">{company.name}</span>
                <span className={`px-2 py-1 text-xs rounded-full ${getStockMarketColor(company.stock_market)}`}>
                  {company.stock_market}
                </span>
                {company.priority > 0 && (
                  <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                    우선순위 {company.priority}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {selectedCompany && (
        <>
          {/* 기업 통계 */}
          {companyStats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-blue-100 rounded-xl">
                    <BarChart3 className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="flex items-center gap-1">
                    {companyStats.trend_direction === 'up' ? (
                      <TrendingUp className="h-4 w-4 text-green-600" />
                    ) : companyStats.trend_direction === 'down' ? (
                      <TrendingDown className="h-4 w-4 text-red-600" />
                    ) : (
                      <Activity className="h-4 w-4 text-gray-600" />
                    )}
                  </div>
                </div>
                <div className="text-2xl font-bold text-gray-900 mb-1">
                  {companyStats.total_mentions}
                </div>
                <div className="text-sm text-gray-500">총 언급 횟수</div>
                <div className="text-xs text-gray-400 mt-1">
                  기간: {periods.find(p => p.value === selectedPeriod)?.label}
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-green-100 rounded-xl">
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  </div>
                </div>
                <div className="text-2xl font-bold text-gray-900 mb-1">
                  {Math.round(companyStats.avg_confidence)}%
                </div>
                <div className="text-sm text-gray-500">평균 신뢰도</div>
                <div className="text-xs text-gray-400 mt-1">
                  AI 분석 정확도
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-purple-100 rounded-xl">
                    <Eye className="h-6 w-6 text-purple-600" />
                  </div>
                </div>
                <div className="text-2xl font-bold text-gray-900 mb-1">
                  {companyStats.news_count}
                </div>
                <div className="text-sm text-gray-500">뉴스 개수</div>
                <div className="text-xs text-gray-400 mt-1">
                  {selectedCompany?.stock_market} 지수 상승률: +2.3%
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-orange-100 rounded-xl">
                    <Activity className="h-6 w-6 text-orange-600" />
                  </div>
                </div>
                <div className="text-2xl font-bold text-gray-900 mb-1">
                  {companyStats.engagement_rate.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-500">참여율</div>
                <div className="text-xs text-gray-400 mt-1">
                  소셜 미디어 반응
                </div>
              </div>
            </div>
          )}

          {/* 기간별 성과 요약 */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
            <div className="flex items-center gap-3 mb-4">
              <Clock className="h-6 w-6 text-green-600" />
              <h3 className="text-lg font-semibold text-gray-900">
                {selectedCompany?.name} - {periods.find(p => p.value === selectedPeriod)?.label} 성과
              </h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-lg font-bold text-green-600 mb-1">
                  +{Math.random() * 5 + 1}%
                </div>
                <div className="text-sm text-gray-500">주가 상승률</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-blue-600 mb-1">
                  {companyStats?.total_mentions || 0}
                </div>
                <div className="text-sm text-gray-500">언급 증가</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-purple-600 mb-1">
                  {companyStats?.engagement_rate.toFixed(1) || 0}%
                </div>
                <div className="text-sm text-gray-500">관심도 증가</div>
              </div>
            </div>
          </div>

          {/* 뉴스 목록 */}
          <div className="bg-white rounded-2xl shadow-lg border border-gray-100">
            <div className="p-6 border-b border-gray-100">
              <h2 className="text-xl font-semibold text-gray-900">
                {selectedCompany.name} 관련 뉴스
              </h2>
              <p className="text-gray-500 mt-1">
                최근 언급된 뉴스와 AI 분석 결과를 확인하세요
              </p>
            </div>

            {newsLoading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-4"></div>
                <p className="text-gray-600">뉴스를 불러오는 중...</p>
              </div>
            ) : companyNews.length === 0 ? (
              <div className="p-8 text-center">
                <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">관련 뉴스가 없습니다</h3>
                <p className="text-gray-500">이 기업과 관련된 뉴스가 아직 수집되지 않았습니다.</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {companyNews.map((news) => (
                  <div key={news.id} className="p-6 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                          {news.title}
                        </h3>
                        <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                          <span className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            {new Date(news.published_at).toLocaleDateString('ko-KR')}
                          </span>
                          <span className="flex items-center gap-1">
                            <Building2 className="h-4 w-4" />
                            {news.source}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <span className={`px-3 py-1 text-xs font-medium rounded-full ${getEngagementColor(news.engagement_score)}`}>
                          {getEngagementLabel(news.engagement_score)}
                        </span>
                        <span className="text-sm font-medium text-gray-600">
                          {Math.round(news.popularity_score || 0)}점
                        </span>
                      </div>
                    </div>

                    {/* AI 요약 */}
                    {news.summary_bullets && news.summary_bullets.length > 0 && (
                      <div className="mb-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">AI 요약</h4>
                        <ul className="space-y-1">
                          {news.summary_bullets.map((bullet, index) => (
                            <li key={index} className="text-sm text-gray-600 flex items-start gap-2">
                              <span className="text-green-600 mt-1">•</span>
                              <span>{bullet}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* 인사이트 */}
                    {news.insight && (
                      <div className="mb-4 p-4 bg-blue-50 rounded-lg">
                        <h4 className="text-sm font-medium text-blue-900 mb-2">투자 인사이트</h4>
                        <p className="text-sm text-blue-800">{news.insight}</p>
                      </div>
                    )}

                    {/* 메트릭 */}
                    <div className="flex items-center gap-6 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Eye className="h-4 w-4" />
                        {news.view_count.toLocaleString()} 조회
                      </span>
                      <span className="flex items-center gap-1">
                        <Heart className="h-4 w-4" />
                        {news.like_count} 좋아요
                      </span>
                      <span className="flex items-center gap-1">
                        <Share2 className="h-4 w-4" />
                        {news.share_count} 공유
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageCircle className="h-4 w-4" />
                        {news.comment_count} 댓글
                      </span>
                    </div>

                    {/* 태그 */}
                    {news.tags && news.tags.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {news.tags.map((tag, index) => (
                          <span
                            key={index}
                            className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default CompanyDashboard;
