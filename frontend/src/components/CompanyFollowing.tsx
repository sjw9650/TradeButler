import React, { useState, useEffect } from 'react';
import { Search, Star, StarOff, TrendingUp, Building2, Filter, X } from 'lucide-react';

interface Company {
  id: number;
  name: string;
  display_name: string;
  industry: string;
  stock_symbol?: string;
  stock_market?: string;
  total_mentions: number;
  confidence_score: number;
  is_following: boolean;
  following_info?: {
    priority: number;
    notification_enabled: boolean;
    auto_summarize: boolean;
    followed_at: string;
  };
}

interface Recommendation {
  id: number;
  name: string;
  display_name: string;
  industry: string;
  stock_symbol?: string;
  stock_market?: string;
  total_mentions: number;
  confidence_score: number;
  recommendation_score: number;
  reason: string;
}

interface CompanyFollowingProps {
  userId: string;
}

const CompanyFollowing: React.FC<CompanyFollowingProps> = ({ userId }) => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [following, setFollowing] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [industryFilter, setIndustryFilter] = useState('');
  const [sortBy, setSortBy] = useState('mentions');
  const [order, setOrder] = useState('desc');
  const [activeTab, setActiveTab] = useState<'all' | 'following' | 'recommendations'>('all');
  const [showFilters, setShowFilters] = useState(false);

  // 기업 목록 조회
  const fetchCompanies = async () => {
    try {
      const params = new URLSearchParams({
        limit: '50',
        offset: '0',
        sort_by: sortBy,
        order: order,
        user_id: userId
      });

      if (searchTerm) params.append('search', searchTerm);
      if (industryFilter) params.append('industry', industryFilter);

      const response = await fetch(`/v1/companies/fast?${params}`);
      const data = await response.json();
      setCompanies(data.companies || []);
    } catch (error) {
      console.error('기업 목록 조회 실패:', error);
    }
  };

  // 팔로잉 기업 조회 (최적화된 API 사용)
  const fetchFollowing = async () => {
    try {
      const response = await fetch(`/v1/companies/following?user_id=${userId}`);
      const data = await response.json();
      setFollowing(data.companies || []);
    } catch (error) {
      console.error('팔로잉 기업 조회 실패:', error);
    }
  };

  // 추천 기업 조회
  const fetchRecommendations = async () => {
    try {
      const params = new URLSearchParams({
        limit: '10',
        user_id: userId
      });

      if (industryFilter) params.append('industry', industryFilter);

      const response = await fetch(`/v1/companies/recommendations/${userId}?${params}`);
      const data = await response.json();
      setRecommendations(data.recommendations || []);
    } catch (error) {
      console.error('추천 기업 조회 실패:', error);
    }
  };

  // 기업 팔로잉
  const followCompany = async (companyId: number, priority: number = 1) => {
    try {
      setLoading(true);
      
      const response = await fetch(`/v1/companies/${companyId}/follow/fast?user_id=${userId}&priority=${priority}`, {
        method: 'POST'
      });

      if (response.ok) {
        // 데이터 새로고침만 수행 (API에서 최신 상태 반환)
        await Promise.all([
          fetchCompanies(),
          fetchFollowing(),
          fetchRecommendations()
        ]);
      } else {
        console.error('팔로잉 실패:', await response.text());
      }
    } catch (error) {
      console.error('기업 팔로잉 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  // 기업 언팔로잉
  const unfollowCompany = async (companyId: number) => {
    try {
      setLoading(true);
      
      const response = await fetch(`/v1/companies/${companyId}/unfollow/fast?user_id=${userId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        // 데이터 새로고침만 수행 (API에서 최신 상태 반환)
        await Promise.all([
          fetchCompanies(),
          fetchFollowing(),
          fetchRecommendations()
        ]);
      } else {
        console.error('언팔로잉 실패:', await response.text());
      }
    } catch (error) {
      console.error('기업 언팔로잉 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchCompanies(),
        fetchFollowing(),
        fetchRecommendations()
      ]);
      setLoading(false);
    };

    loadData();
  }, [userId, searchTerm, industryFilter, sortBy, order]);

  const getIndustryOptions = () => {
    const industries = new Set([
      ...companies.map(c => c.industry).filter(Boolean),
      ...following.map(c => c.industry).filter(Boolean),
      ...recommendations.map(c => c.industry).filter(Boolean)
    ]);
    return Array.from(industries).sort();
  };

  const renderCompanyCard = (company: Company | Recommendation, isRecommendation = false) => {
    const isFollowing = 'is_following' in company ? company.is_following : false;
    const priority = 'following_info' in company ? company.following_info?.priority : 0;

    return (
      <div key={company.id} className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg hover:border-blue-300 transition-all duration-200 group">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            {/* 헤더 섹션 */}
            <div className="flex items-start gap-3 mb-3">
              <div className="flex-1 min-w-0">
                <h3 className="font-bold text-lg text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                  {company.display_name || company.name}
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  <Building2 className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-600">{company.industry || '미분류'}</span>
                </div>
              </div>
              
              {/* 배지들 */}
              <div className="flex flex-wrap gap-1.5">
                {company.stock_symbol && (
                  <span className="px-2 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-md border border-blue-200">
                    {company.stock_symbol}
                  </span>
                )}
                {company.stock_market && (
                  <span className={`px-2 py-1 text-xs font-medium rounded-md border ${
                    company.stock_market === 'KOSPI' ? 'bg-red-50 text-red-700 border-red-200' :
                    company.stock_market === 'KOSDAQ' ? 'bg-orange-50 text-orange-700 border-orange-200' :
                    company.stock_market === 'NASDAQ' ? 'bg-green-50 text-green-700 border-green-200' :
                    company.stock_market === 'NYSE' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                    'bg-gray-50 text-gray-700 border-gray-200'
                  }`}>
                    {company.stock_market}
                  </span>
                )}
                {isRecommendation && 'recommendation_score' in company && (
                  <span className="px-2 py-1 bg-emerald-50 text-emerald-700 text-xs font-medium rounded-md border border-emerald-200">
                    추천도 {company.recommendation_score}
                  </span>
                )}
              </div>
            </div>

            {/* 통계 섹션 */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-xs text-gray-500 mb-1">언급 횟수</div>
                <div className="text-lg font-semibold text-gray-900">{company.total_mentions}회</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-xs text-gray-500 mb-1">AI 신뢰도</div>
                <div className="text-lg font-semibold text-gray-900">
                  {Math.round((company.confidence_score || 0) * 100)}%
                </div>
              </div>
            </div>

            {/* 우선순위 표시 */}
            {isFollowing && priority && priority > 0 && (
              <div className="mb-3">
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded-full">
                  <Star className="w-3 h-3 fill-current" />
                  우선순위 {priority}
                </span>
              </div>
            )}

            {/* 추천 이유 */}
            {isRecommendation && 'reason' in company && (
              <div className="mb-3 p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="text-xs text-green-600 font-medium mb-1">추천 이유</div>
                <div className="text-sm text-green-700">{company.reason}</div>
              </div>
            )}
          </div>

          {/* 액션 버튼 */}
          <div className="flex-shrink-0 ml-4">
            {isFollowing ? (
              <button
                onClick={() => unfollowCompany(company.id)}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 text-sm font-medium shadow-sm hover:shadow-md"
              >
                <Star className="w-4 h-4 fill-current" />
                팔로잉 중
              </button>
            ) : (
              <button
                onClick={() => followCompany(company.id)}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 text-sm font-medium border border-gray-200 hover:border-gray-300"
              >
                <StarOff className="w-4 h-4" />
                팔로잉
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">기업 팔로잉</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-1 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            <Filter className="w-4 h-4" />
            필터
          </button>
        </div>
      </div>

      {/* 필터 패널 */}
      {showFilters && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">필터 설정</h3>
            <button
              onClick={() => setShowFilters(false)}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">검색어</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="기업명 검색..."
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">산업</label>
              <select
                value={industryFilter}
                onChange={(e) => setIndustryFilter(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              >
                <option value="">전체 산업</option>
                {getIndustryOptions().map(industry => (
                  <option key={industry} value={industry}>{industry}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">정렬</label>
              <div className="flex gap-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                >
                  <option value="mentions">언급 수</option>
                  <option value="name">이름</option>
                  <option value="created">생성일</option>
                </select>
                <select
                  value={order}
                  onChange={(e) => setOrder(e.target.value)}
                  className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                >
                  <option value="desc">내림차순</option>
                  <option value="asc">오름차순</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 탭 네비게이션 */}
      <div className="flex space-x-2 bg-gray-100 rounded-xl p-1.5">
        <button
          onClick={() => setActiveTab('all')}
          className={`flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-200 ${
            activeTab === 'all'
              ? 'bg-white text-blue-600 shadow-md'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <Building2 className="w-4 h-4" />
            전체 기업
            <span className="bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full text-xs font-medium">
              {companies.length}
            </span>
          </div>
        </button>
        <button
          onClick={() => setActiveTab('following')}
          className={`flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-200 ${
            activeTab === 'following'
              ? 'bg-white text-blue-600 shadow-md'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <Star className="w-4 h-4" />
            내가 팔로잉하는 기업
            <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs font-medium">
              {following.length}
            </span>
          </div>
        </button>
        <button
          onClick={() => setActiveTab('recommendations')}
          className={`flex-1 py-3 px-4 rounded-lg text-sm font-semibold transition-all duration-200 ${
            activeTab === 'recommendations'
              ? 'bg-white text-blue-600 shadow-md'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
        >
          <div className="flex items-center justify-center gap-2">
            <TrendingUp className="w-4 h-4" />
            추천
            <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded-full text-xs font-medium">
              {recommendations.length}
            </span>
          </div>
        </button>
      </div>

      {/* 콘텐츠 */}
      <div className="space-y-6">
        {activeTab === 'all' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {companies.map(company => renderCompanyCard(company))}
          </div>
        )}
        
        {activeTab === 'following' && (
          <>
            {/* 팔로잉 중 탭 설명 */}
            {following.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Star className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-blue-900 mb-1">팔로잉 중인 기업</h3>
                    <p className="text-sm text-blue-700">
                      이 기업들의 뉴스는 자동으로 요약되어 대시보드에 표시됩니다. 
                      언제든지 팔로잉을 해제할 수 있습니다.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {following.map(company => renderCompanyCard(company))}
            </div>
          </>
        )}
        
        {activeTab === 'recommendations' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {recommendations.map(company => renderCompanyCard(company, true))}
          </div>
        )}
      </div>

      {/* 빈 상태 */}
      {((activeTab === 'all' && companies.length === 0) ||
        (activeTab === 'following' && following.length === 0) ||
        (activeTab === 'recommendations' && recommendations.length === 0)) && (
        <div className="text-center py-12">
          <Building2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {activeTab === 'all' && '기업이 없습니다'}
            {activeTab === 'following' && '팔로잉 중인 기업이 없습니다'}
            {activeTab === 'recommendations' && '추천 기업이 없습니다'}
          </h3>
          <p className="text-gray-500">
            {activeTab === 'following' && '관심 있는 기업을 팔로잉해보세요! 팔로잉한 기업의 뉴스는 자동으로 요약됩니다.'}
            {activeTab === 'recommendations' && '더 많은 뉴스를 수집하면 추천이 나타납니다.'}
          </p>
        </div>
      )}
    </div>
  );
};

export default CompanyFollowing;
