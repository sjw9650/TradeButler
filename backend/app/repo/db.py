from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from ..core.config import settings

engine = create_engine(settings.DB_URL, pool_pre_ping=True)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_db():
    """데이터베이스 세션 의존성 주입 함수"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
