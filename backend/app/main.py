from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1 import feed, brief, schedule, ai, companies, companies_optimized, selective_ai, popular_news, auth, company_analytics, cost_optimization, user_preferences, market_data
from .core.config import settings

app = FastAPI(title="InsightHub API", version="0.1.0")

# CORS 설정 (프론트엔드 연결용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feed.router, prefix="/v1")
app.include_router(brief.router)
app.include_router(schedule.router, prefix="/v1/schedule")
app.include_router(ai.router, prefix="/v1/ai")
app.include_router(companies_optimized.router, prefix="/v1")
app.include_router(companies.router, prefix="/v1")
app.include_router(selective_ai.router, prefix="/v1/selective-ai")
app.include_router(popular_news.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")
app.include_router(company_analytics.router, prefix="/v1")
app.include_router(cost_optimization.router, prefix="/v1")
app.include_router(user_preferences.router, prefix="/v1")
app.include_router(market_data.router, prefix="/v1")

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}
