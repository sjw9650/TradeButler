# 🚀 InsightHub 프로젝트 개요

## 📋 프로젝트 소개
**InsightHub**는 AI 기반 뉴스 분석 및 기업 정보 대시보드 플랫폼입니다. RSS 피드로부터 뉴스를 수집하고, OpenAI를 활용해 요약, 태깅, 인사이트를 생성하며, 웹 기반 대시보드로 정보를 시각화합니다.

## 🏗️ 기술 스택

### Backend
- **FastAPI** (Python 3.11+)
- **PostgreSQL** (데이터베이스)
- **Redis** (캐싱 및 Celery 브로커)
- **SQLAlchemy 2.0+** (ORM)
- **Celery + Celery Beat** (비동기 작업 및 스케줄링)
- **OpenAI API** (GPT-3.5-turbo)

### Frontend
- **React 18** + **TypeScript**
- **Tailwind CSS** (스타일링)
- **React Router** (라우팅)
- **Lucide React** (아이콘)
- **Axios** (HTTP 클라이언트)

### Infrastructure
- **Docker** + **Docker Compose**
- **Git** + **GitHub** (버전 관리)

## 📁 프로젝트 구조
```
insighthub_skeleton/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── feed.py          # RSS 피드 API
│   │   │   ├── brief.py         # 일일 브리핑 API
│   │   │   ├── schedule.py      # 스케줄 관리 API
│   │   │   └── ai.py            # AI 요약/기업 분석 API
│   │   ├── models/
│   │   │   ├── content.py       # Content, AICache 모델
│   │   │   └── cost_log.py      # 비용 로깅 모델
│   │   ├── services/ingest/
│   │   │   ├── rss.py           # RSS 수집 로직
│   │   │   └── multi_rss.py     # 다중 RSS 피드 관리
│   │   ├── workers/
│   │   │   ├── celery_app.py    # Celery 설정
│   │   │   ├── tasks.py         # AI 처리 태스크
│   │   │   ├── scheduled_tasks.py # 스케줄된 태스크
│   │   │   └── beat_config.py   # Celery Beat 설정
│   │   └── utils/
│   │       └── cost_calculator.py # OpenAI 비용 계산
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx    # 대시보드
│   │   │   ├── NewsSummaries.tsx # 뉴스 요약
│   │   │   ├── CompanyAnalysis.tsx # 기업 분석
│   │   │   └── AISettings.tsx   # AI 설정
│   │   ├── services/
│   │   │   └── api.ts           # API 클라이언트
│   │   └── App.tsx              # 메인 앱
│   └── package.json
├── infra/
│   ├── docker-compose.yml       # 서비스 정의
│   ├── Dockerfile.api           # API 컨테이너
│   ├── Dockerfile.worker        # Worker 컨테이너
│   └── Dockerfile.frontend      # Frontend 컨테이너
├── .env                         # 환경 변수
├── PROJECT_OVERVIEW.md          # 이 파일
└── README.md                    # 프로젝트 README
```

## 🔧 핵심 기능

### 1. RSS 수집 시스템
- **한국 뉴스**: 한국경제 경제/금융 피드
- **미국 뉴스**: Yahoo News, CNN, NYT, MarketWatch, CNBC
- **자동 스케줄링**: Celery Beat으로 정기 수집
- **중복 제거**: 해시 기반 중복 방지

### 2. AI 분석 엔진
- **뉴스 요약**: 5개 불릿 포인트로 요약
- **키워드 태깅**: 관련 키워드 자동 추출
- **인사이트 생성**: 2-3문장 인사이트
- **비용 로깅**: OpenAI API 사용량 추적

### 3. 웹 대시보드
- **대시보드**: 통계 및 현황 모니터링
- **뉴스 요약**: AI 요약된 뉴스 목록/상세보기
- **기업 분석**: 기업별 언급 횟수 및 관련 뉴스
- **AI 설정**: 수동 수집 트리거 및 스케줄 관리

## 🚀 실행 방법

