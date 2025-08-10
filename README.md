# InsightHub

AI 기반 콘텐츠 수집 및 분석 플랫폼

## 🚀 프로젝트 소개

InsightHub는 RSS 피드와 웹 콘텐츠를 자동으로 수집하고, OpenAI를 활용하여 AI 요약 및 태그 생성을 수행하는 지능형 콘텐츠 허브입니다.

## ✨ 주요 기능

- **📡 RSS 피드 자동 수집**: 다양한 소스에서 콘텐츠 자동 수집
- **🤖 AI 기반 요약**: OpenAI GPT를 활용한 스마트 콘텐츠 요약
- **🏷️ 자동 태그 생성**: AI가 콘텐츠를 분석하여 관련 태그 자동 생성
- **🔍 고급 검색**: 태그 기반 필터링 및 키워드 검색
- **⚡ 비동기 처리**: Celery를 활용한 백그라운드 AI 처리
- **💾 스마트 캐싱**: AI 결과 캐싱으로 중복 처리 방지

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI API   │    │   Celery Worker │    │   PostgreSQL    │
│   (Content)     │◄──►│   (AI Process)  │    │   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RSS Ingest    │    │   OpenAI API    │    │     Redis       │
│   (Crawler)     │    │   (GPT-3.5)     │    │   (Cache/Queue) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ 기술 스택

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL 15+
- **Cache/Queue**: Redis 7+
- **AI**: OpenAI GPT-3.5-turbo
- **Task Queue**: Celery
- **Container**: Docker & Docker Compose
- **ORM**: SQLAlchemy 2.0+

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/sjw9650/TradeButler.git
cd TradeButler
```

### 2. 환경 변수 설정
```bash
# backend/.env 파일 생성
cp backend/.env.example backend/.env
# OpenAI API 키 설정 필요
```

### 3. Docker 실행
```bash
cd infra
docker-compose up --build
```

### 4. API 테스트
```bash
curl http://localhost:8000/health
```

## 📚 상세 문서

- [Backend README](backend/README.md) - 백엔드 상세 설정 및 API 문서
- [Infrastructure](infra/) - Docker 및 인프라 설정

## 🔧 개발 환경

### 로컬 개발
```bash
cd backend
pip install -e .
pytest  # 테스트 실행
```

### Docker 개발
```bash
docker-compose exec api python -m pytest
```

## 📊 API 엔드포인트

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | 헬스 체크 |
| `GET` | `/v1/feed` | 피드 목록 조회 |
| `GET` | `/v1/feed/{id}` | 특정 콘텐츠 조회 |
| `GET` | `/v1/feed/search/tags` | 인기 태그 목록 |

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 [Issues](https://github.com/sjw9650/TradeButler/issues)를 통해 연락해 주세요. 