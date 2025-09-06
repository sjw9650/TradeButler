from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1 import feed, brief, schedule, ai, companies
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
app.include_router(companies.router, prefix="/v1")

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}
