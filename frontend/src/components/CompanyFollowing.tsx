import React, { useState, useEffect } from 'react';
import { Search, Star, StarOff, TrendingUp, Building2, Filter, X } from 'lucide-react';

interface Company {
  id: number;
  name: string;
  display_name: string;
  industry: string;
  stock_symbol?: string;
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

      const response = await fetch(`/v1/companies?${params}`);
      const data = await response.json();
      setCompanies(data.companies || []);
    } catch (error) {
      console.error('기업 목록 조회 실패:', error);
    }
  };

  // 팔로잉 기업 조회
  const fetchFollowing = async () => {
    try {
      const response = await fetch(`/v1/users/${userId}/following`);
      const data = await response.json();
      setFollowing(data.following || []);
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
      const response = await fetch(`/v1/companies/${companyId}/follow?user_id=${userId}&priority=${priority}`, {
        method: 'POST'
      });

      if (response.ok) {
        await fetchCompanies();
        await fetchFollowing();
        await fetchRecommendations();
      }
    } catch (error) {
      console.error('기업 팔로잉 실패:', error);
    }
  };

  // 기업 언팔로잉
  const unfollowCompany = async (companyId: number) => {
    try {
      const response = await fetch(`/v1/companies/${companyId}/unfollow?user_id=${userId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await fetchCompanies();
        await fetchFollowing();
        await fetchRecommendations();
      }
    } catch (error) {
      console.error('기업 언팔로잉 실패:', error);
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
      <div key={company.id} className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold text-gray-900">{company.display_name || company.name}</h3>
              {company.stock_symbol && (
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                  {company.stock_symbol}
                </span>
              )}
              {isRecommendation && 'recommendation_score' in company && (
                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                  추천도: {company.recommendation_score}
                </span>
              )}
            </div>
            
            <div className="text-sm text-gray-600 mb-2">
              <span className="flex items-center gap-1">
                <Building2 className="w-4 h-4" />
                {company.industry || '미분류'}
              </span>
            </div>

            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>언급: {company.total_mentions}회</span>
              <span>신뢰도: {Math.round((company.confidence_score || 0) * 100)}%</span>
              {isFollowing && priority > 0 && (
                <span className="text-yellow-600">우선순위: {priority}</span>
              )}
            </div>

            {isRecommendation && 'reason' in company && (
              <div className="mt-2 text-sm text-gray-600">
                <span className="text-green-600">추천 이유: {company.reason}</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            {isFollowing ? (
              <button
                onClick={() => unfollowCompany(company.id)}
                className="flex items-center gap-1 px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full hover:bg-yellow-200 transition-colors"
              >
                <Star className="w-4 h-4 fill-current" />
                팔로잉 중
              </button>
            ) : (
              <button
                onClick={() => followCompany(company.id)}
                className="flex items-center gap-1 px-3 py-1 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
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
        <div className="bg-gray-50 rounded-lg p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-gray-900">필터 설정</h3>
            <button
              onClick={() => setShowFilters(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">검색어</label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="기업명 검색..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">산업</label>
              <select
                value={industryFilter}
                onChange={(e) => setIndustryFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">전체</option>
                {getIndustryOptions().map(industry => (
                  <option key={industry} value={industry}>{industry}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">정렬</label>
              <div className="flex gap-2">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="mentions">언급 수</option>
                  <option value="name">이름</option>
                  <option value="created">생성일</option>
                </select>
                <select
                  value={order}
                  onChange={(e) => setOrder(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
        <button
          onClick={() => setActiveTab('all')}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'all'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          전체 기업 ({companies.length})
        </button>
        <button
          onClick={() => setActiveTab('following')}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'following'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          팔로잉 중 ({following.length})
        </button>
        <button
          onClick={() => setActiveTab('recommendations')}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'recommendations'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          추천 ({recommendations.length})
        </button>
      </div>

      {/* 콘텐츠 */}
      <div className="space-y-4">
        {activeTab === 'all' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {companies.map(company => renderCompanyCard(company))}
          </div>
        )}
        
        {activeTab === 'following' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {following.map(company => renderCompanyCard(company))}
          </div>
        )}
        
        {activeTab === 'recommendations' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
            {activeTab === 'following' && '관심 있는 기업을 팔로잉해보세요!'}
            {activeTab === 'recommendations' && '더 많은 뉴스를 수집하면 추천이 나타납니다.'}
          </p>
        </div>
      )}
    </div>
  );
};

export default CompanyFollowing;
