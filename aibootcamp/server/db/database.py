"""
데이터베이스 설정 및 연결 관리

이 모듈은 SQLAlchemy를 사용하여 SQLite 데이터베이스 연결을 관리합니다.
FastAPI의 의존성 주입 시스템과 연동되어 데이터베이스 세션을 제공합니다.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from utils.config import settings

# SQLite 데이터베이스 엔진 생성
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False},  # SQLite 멀티스레드 지원
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy 모델의 기본 클래스
Base = declarative_base()


def get_db():
    """
    데이터베이스 세션 의존성 함수
    
    FastAPI의 의존성 주입 시스템에서 사용되며,
    요청마다 새로운 데이터베이스 세션을 생성하고
    요청 완료 후 자동으로 세션을 닫습니다.
    
    Yields:
        Session: SQLAlchemy 데이터베이스 세션
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
