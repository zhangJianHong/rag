"""
数据库连接管理
从根目录的database.py移动而来，提供更好的模块化结构
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import DB_URL
import logging

logger = logging.getLogger(__name__)

# 全局变量存储引擎和会话工厂
_engine = None
_session_factory = None

# 全局注册 pgvector 类型（在模块加载时立即执行）
def _register_vector_types_globally():
    """在全局范围内注册 pgvector 自定义类型"""
    try:
        from psycopg2.extensions import new_type, register_type
        import psycopg2

        # 创建一个临时连接来获取类型 OID
        from sqlalchemy.engine.url import make_url
        url = make_url(DB_URL)

        temp_conn = psycopg2.connect(
            host=url.host,
            port=url.port,
            database=url.database,
            user=url.username,
            password=url.password
        )

        cursor = temp_conn.cursor()
        cursor.execute("""
            SELECT t.oid, t.typname
            FROM pg_type t
            WHERE t.typname IN ('vector', 'halfvec', 'sparsevec')
        """)

        custom_types = cursor.fetchall()

        # 为每个自定义类型注册全局处理器
        for oid, typname in custom_types:
            # 创建类型转换器
            def typecast_vector(value, cursor):
                if value is None:
                    return None
                return value

            # 注册为全局类型（不需要每次连接都注册）
            vector_type = new_type((oid,), typname.upper(), typecast_vector)
            register_type(vector_type)  # 不传 conn 参数表示全局注册
            logger.info(f"Globally registered PostgreSQL type: {typname} (OID: {oid})")

        cursor.close()
        temp_conn.close()
        return True
    except Exception as e:
        logger.warning(f"Failed to globally register pgvector types: {e}")
        return False

# 尝试全局注册类型
_types_registered = _register_vector_types_globally()

def get_engine():
    """获取数据库引擎（单例模式）"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            DB_URL,
            pool_pre_ping=True,
            connect_args={
                "options": "-c client_encoding=utf8"
            }
        )

        logger.info(f"Database engine created for: {DB_URL}")
        if _types_registered:
            logger.info("pgvector types are globally registered")
        else:
            logger.warning("pgvector types registration failed, may encounter type errors")
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