### 1. 환경 설정
```bash
# .env 파일 생성
OPENAI_API_KEY=your_openai_api_key_here
ENV=development
```

### 2. Docker 실행
```bash
cd infra
docker-compose up -d
```

### 3. 데이터베이스 초기화
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

### 4. 접속
- **API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **프론트엔드**: http://localhost:3000 (Docker 빌드 후)

## 📡 API 엔드포인트

### RSS 피드
- `GET /v1/feed` - 피드 목록 조회
- `GET /v1/feed/{id}` - 특정 콘텐츠 조회
- `GET /v1/feed/popular/tags` - 인기 태그 조회

### AI 분석
- `GET /v1/ai/summaries` - AI 요약 목록
- `GET /v1/ai/summaries/{id}` - 특정 뉴스 AI 요약
- `POST /v1/ai/summaries/{id}/regenerate` - AI 요약 재생성
- `GET /v1/ai/companies` - 기업 정보 목록
- `GET /v1/ai/companies/{name}/news` - 기업 관련 뉴스
- `GET /v1/ai/stats` - AI 분석 통계

### 스케줄 관리
- `GET /v1/schedule/schedules` - 스케줄 목록
- `POST /v1/schedule/trigger/korean` - 한국 뉴스 수집
- `POST /v1/schedule/trigger/us` - 미국 뉴스 수집
- `POST /v1/schedule/trigger/all` - 전체 뉴스 수집

### 브리핑
- `GET /v1/brief/daily` - 일일 브리핑 (Redis 캐시 5분)

## 🔄 자동 스케줄링
- **한국 뉴스**: 매시간 수집
- **미국 뉴스**: 30분마다 수집
- **전체 뉴스**: 매일 수집
- **헬스체크**: 5분마다 실행

## 💾 데이터 모델

### Content (뉴스 콘텐츠)
- `id`, `title`, `author`, `url`, `source`
- `published_at`, `raw_text`, `lang`, `hash`
- `summary_bullets` (JSON), `insight`, `tags` (JSON)

### AICache (AI 결과 캐시)
- `content_id`, `model_version`, `summary_bullets`
- `insight`, `tags`, `created_at`

### CostLog (비용 로깅)
- `content_id`, `model_name`, `tokens_in/out`
- `cost_usd`, `request_type`, `status`

## 🎯 주요 성과
- ✅ **완전한 웹 플랫폼**: 백엔드 API + 프론트엔드 대시보드
- ✅ **AI 기반 분석**: OpenAI를 활용한 자동 요약 및 인사이트
- ✅ **실시간 수집**: Celery Beat으로 자동 RSS 수집
- ✅ **기업 분석**: 뉴스에서 기업 정보 추출 및 분석
- ✅ **모던 UI/UX**: React + Tailwind CSS 반응형 디자인
- ✅ **Docker 컨테이너화**: 완전한 개발/배포 환경
- ✅ **Git 버전 관리**: GitHub에 모든 코드 저장

## 🔗 Git 저장소
- **Repository**: https://github.com/sjw9650/TradeButler.git
- **Latest Commit**: `6b78316` - 웹 기반 AI 요약 및 기업 정보 대시보드 구축

## 📝 다음 단계 (미완료)
- [ ] User-Agent 설정으로 봇 차단 방지
- [ ] Reddit RSS 피드 추가
- [ ] OAuth Google 로그인
- [ ] pytest 테스트 실행 환경 구축
- [ ] DB 마이그레이션 시스템 정식화

## 📊 현재 상태
- **개발 진행률**: 85%
- **핵심 기능**: 완료
- **웹 대시보드**: 완료
- **자동화**: 완료
- **테스트**: 부분 완료

## 🛠️ 개발 환경
- **OS**: macOS (darwin 24.4.0)
- **Shell**: /bin/zsh
- **Node.js**: 18+ (프론트엔드)
- **Python**: 3.11+ (백엔드)
- **Docker**: 최신 버전

## 📞 연락처
- **GitHub**: sjw9650
- **Repository**: TradeButler

---
*마지막 업데이트: 2025-09-04*
*문서 버전: 1.0*
