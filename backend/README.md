# InsightHub Backend

RSS 피드를 수집하고 AI로 요약하는 콘텐츠 허브 백엔드입니다.

## 환경 설정

### 1. 환경 변수 파일 생성

`backend/.env` 파일을 생성하고 다음과 같이 설정하세요:

```bash
# InsightHub Environment Configuration

# Environment
ENV=local

# Database Configuration
DB_URL=postgresql+psycopg2://postgres:postgres@db:5432/insighthub

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# OpenAI Configuration (실제 API 키로 교체하세요)
OPENAI_API_KEY=your_openai_api_key_here

# AWS S3 Configuration (optional)
S3_ENDPOINT=

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

### 2. OpenAI API 키 설정

1. [OpenAI Platform](https://platform.openai.com/api-keys)에서 API 키를 생성하세요
2. `.env` 파일의 `OPENAI_API_KEY`에 실제 키를 입력하세요

### 3. 실행

```bash
cd infra
docker-compose up --build
```

## API 엔드포인트

- `GET /health` - 헬스 체크
- `GET /v1/feed` - 피드 목록 조회
  - `?tags=ai,tech` - 태그 필터
  - `?keyword=OpenAI` - 키워드 검색
  - `?limit=10&offset=0` - 페이징

## RSS 수집 테스트

```bash
docker-compose exec api python -c "
from backend.app.services.ingest.rss import ingest_rss
ingest_rss('https://feeds.feedburner.com/TechCrunch', source_name='rss:techcrunch')
print('RSS 수집 완료')
"
``` 