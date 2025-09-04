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
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">대시보드</h1>
          <p className="text-gray-600">AI 기반 뉴스 분석 현황</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => handleTrigger('korean')}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            <Play className="h-4 w-4 mr-2" />
            한국 뉴스 수집
          </button>
          <button
            onClick={() => handleTrigger('us')}
            disabled={isLoading}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center"
          >
            <Play className="h-4 w-4 mr-2" />
            미국 뉴스 수집
          </button>
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">총 기사 수</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_contents.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <TrendingUp className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">AI 분석 완료</p>
              <p className="text-2xl font-bold text-gray-900">{stats.ai_summarized.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <Building2 className="h-8 w-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">AI 분석률</p>
              <p className="text-2xl font-bold text-gray-900">{stats.ai_summary_rate}%</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center">
            <Globe className="h-8 w-8 text-orange-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">언어</p>
              <p className="text-2xl font-bold text-gray-900">
                {Object.keys(stats.language_stats).length}개
              </p>
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
