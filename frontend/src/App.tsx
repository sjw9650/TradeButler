import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { 
  BarChart3, 
  Building2, 
  Newspaper, 
  TrendingUp, 
  Settings,
  RefreshCw
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import NewsSummaries from './components/NewsSummaries';
import CompanyAnalysis from './components/CompanyAnalysis';
import CompanyFollowing from './components/CompanyFollowing';
import AISettings from './components/AISettings';
import { API_BASE_URL } from './services/api';

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/v1/ai/stats`);
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('통계 조회 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-primary-600" />
          <p className="text-gray-600">로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <TrendingUp className="h-8 w-8 text-primary-600 mr-3" />
                <h1 className="text-xl font-bold text-gray-900">InsightHub</h1>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-500">
                  총 {stats?.total_contents || 0}개 기사
                </div>
                <div className="text-sm text-gray-500">
                  AI 분석 {stats?.ai_summary_rate || 0}%
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="flex">
          {/* Sidebar */}
          <nav className="w-64 bg-white shadow-sm min-h-screen">
            <div className="p-4">
              <ul className="space-y-2">
                <li>
                  <Link
                    to="/"
                    className="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <BarChart3 className="h-5 w-5 mr-3" />
                    대시보드
                  </Link>
                </li>
                <li>
                  <Link
                    to="/news"
                    className="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <Newspaper className="h-5 w-5 mr-3" />
                    뉴스 요약
                  </Link>
                </li>
                <li>
                  <Link
                    to="/companies"
                    className="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <Building2 className="h-5 w-5 mr-3" />
                    기업 분석
                  </Link>
                </li>
                <li>
                  <Link
                    to="/following"
                    className="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <TrendingUp className="h-5 w-5 mr-3" />
                    기업 팔로잉
                  </Link>
                </li>
                <li>
                  <Link
                    to="/settings"
                    className="flex items-center px-4 py-2 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <Settings className="h-5 w-5 mr-3" />
                    AI 설정
                  </Link>
                </li>
              </ul>
            </div>
          </nav>

          {/* Main Content */}
          <main className="flex-1 p-6">
            <Routes>
              <Route path="/" element={<Dashboard stats={stats} />} />
              <Route path="/news" element={<NewsSummaries />} />
              <Route path="/companies" element={<CompanyAnalysis />} />
              <Route path="/following" element={<CompanyFollowing userId="test_user" />} />
              <Route path="/settings" element={<AISettings />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
