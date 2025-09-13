import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, Globe, DollarSign, Calendar } from 'lucide-react';

interface MarketData {
  name: string;
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: string;
  market: string;
}

interface NewsMetrics {
  view_count: number;
  like_count: number;
  share_count: number;
  comment_count: number;
  engagement_score: string;
}

const MarketIndices: React.FC = () => {
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMarket, setSelectedMarket] = useState<string>('all');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('1D');
  const [marketStatus, setMarketStatus] = useState<any>(null);

  // 기간별 데이터 (실제로는 API에서 가져와야 함)
  const getPeriodData = (period: string): MarketData[] => {
    const baseData = [
      {
        name: 'KOSPI',
        symbol: 'KOSPI',
        price: 2650.45,
        change: 12.34,
        changePercent: 0.47,
        volume: '450M',
        market: 'KOSPI'
      },
      {
        name: 'KOSDAQ',
        symbol: 'KOSDAQ',
        price: 845.67,
        change: -8.23,
        changePercent: -0.96,
        volume: '320M',
        market: 'KOSDAQ'
      },
      {
        name: 'S&P 500',
        symbol: 'SPX',
        price: 4567.89,
        change: 23.45,
        changePercent: 0.52,
        volume: '2.1B',
        market: 'NYSE'
      },
      {
        name: 'NASDAQ',
        symbol: 'NDX',
        price: 14234.56,
        change: -45.67,
        changePercent: -0.32,
        volume: '1.8B',
        market: 'NASDAQ'
      },
      {
        name: 'Nikkei 225',
        symbol: 'N225',
        price: 32145.67,
        change: 89.12,
        changePercent: 0.28,
        volume: '890M',
        market: 'NIKKEI'
      },
      {
        name: 'Shanghai Composite',
        symbol: 'SSE',
        price: 3123.45,
        change: -15.67,
        changePercent: -0.50,
        volume: '456M',
        market: 'SSE'
      }
    ];

    // 기간별로 다른 데이터 시뮬레이션
    return baseData.map(item => {
      let multiplier = 1;
      switch (period) {
        case '1D':
          multiplier = 1;
          break;
        case '1W':
          multiplier = 1.2;
          break;
        case '1M':
          multiplier = 1.5;
          break;
        case 'YTD':
          multiplier = 2.0;
          break;
        case '1Y':
          multiplier = 2.5;
          break;
        default:
          multiplier = 1;
      }
      
      return {
        ...item,
        change: item.change * multiplier,
        changePercent: item.changePercent * multiplier
      };
    });
  };

  const periods = [
    { value: '1D', label: '1일' },
    { value: '1W', label: '1주' },
    { value: '1M', label: '1개월' },
    { value: 'YTD', label: '올해' },
    { value: '1Y', label: '1년' }
  ];

  const markets = [
    { value: 'all', label: '전체' },
    { value: 'KOR', label: '한국' },
    { value: 'USA', label: '미국' },
    { value: 'JPN', label: '일본' },
    { value: 'CHN', label: '중국' }
  ];

  useEffect(() => {
    fetchMarketData();
    fetchMarketStatus();
  }, [selectedPeriod, selectedMarket]);

  const fetchMarketData = async () => {
    setLoading(true);
    try {
      // API에서 실제 데이터 가져오기
      const marketParam = selectedMarket === 'all' ? '' : `&market=${selectedMarket}`;
      const response = await fetch(`http://localhost:8000/v1/market/indices?${marketParam}`);
      const data = await response.json();
      
      if (data.indices) {
        // API 데이터를 프론트엔드 형식으로 변환
        const adjustedData = data.indices.map((index: any) => {
          const multiplier = getPeriodMultiplier(selectedPeriod);
          return {
            ...index,
            change: (index.change || 0) * multiplier,
            changePercent: (index.change_percent || 0) * multiplier,
            volume: index.volume || 'N/A'
          };
        });
        setMarketData(adjustedData);
      }
    } catch (error) {
      console.error('시장 데이터 조회 실패:', error);
      // 에러 시 모의 데이터 사용
      setMarketData(getPeriodData(selectedPeriod));
    } finally {
      setLoading(false);
    }
  };

  const fetchMarketStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/v1/market/status');
      const data = await response.json();
      setMarketStatus(data);
    } catch (error) {
      console.error('시장 상태 조회 실패:', error);
    }
  };

  const getPeriodMultiplier = (period: string): number => {
    const multipliers = {
      '1D': 1.0,
      '1W': 1.2,
      '1M': 1.5,
      'YTD': 2.0,
      '1Y': 2.5
    };
    return multipliers[period as keyof typeof multipliers] || 1.0;
  };

  const filteredData = marketData.filter(item => {
    if (selectedMarket === 'all') return true;
    
    switch (selectedMarket) {
      case 'KOR':
        return item.market === 'KOSPI' || item.market === 'KOSDAQ';
      case 'USA':
        return item.market === 'NYSE' || item.market === 'NASDAQ';
      case 'JPN':
        return item.market === 'NIKKEI';
      case 'CHN':
        return item.market === 'SSE';
      default:
        return true;
    }
  });

  const getMarketColor = (market: string) => {
    switch (market) {
      case 'KOSPI':
      case 'KOSDAQ':
        return 'text-blue-600 bg-blue-100';
      case 'NYSE':
      case 'NASDAQ':
        return 'text-red-600 bg-red-100';
      case 'NIKKEI':
        return 'text-purple-600 bg-purple-100';
      case 'SSE':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">시장 지수를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-700 rounded-2xl p-8 text-white">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-white/20 rounded-xl">
            <Activity className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-3xl font-bold mb-2">시장 지수</h1>
            <p className="text-green-100 text-lg">전 세계 주요 주식 시장 현황</p>
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

        {/* 시장 필터 */}
        <div className="flex flex-wrap gap-2">
          {markets.map((market) => (
            <button
              key={market.value}
              onClick={() => setSelectedMarket(market.value)}
              className={`px-4 py-2 rounded-lg transition-all duration-200 ${
                selectedMarket === market.value
                  ? 'bg-white text-green-700 font-semibold'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              {market.label}
            </button>
          ))}
        </div>

        {/* 시장 상태 표시 */}
        {marketStatus && (
          <div className="mt-4 flex flex-wrap gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${marketStatus.korean_market?.is_open ? 'bg-green-400' : 'bg-red-400'}`}></div>
              <span className="text-white/90">
                한국 시장: {marketStatus.korean_market?.is_open ? '개장' : '마감'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${marketStatus.us_market?.is_open ? 'bg-green-400' : 'bg-red-400'}`}></div>
              <span className="text-white/90">
                미국 시장: {marketStatus.us_market?.is_open ? '개장' : '마감'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* 지수 카드들 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredData.map((index) => (
          <div
            key={index.symbol}
            className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 hover:shadow-xl transition-shadow duration-300"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gray-100 rounded-lg">
                  <Globe className="h-5 w-5 text-gray-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{index.name}</h3>
                  <p className="text-sm text-gray-500">{index.symbol}</p>
                </div>
              </div>
              <span className={`px-3 py-1 text-xs font-medium rounded-full ${getMarketColor(index.market)}`}>
                {index.market}
              </span>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold text-gray-900">
                  {index.price.toLocaleString()}
                </span>
                <div className="flex items-center gap-1">
                  {index.change >= 0 ? (
                    <TrendingUp className="h-4 w-4 text-green-600" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-600" />
                  )}
                  <span
                    className={`text-sm font-medium ${
                      index.change >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}
                  >
                    {index.change >= 0 ? '+' : ''}{index.change.toFixed(2)}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">변동률</span>
                <span
                  className={`text-sm font-medium ${
                    index.changePercent >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {index.changePercent >= 0 ? '+' : ''}{index.changePercent.toFixed(2)}%
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">거래량</span>
                <span className="text-sm font-medium text-gray-900">{index.volume}</span>
              </div>
            </div>

            {/* 기간별 성과 표시 */}
            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>기간: {periods.find(p => p.value === selectedPeriod)?.label}</span>
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {new Date().toLocaleDateString('ko-KR')}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 요약 통계 */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">시장 요약</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600 mb-1">
              {filteredData.filter(item => item.change >= 0).length}
            </div>
            <div className="text-sm text-gray-500">상승 지수</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600 mb-1">
              {filteredData.filter(item => item.change < 0).length}
            </div>
            <div className="text-sm text-gray-500">하락 지수</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {filteredData.length}
            </div>
            <div className="text-sm text-gray-500">전체 지수</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketIndices;
