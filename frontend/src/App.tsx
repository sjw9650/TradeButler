import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  BarChart3, 
  Building2, 
  Newspaper, 
  TrendingUp, 
  Settings,
  RefreshCw,
  Menu,
  X,
  Bell,
  User
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import NewsSummaries from './components/NewsSummaries';
import CompanyAnalysis from './components/CompanyAnalysis';
import CompanyFollowing from './components/CompanyFollowing';
import AISettings from './components/AISettings';
import { API_BASE_URL } from './services/api';

// NavItem 컴포넌트
interface NavItemProps {
  to: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon: Icon, label }) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  
  return (
    <li>
      <Link
        to={to}
        className={`flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
          isActive
            ? 'bg-blue-50 text-blue-700 border border-blue-200 shadow-sm'
            : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
        }`}
      >
        <Icon className={`h-5 w-5 mr-3 ${isActive ? 'text-blue-600' : 'text-gray-500'}`} />
        {label}
        {isActive && (
          <div className="ml-auto w-2 h-2 bg-blue-600 rounded-full"></div>
        )}
      </Link>
    </li>
  );
};

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <RefreshCw className="h-12 w-12 animate-spin mx-auto mb-6 text-blue-600" />
            <div className="absolute inset-0 rounded-full border-4 border-blue-200"></div>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">InsightHub 로딩 중</h2>
          <p className="text-gray-600">데이터를 불러오고 있습니다...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
        {/* Header */}
        <header className="bg-white/80 backdrop-blur-sm shadow-lg border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="lg:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors mr-2"
                >
                  {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                </button>
                <div className="flex items-center">
                  <div className="relative">
                    <TrendingUp className="h-8 w-8 text-blue-600 mr-3" />
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  </div>
                  <div>
                    <h1 className="text-xl font-bold text-gray-900">InsightHub</h1>
                    <p className="text-xs text-gray-500">AI 기반 뉴스 분석 플랫폼</p>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-6">
                <div className="hidden md:flex items-center space-x-4">
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">{stats?.total_contents || 0}</div>
                    <div className="text-xs text-gray-500">총 기사</div>
                  </div>
                  <div className="w-px h-8 bg-gray-300"></div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-blue-600">{stats?.ai_summary_rate || 0}%</div>
                    <div className="text-xs text-gray-500">AI 분석</div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors relative">
                    <Bell className="h-5 w-5" />
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                  </button>
                  <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                    <User className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </header>

        <div className="flex">
          {/* Sidebar */}
          <nav className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:static inset-y-0 left-0 z-40 w-64 bg-white/95 backdrop-blur-sm shadow-xl lg:shadow-sm transition-transform duration-300 ease-in-out`}>
            <div className="p-6">
              <div className="mb-8">
                <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">메뉴</h2>
                <ul className="space-y-1">
                  <NavItem to="/" icon={BarChart3} label="대시보드" />
                  <NavItem to="/news" icon={Newspaper} label="뉴스 요약" />
                  <NavItem to="/companies" icon={Building2} label="기업 분석" />
                  <NavItem to="/following" icon={TrendingUp} label="기업 팔로잉" />
                  <NavItem to="/settings" icon={Settings} label="AI 설정" />
                </ul>
              </div>
              
            </div>
          </nav>
          
          {/* Overlay for mobile */}
          {sidebarOpen && (
            <div 
              className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}

          {/* Main Content */}
          <main className="flex-1 p-6 lg:p-8">
            <div className="max-w-7xl mx-auto">
              <Routes>
                <Route path="/" element={<Dashboard stats={stats} />} />
                <Route path="/news" element={<NewsSummaries />} />
                <Route path="/companies" element={<CompanyAnalysis />} />
                <Route path="/following" element={<CompanyFollowing userId="test_user" />} />
                <Route path="/settings" element={<AISettings />} />
              </Routes>
            </div>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
