# 🛠️ InsightHub 개발 가이드

## 📚 목차
1. [개발 환경 설정](#개발-환경-설정)
2. [프로젝트 구조](#프로젝트-구조)
3. [개발 워크플로우](#개발-워크플로우)
4. [코딩 컨벤션](#코딩-컨벤션)
5. [테스트 가이드](#테스트-가이드)
6. [배포 가이드](#배포-가이드)
7. [문제 해결](#문제-해결)

## 🚀 개발 환경 설정

### 1. 필수 요구사항
```bash
# Docker & Docker Compose
docker --version
docker-compose --version

# Node.js (프론트엔드)
node --version  # 18+

# Python (백엔드)
python --version  # 3.11+

# Git
git --version
```

### 2. 프로젝트 클론
```bash
git clone https://github.com/sjw9650/TradeButler.git
cd TradeButler
```

### 3. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# OpenAI API 키 설정
echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
echo "ENV=development" >> .env
```

### 4. 개발 환경 시작
```bash
cd infra
docker-compose up -d
```

### 5. 데이터베이스 초기화
```bash
docker-compose exec -T api python -c "
from backend.app.repo.db import engine
from backend.app.models.base import Base
from backend.app.models.content import Content, AICache
from backend.app.models.cost_log import CostLog
Base.metadata.create_all(bind=engine)
print('테이블 생성 완료!')
"
```

## 📁 프로젝트 구조

### Backend 구조
```
backend/
├── app/
│   ├── api/v1/           # API 엔드포인트
│   ├── models/           # 데이터베이스 모델
│   ├── services/         # 비즈니스 로직
│   ├── workers/          # Celery 태스크
│   ├── utils/            # 유틸리티 함수
│   └── core/             # 핵심 설정
├── tests/                # 테스트 코드
└── pyproject.toml        # 의존성 관리
```

### Frontend 구조
```
frontend/
├── src/
│   ├── components/       # React 컴포넌트
│   ├── services/         # API 클라이언트
│   ├── types/            # TypeScript 타입
│   └── utils/            # 유틸리티 함수
├── public/               # 정적 파일
└── package.json          # 의존성 관리
```

### Infrastructure 구조
```
infra/
├── docker-compose.yml    # 서비스 정의
├── Dockerfile.api        # API 컨테이너
├── Dockerfile.worker     # Worker 컨테이너
└── Dockerfile.frontend   # Frontend 컨테이너
```

## 🔄 개발 워크플로우

### 1. 새 기능 개발
```bash
# 새 브랜치 생성
git checkout -b feature/new-feature

# 개발 작업
# ... 코드 작성 ...

# 커밋
git add .
git commit -m "feat: 새 기능 추가"

# 푸시
git push origin feature/new-feature
```

### 2. 백엔드 개발
```bash
# API 서버 재시작
docker-compose restart api

# 로그 확인
docker-compose logs -f api

# 데이터베이스 접속
docker-compose exec -T db psql -U postgres -d insighthub
```

### 3. 프론트엔드 개발
```bash
# 프론트엔드 컨테이너 재시작
docker-compose restart frontend

# 로그 확인
docker-compose logs -f frontend

# 로컬 개발 서버 (선택사항)
cd frontend
npm install
npm start
```

### 4. 테스트 실행
```bash
# 백엔드 테스트
docker-compose exec -T api python -m pytest

# 프론트엔드 테스트
docker-compose exec -T frontend npm test
```

## 📝 코딩 컨벤션

### Python (Backend)
```python
# 함수명: snake_case
def get_user_by_id(user_id: int) -> User:
    """사용자 ID로 사용자 조회
    
    Parameters
    ----------
    user_id : int
        사용자 ID
        
    Returns
    -------
    User
        사용자 객체
    """
    pass

# 클래스명: PascalCase
class UserService:
    def __init__(self, db: Session):
        self.db = db

# 상수: UPPER_CASE
MAX_RETRY_COUNT = 3
```

### TypeScript (Frontend)
```typescript
// 함수명: camelCase
const getUserById = (userId: number): User => {
  // 함수 구현
};

// 인터페이스명: PascalCase
interface User {
  id: number;
  name: string;
  email: string;
}

// 컴포넌트명: PascalCase
const UserProfile: React.FC<UserProfileProps> = ({ user }) => {
  return <div>{user.name}</div>;
};
```

### Git 커밋 메시지
```
feat: 새 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 스타일 변경
refactor: 코드 리팩토링
test: 테스트 추가/수정
chore: 빌드/설정 변경
```

## 🧪 테스트 가이드

### 백엔드 테스트
```python
# tests/test_content_repo.py
import pytest
from backend.app.repo.content import ContentRepo

def test_list_contents():
    """콘텐츠 목록 조회 테스트"""
    # Given
    repo = ContentRepo(mock_db)
    
    # When
    result = repo.list_contents(limit=10)
    
    # Then
    assert len(result) <= 10
```

### 프론트엔드 테스트
```typescript
// components/__tests__/Dashboard.test.tsx
import { render, screen } from '@testing-library/react';
import Dashboard from '../Dashboard';

test('renders dashboard title', () => {
  render(<Dashboard stats={mockStats} />);
  expect(screen.getByText('대시보드')).toBeInTheDocument();
});
```

## 🚀 배포 가이드

### 1. 프로덕션 환경 설정
```bash
# .env.production 파일 생성
OPENAI_API_KEY=your_production_key_here
ENV=production
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port/0
```

### 2. Docker 이미지 빌드
```bash
# 프로덕션 이미지 빌드
docker-compose -f docker-compose.prod.yml build

# 이미지 푸시
docker tag insighthub-api your-registry/insighthub-api:latest
docker push your-registry/insighthub-api:latest
```

### 3. 배포
```bash
# 프로덕션 환경 시작
docker-compose -f docker-compose.prod.yml up -d

# 헬스체크
curl http://your-domain/health
```

## 🔧 문제 해결

### 1. 데이터베이스 연결 오류
```bash
# 컨테이너 재시작
docker-compose restart db api

# 연결 테스트
docker-compose exec -T api python -c "
from backend.app.repo.db import engine
print(engine.url)
"
```

### 2. Redis 연결 오류
```bash
# Redis 상태 확인
docker-compose exec -T redis redis-cli ping

# Redis 재시작
docker-compose restart redis
```

### 3. Celery 태스크 실행 오류
```bash
# Worker 재시작
docker-compose restart worker beat

# 태스크 상태 확인
docker-compose exec -T worker celery -A backend.app.workers.celery_app inspect active
```

### 4. 프론트엔드 빌드 오류
```bash
# 의존성 재설치
docker-compose exec -T frontend npm install

# 캐시 클리어
docker-compose exec -T frontend npm run build -- --no-cache
```

## 📊 모니터링

### 1. 로그 확인
```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f frontend
```

### 2. 리소스 사용량
```bash
# 컨테이너 리소스 사용량
docker stats

# 특정 컨테이너
docker stats infra_api_1
```

### 3. 데이터베이스 상태
```bash
# 연결 수 확인
docker-compose exec -T db psql -U postgres -d insighthub -c "
SELECT count(*) FROM pg_stat_activity;
"

# 테이블 크기 확인
docker-compose exec -T db psql -U postgres -d insighthub -c "
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables WHERE schemaname = 'public';
"
```

## 🔗 유용한 링크

- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [React 문서](https://react.dev/)
- [Tailwind CSS 문서](https://tailwindcss.com/)
- [Docker 문서](https://docs.docker.com/)
- [Celery 문서](https://docs.celeryproject.org/)

---
*마지막 업데이트: 2025-09-04*
*문서 버전: 1.0*
