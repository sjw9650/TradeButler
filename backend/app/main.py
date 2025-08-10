from fastapi import FastAPI
from .api.v1 import feed, brief
from .core.config import settings

app = FastAPI(title="InsightHub API", version="0.1.0")

app.include_router(feed.router, prefix="/v1")
app.include_router(brief.router)

@app.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV}
