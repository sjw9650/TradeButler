import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, Globe, DollarSign } from 'lucide-react';

interface MarketData {
  name: string;
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume?: string;
  market: 'KOSPI' | 'KOSDAQ' | 'NASDAQ' | 'NYSE' | 'NIKKEI';
}

const MarketIndices: React.FC = () => {
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMarket, setSelectedMarket] = useState<string>('all');

  // 모의 데이터 (실제로는 API에서 가져와야 함)
  const mockData: MarketData[] = [
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
      name: 'Dow Jones',
      symbol: 'DJI',
      price: 34567.89,
      change: 123.45,
      changePercent: 0.36,
      volume: '1.2B',
      market: 'NYSE'
    }
  ];

  useEffect(() => {
    // 모의 로딩 시뮬레이션
    const timer = setTimeout(() => {
      setMarketData(mockData);
      setLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  const filteredData = selectedMarket === 'all' 
    ? marketData 
    : marketData.filter(item => item.market === selectedMarket);

  const getMarketIcon = (market: string) => {
    switch (market) {
      case 'KOSPI':
      case 'KOSDAQ':
        return <Activity className="h-5 w-5" />;
      case 'NASDAQ':
      case 'NYSE':
        return <DollarSign className="h-5 w-5" />;
      case 'NIKKEI':
        return <Globe className="h-5 w-5" />;
      default:
        return <TrendingUp className="h-5 w-5" />;
    }
  };

  const getMarketColor = (market: string) => {
    switch (market) {
      case 'KOSPI':
      case 'KOSDAQ':
        return 'text-blue-600';
      case 'NASDAQ':
      case 'NYSE':
        return 'text-green-600';
      case 'NIKKEI':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">시장 지수 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-700 rounded-2xl p-8 text-white">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">주요 시장 지수</h1>
            <p className="text-green-100 text-lg">실시간 글로벌 시장 현황을 확인하세요</p>
          </div>
          <div className="mt-6 lg:mt-0">
            <select
              value={selectedMarket}
              onChange={(e) => setSelectedMarket(e.target.value)}
              className="bg-white/20 backdrop-blur-sm text-white rounded-xl px-4 py-2 border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50"
            >
              <option value="all" className="text-gray-900">전체 시장</option>
              <option value="KOSPI" className="text-gray-900">한국 (KOSPI/KOSDAQ)</option>
              <option value="NASDAQ" className="text-gray-900">미국 (NASDAQ/NYSE)</option>
              <option value="NIKKEI" className="text-gray-900">일본 (Nikkei)</option>
            </select>
          </div>
        </div>
      </div>

      {/* 시장 지수 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredData.map((item, index) => (
          <div
            key={item.symbol}
            className="bg-white rounded-2xl shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-200 p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg bg-gray-50 ${getMarketColor(item.market)}`}>
                  {getMarketIcon(item.market)}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{item.name}</h3>
                  <p className="text-sm text-gray-500">{item.symbol}</p>
                </div>
              </div>
              <div className={`flex items-center gap-1 ${
                item.change >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {item.change >= 0 ? (
                  <TrendingUp className="h-4 w-4" />
                ) : (
                  <TrendingDown className="h-4 w-4" />
                )}
                <span className="text-sm font-medium">
                  {item.changePercent > 0 ? '+' : ''}{item.changePercent.toFixed(2)}%
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-bold text-gray-900">
                  {item.price.toLocaleString()}
                </span>
                <span className={`text-sm font-medium ${
                  item.change >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {item.change > 0 ? '+' : ''}{item.change.toFixed(2)}
                </span>
              </div>
              
              {item.volume && (
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>거래량</span>
                  <span>{item.volume}</span>
                </div>
              )}
            </div>

            {/* 미니 차트 영역 (실제로는 차트 라이브러리 사용) */}
            <div className="mt-4 h-16 bg-gray-50 rounded-lg flex items-center justify-center">
              <div className="text-xs text-gray-400">
                📈 실시간 차트 영역
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 시장 요약 */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">시장 요약</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-xl">
            <div className="text-2xl font-bold text-green-600">
              {filteredData.filter(item => item.change >= 0).length}
            </div>
            <div className="text-sm text-green-700">상승 지수</div>
          </div>
          <div className="text-center p-4 bg-red-50 rounded-xl">
            <div className="text-2xl font-bold text-red-600">
              {filteredData.filter(item => item.change < 0).length}
            </div>
            <div className="text-sm text-red-700">하락 지수</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-xl">
            <div className="text-2xl font-bold text-blue-600">
              {filteredData.length}
            </div>
            <div className="text-sm text-blue-700">전체 지수</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketIndices;
