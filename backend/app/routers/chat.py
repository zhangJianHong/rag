"""
Chat对话相关的API路由
"""
from math import log
from venv import logger
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import uuid
import asyncio
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.chat import ChatSession, ChatMessage
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService
from app.services.chat_rag_service import ChatRAGService
from app.config.settings import get_settings
import logging

router = APIRouter()
settings = get_settings()

# RAG服务(保留旧服务作为降级备用)
rag_service = RAGService()
logger = logging.getLogger(__name__)


def get_llm_service(db: Session = Depends(get_db)) -> LLMService:
    """
    获取LLM服务实例（带数据库依赖注入）
    """
    return LLMService(db=db)

class ChatRequest(BaseModel):
    """聊天请求模型"""
    session_id: Optional[str] = None
    message: str
    use_rag: bool = True
    stream: bool = True
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000
    namespace: Optional[str] = None  # 可选的知识领域过滤参数

class ChatResponse(BaseModel):
    """聊天响应模型"""
    session_id: str
    message: str
    sources: Optional[List[Dict]] = None
    tokens_used: Optional[int] = None
    timestamp: Optional[datetime] = None
    # 新增可选字段(向后兼容)
    domain_classification: Optional[Dict] = None
    retrieval_stats: Optional[Dict] = None

class SessionCreate(BaseModel):
    """创建会话请求"""
    title: Optional[str] = "新对话"
    metadata: Optional[Dict] = {}

class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message: Optional[str] = None

