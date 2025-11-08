"""
RAG服务 - 处理检索增强生成

改进记录 (2025-11-08):
1. 嵌入获取方式优化：
   - 原: 使用 self.llm_service.get_embeddings() (仅支持OpenAI)
   - 新: 使用 embedding_service.create_embedding() (支持OpenAI + HuggingFace)
   - 优势: LRU缓存、批量处理、多后端支持、性能提升

2. 服务分层清晰：
   - embedding_service: 专负责向量嵌入
   - llm_service: 专负责文本生成
   - 职责分离，便于维护和扩展
"""
from typing import List, Dict, Any
from venv import logger
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.embedding import embedding_service
from app.services.llm_service import LLMService
from app.models.document import Document, DocumentChunk
from app.config.settings import get_settings

settings = get_settings()

class RAGService:
    """RAG服务类"""

    def __init__(self):
        """初始化RAG服务"""
        # 创建数据库连接
        engine = create_engine(settings["db_url"])
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.db = SessionLocal()

        # LLM服务用于生成响应（RAG的生成阶段）
        self.llm_service = LLMService()

    async def search_relevant_docs(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        搜索相关文档
        """
        try:
            # 获取查询的向量嵌入（使用 embedding_service，支持缓存和多后端）
            query_embedding = await embedding_service.create_embedding(query)

            # 从数据库查询所有文档块
            chunks = self.db.query(DocumentChunk).all()

            if not chunks:
                return []

            # 计算相似度
            results = []
            for chunk in chunks:
                if chunk.embedding:
                    # 直接使用 embedding（PostgreSQL ARRAY类型返回列表）
                    similarity = self._cosine_similarity(query_embedding, chunk.embedding)
                    if similarity >= similarity_threshold:
                        results.append({
                            "chunk_id": chunk.id,
                            "document_id": chunk.document_id,
                            "content": chunk.content,
                            "similarity": float(similarity),
                            "metadata": chunk.chunk_metadata
                        })

            # 按相似度排序并返回top_k个结果
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"RAG search error: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def generate_augmented_response(
        self,
        query: str,
        context_docs: List[Dict[str, Any]],
        model: str = None,
        temperature: float = 0.7
    ) -> str:
        """
        使用检索到的文档生成增强响应
        """
        # 构建上下文
        context = "\n\n".join([
            f"文档 {i+1}:\n{doc['content']}"
            for i, doc in enumerate(context_docs)
        ])

        # 构建提示
        messages = [
            {
                "role": "system",
                "content": "你是一个基于文档的智能助手。请根据提供的文档内容回答用户的问题。如果文档中没有相关信息，请诚实地告知用户。"
            },
            {
                "role": "user",
                "content": f"参考文档：\n{context}\n\n用户问题：{query}\n\n请基于以上文档内容回答问题。"
            }
        ]

        # 生成响应
        response = await self.llm_service.get_completion(
            messages=messages,
            model=model,
            temperature=temperature
        )

        return response["content"]

    async def rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        model: str = None
    ) -> List[Dict[str, Any]]:
        """
        使用LLM对搜索结果重新排序
        """
        if not results:
            return results

        # 构建重排序提示
        context = "\n".join([
            f"{i+1}. {result['content'][:200]}..."
            for i, result in enumerate(results)
        ])

        messages = [
            {
                "role": "system",
                "content": "你是一个文档相关性评估专家。请根据查询内容对文档的相关性进行排序。"
            },
            {
                "role": "user",
                "content": f"查询：{query}\n\n文档列表：\n{context}\n\n请按相关性从高到低输出文档编号，用逗号分隔。"
            }
        ]

        response = await self.llm_service.get_completion(
            messages=messages,
            model=model,
            temperature=0.3,
            max_tokens=100
        )

        # 解析排序结果
        try:
            order = [int(x.strip()) - 1 for x in response["content"].split(",")]
            reranked = []
            for idx in order:
                if 0 <= idx < len(results):
                    reranked.append(results[idx])

            # 添加未被排序的结果
            for i, result in enumerate(results):
                if i not in order:
                    reranked.append(result)

            return reranked
        except:
            # 如果解析失败，返回原始结果
            return results

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'db'):
            self.db.close()