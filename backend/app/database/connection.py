"""
数据库连接管理
从根目录的database.py移动而来，提供更好的模块化结构
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import DB_URL
import logging

logger = logging.getLogger(__name__)

def get_db():
    """获取数据库会话"""
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_engine():
    """获取数据库引擎"""
    return create_engine(DB_URL)

def get_session_local():
    """获取会话工厂"""
    engine = create_engine(DB_URL)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
