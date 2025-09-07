import React, { useState, useEffect } from 'react';
import { User, LogOut, Settings } from 'lucide-react';

interface User {
  id: number;
  email: string;
  name: string;
  picture?: string;
  is_premium: boolean;
  subscription_tier: string;
}

interface GoogleLoginProps {
  onLogin: (user: User, sessionToken: string) => void;
  onLogout: () => void;
}

const GoogleLogin: React.FC<GoogleLoginProps> = ({ onLogin, onLogout }) => {
  const [user, setUser] = useState<User | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  // 컴포넌트 마운트 시 저장된 세션 확인
  useEffect(() => {
    const savedToken = localStorage.getItem('session_token');
    const savedUser = localStorage.getItem('user');
    
    if (savedToken && savedUser) {
      setSessionToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      // Google OAuth 2.0 로그인 URL 생성
      const response = await fetch('http://localhost:8000/v1/auth/google/login');
      const data = await response.json();
      
      if (data.auth_url) {
        // 새 창에서 Google 로그인 페이지 열기
        const popup = window.open(
          data.auth_url,
          'google-login',
          'width=500,height=600,scrollbars=yes,resizable=yes'
        );
        
        // 팝업에서 로그인 완료 시 메시지 수신
        const messageListener = (event: MessageEvent) => {
          if (event.origin !== window.location.origin) return;
          
          if (event.data.type === 'GOOGLE_LOGIN_SUCCESS') {
            const { user, sessionToken } = event.data;
            setUser(user);
            setSessionToken(sessionToken);
            localStorage.setItem('session_token', sessionToken);
            localStorage.setItem('user', JSON.stringify(user));
            onLogin(user, sessionToken);
            popup?.close();
            window.removeEventListener('message', messageListener);
          }
        };
        
        window.addEventListener('message', messageListener);
        
        // 팝업이 닫혔는지 확인
        const checkClosed = setInterval(() => {
          if (popup?.closed) {
            clearInterval(checkClosed);
            window.removeEventListener('message', messageListener);
            setLoading(false);
          }
        }, 1000);
        
      } else {
        throw new Error('로그인 URL을 가져올 수 없습니다.');
      }
    } catch (error) {
      console.error('Google 로그인 실패:', error);
      alert('로그인에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      if (sessionToken) {
        await fetch('http://localhost:8000/v1/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${sessionToken}`,
            'Content-Type': 'application/json'
          }
        });
      }
      
      // 로컬 저장소 정리
      localStorage.removeItem('session_token');
      localStorage.removeItem('user');
      
      setUser(null);
      setSessionToken(null);
      onLogout();
      setShowDropdown(false);
    } catch (error) {
      console.error('로그아웃 실패:', error);
      // 에러가 있어도 로컬 상태는 정리
      localStorage.removeItem('session_token');
      localStorage.removeItem('user');
      setUser(null);
      setSessionToken(null);
      onLogout();
      setShowDropdown(false);
    }
  };

  if (user) {
    return (
      <div className="relative">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="flex items-center gap-2 p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          {user.picture ? (
            <img
              src={user.picture}
              alt={user.name}
              className="w-8 h-8 rounded-full"
            />
          ) : (
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
          )}
          <span className="hidden md:block text-sm font-medium text-gray-700">
            {user.name}
          </span>
        </button>

        {showDropdown && (
          <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
            <div className="px-4 py-3 border-b border-gray-100">
              <p className="text-sm font-medium text-gray-900">{user.name}</p>
              <p className="text-xs text-gray-500">{user.email}</p>
              {user.is_premium && (
                <span className="inline-block mt-1 px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                  {user.subscription_tier}
                </span>
              )}
            </div>
            
            <div className="py-1">
              <button
                onClick={() => {
                  setShowDropdown(false);
                  // 설정 페이지로 이동
                }}
                className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
              >
                <Settings className="w-4 h-4" />
                설정
              </button>
              
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                <LogOut className="w-4 h-4" />
                로그아웃
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <button
      onClick={handleGoogleLogin}
      disabled={loading}
      className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
    >
      {loading ? (
        <div className="w-5 h-5 border-2 border-gray-300 border-t-green-600 rounded-full animate-spin" />
      ) : (
        <svg className="w-5 h-5" viewBox="0 0 24 24">
          <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
          />
          <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
          />
        </svg>
      )}
      <span className="text-sm font-medium text-gray-700">
        {loading ? '로그인 중...' : 'Google 로그인'}
      </span>
    </button>
  );
};

export default GoogleLogin;
