# 📋 InsightHub 개발 TODO

## ✅ 완료된 작업

### 1. 기본 인프라 구축
- [x] FastAPI 백엔드 설정
- [x] PostgreSQL 데이터베이스 설정
- [x] Redis 캐싱 시스템
- [x] Docker 컨테이너화
- [x] Git 저장소 설정

### 2. RSS 수집 시스템
- [x] RSS 피드 파싱 로직
- [x] 한국경제 피드 연동 (경제/금융)
- [x] 미국 뉴스 피드 연동 (Yahoo, CNN, NYT, MarketWatch, CNBC)
- [x] 중복 제거 시스템 (해시 기반)
- [x] 다중 RSS 피드 관리 시스템

### 3. AI 분석 엔진
- [x] OpenAI API 연동
- [x] 뉴스 요약 생성 (5개 불릿 포인트)
- [x] 키워드 태깅 시스템
- [x] 인사이트 생성 (2-3문장)
- [x] AI 결과 캐싱 시스템
- [x] 비용 로깅 시스템

### 4. 자동화 시스템
- [x] Celery 비동기 작업 처리
- [x] Celery Beat 스케줄링
- [x] 자동 RSS 수집 스케줄
- [x] 수동 트리거 API

### 5. 웹 대시보드
- [x] React + TypeScript 프론트엔드
- [x] Tailwind CSS 스타일링
- [x] 대시보드 컴포넌트
- [x] 뉴스 요약 뷰어
- [x] 기업 분석 도구
- [x] AI 설정 관리
- [x] 반응형 디자인

### 6. API 개발
- [x] RSS 피드 API (`/v1/feed/*`)
- [x] AI 분석 API (`/v1/ai/*`)
- [x] 스케줄 관리 API (`/v1/schedule/*`)
- [x] 브리핑 API (`/v1/brief/*`)
- [x] CORS 설정

## 🔄 진행 중인 작업

### 현재 작업
- [ ] 프론트엔드 Docker 빌드 문제 해결
- [ ] Celery Beat 태스크 등록 문제 해결

## 📝 예정된 작업

### 1. 개선 사항
- [ ] User-Agent 설정으로 봇 차단 방지
- [ ] Reddit RSS 피드 추가
- [ ] 더 정교한 기업명 추출 알고리즘
- [ ] 뉴스 카테고리 분류 시스템
- [ ] 감정 분석 기능 추가

### 2. 사용자 경험
- [ ] OAuth Google 로그인
- [ ] 사용자별 맞춤 설정
- [ ] 알림 시스템
- [ ] 모바일 앱 (React Native)

### 3. 테스트 및 품질
- [ ] pytest 테스트 실행 환경 구축
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] 성능 테스트
- [ ] 보안 테스트

### 4. 운영 및 배포
- [ ] DB 마이그레이션 시스템 정식화
- [ ] 로깅 시스템 개선
- [ ] 모니터링 대시보드
- [ ] 백업 시스템
- [ ] CI/CD 파이프라인

### 5. 확장 기능
- [ ] 다국어 지원 확장
- [ ] 실시간 알림 (WebSocket)
- [ ] 데이터 내보내기 (CSV, PDF)
- [ ] API 문서 자동화
- [ ] 버전 관리 시스템

## 🐛 알려진 문제

### 1. 프론트엔드
- [ ] React Router 의존성 문제로 Docker 빌드 실패
- [ ] TypeScript 컴파일 오류

### 2. 백엔드
- [ ] Celery Beat 태스크가 worker에 등록되지 않음
- [ ] 수동 트리거 API가 타임아웃됨

### 3. 인프라
- [ ] 데이터베이스 연결 불안정
- [ ] Redis 연결 문제

## 🎯 우선순위

### 높음 (High)
1. 프론트엔드 Docker 빌드 문제 해결
2. Celery Beat 태스크 등록 문제 해결
3. User-Agent 설정 추가

### 중간 (Medium)
1. Reddit RSS 피드 추가
2. pytest 테스트 환경 구축
3. DB 마이그레이션 시스템

### 낮음 (Low)
1. OAuth 로그인
2. 모바일 앱 개발
3. 고급 분석 기능

## 📊 진행률

- **전체 진행률**: 85%
- **핵심 기능**: 100%
- **웹 대시보드**: 90%
- **자동화**: 80%
- **테스트**: 20%
- **문서화**: 70%

## 📅 마일스톤

### Phase 1: 기본 기능 (완료)
- [x] RSS 수집 시스템
- [x] AI 분석 엔진
- [x] 기본 API

### Phase 2: 웹 플랫폼 (완료)
- [x] React 프론트엔드
- [x] 대시보드 UI
- [x] 자동화 시스템

### Phase 3: 개선 및 확장 (진행 중)
- [ ] 테스트 시스템
- [ ] 추가 RSS 피드
- [ ] 사용자 인증

### Phase 4: 운영 준비 (예정)
- [ ] 모니터링
- [ ] 배포 자동화
- [ ] 보안 강화

## 🔧 개발 환경 설정

### 필수 요구사항
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Git

### 환경 변수
```bash
OPENAI_API_KEY=your_openai_api_key_here
ENV=development
```

### 실행 명령어
```bash
# 개발 환경 시작
cd infra
docker-compose up -d

# 데이터베이스 초기화
docker-compose exec -T api python -c "
from backend.app.repo.db import engine
from backend.app.models.base import Base
from backend.app.models.content import Content, AICache
from backend.app.models.cost_log import CostLog
Base.metadata.create_all(bind=engine)
print('테이블 생성 완료!')
"
```

---
*마지막 업데이트: 2025-09-04*
*문서 버전: 1.0*
