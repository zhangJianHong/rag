# 导入必要的FastAPI和数据库相关模块
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.embedding import embedding_service
from app.services.retrieval import retrieval_service
from app.services.advanced_retrieval import advanced_retrieval_service
from app.services.generation import generation_service
from app.models.database import Query
from app.models.schemas import QueryRequest, QueryResponse
from app.config.logging_config import get_app_logger
import json
from datetime import datetime
import re

# 创建路由器实例
router = APIRouter()
logger = get_app_logger()

@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest, db: Session = Depends(get_db)):
    """处理文档查询请求"""
    import os
    import time
    start_time = time.time()
    
    try:
        # 检查是否启用文档分块检索
        use_chunks = os.getenv("USE_CHUNK_RETRIEVAL", "false").lower() == "true"
        
        if use_chunks:
            # 使用文档分块检索
            logger.info("使用文档分块检索")
            retrieved_docs = await advanced_retrieval_service.retrieve_relevant_chunks(
                db, request.query, 15
            )
        else:
            # 使用传统文档检索
            logger.info("使用传统文档检索")
            retrieved_docs = await retrieval_service.retrieve_documents(db, request.query)
        
        if not retrieved_docs:
            return QueryResponse(
                response="未找到相关文档信息",
                sources=[]
            )
        
        # 格式化上下文（传递查询文本用于智能提取）
        if use_chunks:
            # 使用文档块格式化上下文
            context = advanced_retrieval_service.format_context_with_chunks(retrieved_docs, request.query)
        else:
            # 使用传统格式化上下文
            context = retrieval_service.format_context(retrieved_docs, request.query)
        
        # 生成回答
        response = await generation_service.generate_response(request.query, context)
        
        # 保存查询历史
        query_record = Query(
            query_text=request.query,
            response=response,
            sources=json.dumps(retrieved_docs),
            created_at=str(datetime.now())
        )
        db.add(query_record)
        db.commit()
        
        # 准备返回的源文档信息
        sources = []
        for doc in retrieved_docs:
            source_info = {
                "id": doc.get("id", doc.get("doc_id")),
                "filename": doc["filename"],
                "content_preview": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"]
            }
            
            # 添加相似度信息（如果存在）
            if "similarity" in doc:
                source_info["similarity"] = doc["similarity"]
            
            # 添加分块信息（如果使用分块检索）
            if "chunk_index" in doc:
                source_info["chunk_index"] = doc["chunk_index"]
                source_info["is_chunk"] = True
            else:
                source_info["is_chunk"] = False
            
            sources.append(source_info)
        
        # 记录处理时间
        processing_time = time.time() - start_time
        logger.info(f"查询处理完成，处理时间: {processing_time:.3f}s，上下文长度: {len(context)}，检索方法: {'chunk' if use_chunks else 'document'}")
        
        return QueryResponse(
            response=response,
            sources=sources
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@router.get("/history")
async def get_query_history(db: Session = Depends(get_db)):
    """获取查询历史记录"""
    try:
        queries = db.query(Query).order_by(Query.created_at.desc()).limit(50).all()
        
        history = []
        for query in queries:
            history.append({
                "id": query.id,
                "query": query.query_text,
                "response": query.response[:200] + "..." if len(query.response) > 200 else query.response,
                "sources": json.loads(query.sources) if query.sources else [],
                "created_at": query.created_at
            })
        
        return history
        
    except Exception as e:
        logger.error(f"Error getting query history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get query history")