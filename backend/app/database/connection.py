"""
数据库连接管理
从根目录的database.py移动而来，提供更好的模块化结构
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import DB_URL
import logging

logger = logging.getLogger(__name__)

# 全局变量存储引擎和会话工厂
_engine = None
_session_factory = None

def get_engine():
    """获取数据库引擎（单例模式）"""
    global _engine
    if _engine is None:
        _engine = create_engine(DB_URL, pool_pre_ping=True)
        logger.info(f"Database engine created for: {DB_URL}")
    return _engine

def get_session_local():
    """获取会话工厂（单例模式）"""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _session_factory

def get_db() -> Session:
    """获取数据库会话"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