@router.post("/chat/send", response_model=ChatResponse)
async def send_message(request: ChatRequest, llm_svc: LLMService = Depends(get_llm_service), db: Session = Depends(get_db)):
    """
    发送聊天消息
    支持流式响应和RAG增强
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        # 获取或创建会话
        session_id = request.session_id or str(uuid.uuid4())

        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()

        if not session:
            session = ChatSession(
                session_id=session_id,
                title=request.message[:50] if len(request.message) > 50 else request.message
            )
            db.add(session)
            db.commit()

        # 保存用户消息
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        db.commit()

        # 【自动生成标题】检查是否为第一条用户消息
        user_message_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role == "user"
        ).count()

        if user_message_count == 1 and session.title in ["新对话", "新会话", request.message[:50]]:
            # 这是第一条消息,自动生成标题
            try:
                logger.info(f"为会话 {session_id} 生成标题...")
                new_title = await llm_svc.generate_session_title(
                    first_message=request.message,
                    model=request.model
                )

                session.title = new_title
                session.updated_at = datetime.utcnow()
                db.commit()

                logger.info(f"会话标题已更新: {new_title}")
            except Exception as title_error:
                logger.error(f"生成标题失败: {title_error}")
                # 标题生成失败不影响主流程,使用默认标题

        # 获取历史消息作为上下文
        history = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp).limit(10).all()

        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]

        # 如果启用RAG，获取相关文档
        sources = None
        rag_metadata = None
        if request.use_rag:
            msg = ""
            if len(request.message) > 50:
                msg = request.message[:50]
            else:
                msg = request.message

            logger.info(f"开始检索相关文档: {msg}...")

            try:
                # 使用新的ChatRAGService (多领域检索)
                chat_rag_service = ChatRAGService(db=db)
                sources, rag_metadata = await chat_rag_service.search_for_chat(
                    query=request.message,
                    session_id=session_id,
                    top_k=5,
                    similarity_threshold=0.2,
                    namespace=request.namespace  # 传递用户指定的领域参数
                )

                if sources:
                    # 将相关文档添加到上下文
                    context = "\n".join([doc["content"] for doc in sources[:3]])
                    messages.append({
                        "role": "system",
                        "content": f"参考以下文档内容回答用户问题：\n{context}"
                    })

                    # 记录检索元数据
                    if rag_metadata:
                        logger.info(
                            f"检索完成: mode={rag_metadata.get('retrieval_mode')}, "
                            f"domain={rag_metadata.get('classification', {}).get('namespace')}, "
                            f"results={len(sources)}, "
                            f"latency={rag_metadata.get('total_latency_ms', 0):.0f}ms"
                        )

            except Exception as e:
                logger.error(f"多领域检索失败，降级到旧方法: {e}")
                # 降级到旧RAG方法
                try:
                    sources = await rag_service.search_relevant_docs(
                        request.message,
                        similarity_threshold=0.2
                    )
                    if sources:
                        context = "\n".join([doc["content"] for doc in sources[:3]])
                        messages.append({
                            "role": "system",
                            "content": f"参考以下文档内容回答用户问题：\n{context}"
                        })
                except Exception as e2:
                    logger.error(f"RAG检索完全失败: {e2}")
                    # 完全失败时，继续对话但不使用RAG
                    sources = None

        # 生成响应
        if request.stream:
            # 流式响应
            return StreamingResponse(
                llm_svc.stream_completion(
                    messages=messages,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    session_id=session_id,
                    db=db
                ),
                media_type="text/event-stream"
            )
        else:
            # 非流式响应
            response = await llm_svc.get_completion(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )

            # 保存助手响应
            assistant_message = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=response["content"],
                message_metadata={
                    "model": request.model,
                    "tokens": response.get("tokens_used", 0)
                }
            )
            db.add(assistant_message)
            db.commit()

            # 构建响应
            chat_response = ChatResponse(
                session_id=session_id,
                message=response["content"],
                sources=sources,
                tokens_used=response.get("tokens_used"),
                timestamp=datetime.utcnow()
            )

            # 添加扩展信息(可选)
            if rag_metadata:
                chat_response.domain_classification = rag_metadata.get('classification')
                chat_response.retrieval_stats = {
                    'retrieval_mode': rag_metadata.get('retrieval_mode'),
                    'retrieval_method': rag_metadata.get('retrieval_method'),
                    'total_latency_ms': rag_metadata.get('total_latency_ms'),
                    'total_results': rag_metadata.get('total_results')
                }

            return chat_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/send", response_model=ChatResponse)
async def send_message_get(
    session_id: Optional[str] = None,
    message: str = "",
    use_rag: bool = True,
    stream: bool = True,
    model: str = "gpt-3.5-turbo",
    namespace: Optional[str] = None,  # 添加知识领域参数
    llm_svc: LLMService = Depends(get_llm_service),
    db: Session = Depends(get_db)
):
    """
    发送聊天消息 (GET方法,支持URL参数)
    """
    try:
        # 构建请求对象
        request = ChatRequest(
            session_id=session_id,
            message=message,
            use_rag=use_rag,
            stream=stream,
            model=model,
            namespace=namespace  # 传递 namespace 参数
        )
        return await send_message(request, llm_svc, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/sessions", response_model=List[SessionResponse])
async def get_sessions(db: Session = Depends(get_db)):
    """获取所有聊天会话"""
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()

    result = []
    for session in sessions:
        message_count = len(session.messages)
        last_message = None
        if session.messages:
            last_msg = sorted(session.messages, key=lambda m: m.timestamp)[-1]
            last_message = last_msg.content[:100] if len(last_msg.content) > 100 else last_msg.content

        result.append(SessionResponse(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count,
            last_message=last_message
        ))

    return result

@router.post("/chat/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreate, db: Session = Depends(get_db)):
    """创建新的聊天会话"""
    session_id = str(uuid.uuid4())

    session = ChatSession(
        session_id=session_id,
        title=request.title,
        session_metadata=request.metadata
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return SessionResponse(
        session_id=session.session_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
        last_message=None
    )

@router.get("/chat/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """获取会话的所有消息"""
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp).all()

    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp,
            "metadata": msg.message_metadata
        }
        for msg in messages
    ]

@router.delete("/chat/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """删除聊天会话"""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()

    return {"message": "Session deleted successfully"}

@router.put("/chat/sessions/{session_id}")
async def update_session_title(
    session_id: str,
    title: str,
    db: Session = Depends(get_db)
):
    """更新会话标题"""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.title = title
    session.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Session title updated successfully"}

@router.get("/chat/history")
async def get_query_history(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    获取查询历史记录
    支持分页
    """
    try:
        # 计算总数
        total = db.query(ChatSession).count()

        # 获取分页会话，按更新时间倒序
        sessions = db.query(ChatSession)\
            .order_by(ChatSession.updated_at.desc())\
            .offset((page - 1) * page_size)\
            .limit(page_size)\
            .all()

        # 转换为历史记录格式
        history = []
        for session in sessions:
            # 获取会话中的第一条用户消息作为查询
            first_user_message = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.session_id,
                ChatMessage.role == "user"
            ).order_by(ChatMessage.timestamp.asc()).first()

            if first_user_message:
                history.append({
                    "id": session.session_id,
                    "query": first_user_message.content,
                    "timestamp": session.created_at.isoformat(),
                    "session_id": session.session_id,
                    "title": session.title
                })

        # 返回分页数据和元信息
        return {
            "data": history,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))