import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Building2, 
  Globe, 
  RefreshCw,
  Play,
  Clock
} from 'lucide-react';
import { api, AIStats } from '../services/api';

interface DashboardProps {
  stats: AIStats | null;
}

const Dashboard: React.FC<DashboardProps> = ({ stats }) => {
  const [schedules, setSchedules] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchSchedules();
  }, []);

  const fetchSchedules = async () => {
    try {
      const data = await api.getSchedules();
      setSchedules(data.schedules || []);
    } catch (error) {
      console.error('스케줄 조회 실패:', error);
    }
  };

  const handleTrigger = async (type: 'korean' | 'us' | 'all') => {
    setIsLoading(true);
    try {
      let result;
      switch (type) {
        case 'korean':
          result = await api.triggerKoreanNews();
          break;
        case 'us':
          result = await api.triggerUSNews();
          break;
        case 'all':
          result = await api.triggerAllNews();
          break;
      }
      console.log(`${type} 뉴스 수집 시작:`, result);
      // 성공 메시지 표시
    } catch (error) {
      console.error('뉴스 수집 트리거 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-8 text-white">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">대시보드</h1>
            <p className="text-blue-100 text-lg">AI 기반 뉴스 분석 현황을 한눈에 확인하세요</p>
          </div>
          <div className="mt-6 lg:mt-0 flex flex-col sm:flex-row gap-3">
            <button
              onClick={() => handleTrigger('korean')}
              disabled={isLoading}
              className="px-6 py-3 bg-white/20 backdrop-blur-sm text-white rounded-xl hover:bg-white/30 disabled:opacity-50 flex items-center justify-center transition-all duration-200 border border-white/30"
            >
              <Play className="h-5 w-5 mr-2" />
              한국 뉴스 수집
            </button>
            <button
              onClick={() => handleTrigger('us')}
              disabled={isLoading}
              className="px-6 py-3 bg-white/20 backdrop-blur-sm text-white rounded-xl hover:bg-white/30 disabled:opacity-50 flex items-center justify-center transition-all duration-200 border border-white/30"
            >
              <Play className="h-5 w-5 mr-2" />
              미국 뉴스 수집
            </button>
          </div>
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300 group">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-gray-600 mb-2">총 기사 수</p>
              <p className="text-3xl font-bold text-gray-900">{stats.total_contents.toLocaleString()}</p>
              <p className="text-xs text-gray-500 mt-1">수집된 뉴스 기사</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center group-hover:bg-blue-200 transition-colors">
              <BarChart3 className="h-6 w-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300 group">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-gray-600 mb-2">AI 분석 완료</p>
              <p className="text-3xl font-bold text-gray-900">{stats.ai_summarized.toLocaleString()}</p>
              <p className="text-xs text-gray-500 mt-1">요약 완료된 기사</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center group-hover:bg-green-200 transition-colors">
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300 group">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-gray-600 mb-2">AI 분석률</p>
              <p className="text-3xl font-bold text-gray-900">{stats.ai_summary_rate}%</p>
              <p className="text-xs text-gray-500 mt-1">자동 분석 완료율</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center group-hover:bg-purple-200 transition-colors">
              <Building2 className="h-6 w-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300 group">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-gray-600 mb-2">언어</p>
              <p className="text-3xl font-bold text-gray-900">
                {Object.keys(stats.language_stats).length}개
              </p>
              <p className="text-xs text-gray-500 mt-1">지원 언어 수</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center group-hover:bg-orange-200 transition-colors">
              <Globe className="h-6 w-6 text-orange-600" />
            </div>
          </div>
        </div>
      </div>

      {/* 소스별 통계 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">소스별 통계</h3>
          <div className="space-y-3">
            {Object.entries(stats.source_stats).map(([source, data]) => (
              <div key={source} className="flex justify-between items-center">
                <span className="text-sm text-gray-600">{source}</span>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-900">{data.ai_summarized}/{data.total}</span>
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${(data.ai_summarized / data.total) * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">언어별 분포</h3>
          <div className="space-y-3">
            {Object.entries(stats.language_stats).map(([lang, count]) => (
              <div key={lang} className="flex justify-between items-center">
                <span className="text-sm text-gray-600">
                  {lang === 'ko' ? '한국어' : lang === 'en' ? '영어' : lang}
                </span>
                <span className="text-sm font-medium text-gray-900">{count.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 스케줄 정보 */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">자동 수집 스케줄</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {schedules.map((schedule) => (
            <div key={schedule.name} className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center mb-2">
                <Clock className="h-4 w-4 text-gray-500 mr-2" />
                <span className="text-sm font-medium text-gray-900">{schedule.description}</span>
              </div>
              <p className="text-xs text-gray-600">{schedule.schedule}</p>
              <p className="text-xs text-gray-500 mt-1">우선순위: {schedule.priority}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
