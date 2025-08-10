from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ContentOut(BaseModel):
    id: int
    source: str
    title: str
    author: Optional[str] = None
    url: str
    published_at: Optional[datetime] = None
    summary_bullets: Optional[List[str]] = Field(default=None)
    insight: Optional[str] = None
    tags: Optional[List[str]] = None
    class Config:
        from_attributes = True
