import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Play, 
  RefreshCw, 
  Clock, 
  CheckCircle,
  AlertCircle,
  BarChart3
} from 'lucide-react';
import { api } from '../services/api';

const AISettings: React.FC = () => {
  const [schedules, setSchedules] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isTriggering, setIsTriggering] = useState<string | null>(null);
  const [triggerResult, setTriggerResult] = useState<any>(null);

  useEffect(() => {
    fetchSchedules();
  }, []);

  const fetchSchedules = async () => {
    setIsLoading(true);
    try {
      const data = await api.getSchedules();
      setSchedules(data.schedules || []);
    } catch (error) {
      console.error('스케줄 조회 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTrigger = async (type: 'korean' | 'us' | 'all') => {
    setIsTriggering(type);
    setTriggerResult(null);
    
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
      setTriggerResult({ type, result, success: true });
    } catch (error) {
      setTriggerResult({ type, error: error.message, success: false });
    } finally {
      setIsTriggering(null);
    }
  };

  const getScheduleDisplayName = (scheduleName: string) => {
    const nameMap: Record<string, string> = {
      'korean-news-hourly': '한국 뉴스 수집',
      'us-news-30min': '미국 뉴스 수집',
      'all-news-daily': '전체 뉴스 수집',
      'health-check': '시스템 상태 확인'
    };
    return nameMap[scheduleName] || scheduleName;
  };

  const getTriggerButtonText = (type: string) => {
    const textMap: Record<string, string> = {
      'korean': '한국 뉴스 수집',
      'us': '미국 뉴스 수집',
      'all': '전체 뉴스 수집'
    };
    return textMap[type] || type;
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI 설정</h1>
        <p className="text-gray-600">RSS 수집 스케줄과 AI 분석 설정을 관리하세요</p>
      </div>

      {/* 수동 트리거 */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">수동 수집 트리거</h2>
        <p className="text-sm text-gray-600 mb-6">
          필요에 따라 수동으로 RSS 수집을 실행할 수 있습니다.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => handleTrigger('korean')}
            disabled={isTriggering === 'korean'}
            className="p-4 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 disabled:opacity-50 transition-colors"
          >
            <div className="flex items-center justify-center mb-2">
              {isTriggering === 'korean' ? (
                <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
              ) : (
                <Play className="h-6 w-6 text-blue-600" />
              )}
            </div>
            <h3 className="font-medium text-gray-900">한국 뉴스</h3>
            <p className="text-sm text-gray-600">한국경제 RSS 수집</p>
          </button>

          <button
            onClick={() => handleTrigger('us')}
            disabled={isTriggering === 'us'}
            className="p-4 bg-green-50 border border-green-200 rounded-lg hover:bg-green-100 disabled:opacity-50 transition-colors"
          >
            <div className="flex items-center justify-center mb-2">
              {isTriggering === 'us' ? (
                <RefreshCw className="h-6 w-6 animate-spin text-green-600" />
              ) : (
                <Play className="h-6 w-6 text-green-600" />
              )}
            </div>
            <h3 className="font-medium text-gray-900">미국 뉴스</h3>
            <p className="text-sm text-gray-600">Yahoo, CNN, NYT 등</p>
          </button>

          <button
            onClick={() => handleTrigger('all')}
            disabled={isTriggering === 'all'}
            className="p-4 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 disabled:opacity-50 transition-colors"
          >
            <div className="flex items-center justify-center mb-2">
              {isTriggering === 'all' ? (
                <RefreshCw className="h-6 w-6 animate-spin text-purple-600" />
              ) : (
                <Play className="h-6 w-6 text-purple-600" />
              )}
            </div>
            <h3 className="font-medium text-gray-900">전체 뉴스</h3>
            <p className="text-sm text-gray-600">모든 RSS 피드 수집</p>
          </button>
        </div>

        {/* 트리거 결과 */}
        {triggerResult && (
          <div className={`mt-4 p-4 rounded-lg ${
            triggerResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-center">
              {triggerResult.success ? (
                <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
              )}
              <span className={`font-medium ${
                triggerResult.success ? 'text-green-800' : 'text-red-800'
              }`}>
                {getTriggerButtonText(triggerResult.type)} {triggerResult.success ? '시작됨' : '실패'}
              </span>
            </div>
            {triggerResult.success && triggerResult.result && (
              <p className="text-sm text-green-700 mt-1">
                태스크 ID: {triggerResult.result.task_id}
              </p>
            )}
            {!triggerResult.success && triggerResult.error && (
              <p className="text-sm text-red-700 mt-1">
                에러: {triggerResult.error}
              </p>
            )}
          </div>
        )}
      </div>

      {/* 자동 스케줄 */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">자동 수집 스케줄</h2>
        <p className="text-sm text-gray-600 mb-6">
          시스템이 자동으로 실행하는 RSS 수집 스케줄입니다.
        </p>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-primary-600" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {schedules.map((schedule) => (
              <div key={schedule.name} className="p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900">
                    {getScheduleDisplayName(schedule.name)}
                  </h3>
                  <div className="flex items-center text-sm text-gray-500">
                    <Clock className="h-4 w-4 mr-1" />
                    우선순위 {schedule.priority}
                  </div>
                </div>
                <p className="text-sm text-gray-600 mb-2">{schedule.description}</p>
                <div className="text-xs text-gray-500">
                  <p><strong>스케줄:</strong> {schedule.schedule}</p>
                  <p><strong>큐:</strong> {schedule.queue}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 시스템 정보 */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">시스템 정보</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">RSS 피드</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• 한국경제 경제/금융</li>
              <li>• Yahoo News</li>
              <li>• CNN Top Stories</li>
              <li>• NYT HomePage</li>
              <li>• MarketWatch</li>
              <li>• CNBC</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-gray-900 mb-2">AI 기능</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• 뉴스 요약 생성</li>
              <li>• 키워드 태깅</li>
              <li>• 인사이트 추출</li>
              <li>• 기업 정보 분석</li>
              <li>• 다국어 지원 (한/영)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AISettings;
