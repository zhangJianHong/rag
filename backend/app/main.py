# 导入FastAPI和相关模块
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.routers import upload, query, logs, settings, llm_models, auth, chat, users, roles, dashboard, knowledge_domains
from app.config.logging_config import setup_logging, get_app_logger
from app.middleware.logging_middleware import LoggingMiddleware, ErrorLoggingMiddleware, PerformanceLoggingMiddleware
from app.config.settings import validate_config

from traceloop.sdk import Traceloop

#Traceloop.init(api_key="tl_09341271a5434811bc237a03b15bb9a2")

# 设置日志配置
loggers = setup_logging()
logger = get_app_logger()

# 创建FastAPI应用实例
app = FastAPI(
    title="RAG System API",
    description="基于检索增强生成的智能问答系统API",
    version="1.0.0"
)

# 启动时创建数据库表
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    try:
        from app.database_chat import create_chat_tables
        create_chat_tables()
        logger.info("Chat tables initialized successfully")

        # 创建所有模型表
        from app.database import get_engine
        from app.models.settings import Base as SettingsBase
        from app.models.llm_models import Base as LLMBase
        from app.models.database import Base as DocumentBase
        from app.models.document import Base as DocumentModelBase
        from app.models.knowledge_domain import Base as KnowledgeDomainBase

        engine = get_engine()

        # 创建文档表
        DocumentBase.metadata.create_all(bind=engine)
        DocumentModelBase.metadata.create_all(bind=engine)
        logger.info("Document tables initialized successfully")

        # 创建设置表
        SettingsBase.metadata.create_all(bind=engine)
        logger.info("Settings table initialized successfully")

        # 创建LLM模型表
        LLMBase.metadata.create_all(bind=engine)
        logger.info("LLM models tables initialized successfully")

        # 创建知识领域表
        KnowledgeDomainBase.metadata.create_all(bind=engine)
        logger.info("Knowledge domain tables initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        import traceback
        logger.error(traceback.format_exc())

# 添加日志中间件
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorLoggingMiddleware)
app.add_middleware(PerformanceLoggingMiddleware, slow_request_threshold=2.0)

# 配置CORS中间件，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api", tags=["认证"])
app.include_router(users.router, tags=["用户管理"])
app.include_router(roles.router, tags=["角色管理"])
app.include_router(upload.router, prefix="/api", tags=["文档管理"])
app.include_router(query.router, prefix="/api", tags=["查询接口"])
app.include_router(logs.router, prefix="/api", tags=["日志管理"])
app.include_router(settings.router, prefix="/api", tags=["系统设置"])
app.include_router(llm_models.router, prefix="/api", tags=["LLM模型管理"])

# 导入并注册Chat路由
from app.routers import chat
app.include_router(chat.router, prefix="/api", tags=["聊天接口"])

# 注册Dashboard路由
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])

# 注册知识领域管理路由
app.include_router(knowledge_domains.router, prefix="/api", tags=["知识领域管理"])

@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": "RAG System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8800)