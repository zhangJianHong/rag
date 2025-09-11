# 导入FastAPI和相关模块
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload, query, logs
from app.config.logging_config import setup_logging, get_app_logger
from app.middleware.logging_middleware import LoggingMiddleware, ErrorLoggingMiddleware, PerformanceLoggingMiddleware
from app.config.settings import validate_config

from traceloop.sdk import Traceloop

Traceloop.init(api_key="tl_09341271a5434811bc237a03b15bb9a2")

# 设置日志配置
loggers = setup_logging()
logger = get_app_logger()

# 创建FastAPI应用实例
app = FastAPI(
    title="RAG System API",
    description="基于检索增强生成的智能问答系统API",
    version="1.0.0"
)

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
app.include_router(upload.router, prefix="/api", tags=["文档管理"])
app.include_router(query.router, prefix="/api", tags=["查询接口"])
app.include_router(logs.router, prefix="/api", tags=["日志管理"])

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
    """健康检查接口"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)