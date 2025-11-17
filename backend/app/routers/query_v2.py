"""
查询API v2 - 支持多领域智能检索

提供完整的查询流程:
1. 自动领域分类
2. 单领域/跨领域检索
3. 多种检索方法(向量/BM25/混合)
"""
import time
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.query import QueryRequestV2, QueryResponseV2, ChunkResult, RetrievalStats
from app.models.database import User
from app.models.knowledge_domain import KnowledgeDomain
from app.middleware.auth import require_query_ask
from app.services.domain_classifier import get_classifier
from app.services.vector_retrieval import vector_retrieval_service
from app.services.bm25_retrieval import get_bm25_service
from app.services.hybrid_retrieval import get_hybrid_retrieval
from app.config.logging_config import get_app_logger

router = APIRouter()
logger = get_app_logger()


@router.post("/query/v2", response_model=QueryResponseV2)
async def query_documents_v2(
    request: QueryRequestV2,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_query_ask)
):
    """
    查询文档 v2 (支持自动分类和多领域检索)

    检索模式:
    - auto: 自动识别领域并决定检索策略
    - single: 单领域精确检索
    - cross: 跨领域检索

    检索方法:
    - vector: 纯向量检索(语义相似度)
    - bm25: 纯关键词检索(BM25算法)
    - hybrid: 混合检索(推荐,准确度最高)
    """
    start_time = time.time()

    try:
        logger.info(f"查询v2: {request.query}, mode={request.retrieval_mode}, method={request.retrieval_method}")

        # === 步骤 1: 领域分类 ===
        namespace = request.namespace
        retrieval_mode = request.retrieval_mode or 'auto'
        classification_result = None

        if not namespace or retrieval_mode == 'auto':
            # 自动分类
            classifier = get_classifier(
                db=db,
                classifier_type='hybrid'  # 使用混合分类器
            )

            classification_result = await classifier.classify(
                query=request.query,
                context={
                    'user_id': current_user.id,
                    'session_id': request.session_id
                }
            )

            namespace = classification_result.namespace

            # 判断是否需要跨领域检索
            if classification_result.fallback_to_cross_domain:
                retrieval_mode = 'cross'
                logger.info(f"低置信度({classification_result.confidence:.2f}),切换到跨领域检索")
            else:
                retrieval_mode = 'single'

        # === 步骤 2: 执行检索 ===
        if retrieval_mode == 'single':
            # 单领域检索
            results = await _single_domain_retrieval(
                query=request.query,
                namespace=namespace,
                top_k=request.top_k,
                method=request.retrieval_method,
                alpha=request.alpha,
                similarity_threshold=request.similarity_threshold,
                db=db
            )

            # 转换为ChunkResult格式
            chunk_results = [
                await _chunk_to_result(chunk, namespace, db)
                for chunk in results
            ]

        elif retrieval_mode == 'cross':
            # 跨领域检索(暂时使用单领域实现,后续Week 2实现)
            logger.warning("跨领域检索功能将在Week 2实现,暂时降级到单领域")
            results = await _single_domain_retrieval(
                query=request.query,
                namespace=namespace,
                top_k=request.top_k,
                method=request.retrieval_method,
                alpha=request.alpha,
                similarity_threshold=request.similarity_threshold,
                db=db
            )

            chunk_results = [
                await _chunk_to_result(chunk, namespace, db)
                for chunk in results
            ]

        else:
            raise HTTPException(
                status_code=400,
                detail=f"未知的检索模式: {retrieval_mode}"
            )

        # === 步骤 3: 构建响应 ===
        latency_ms = (time.time() - start_time) * 1000

        response = QueryResponseV2(
            query_id=str(uuid.uuid4()),
            query=request.query,
            domain_classification=classification_result.to_dict() if classification_result else None,
            retrieval_mode=retrieval_mode,
            retrieval_method=request.retrieval_method,
            results=chunk_results,
            cross_domain_results=None,  # Week 2实现
            retrieval_stats=RetrievalStats(
                total_candidates=len(chunk_results),
                method=request.retrieval_method,
                latency_ms=latency_ms
            )
        )

        logger.info(f"查询完成: {len(chunk_results)} 结果, 耗时 {latency_ms:.2f}ms")
        return response

    except Exception as e:
        logger.error(f"查询失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )


async def _single_domain_retrieval(
    query: str,
    namespace: str,
    top_k: int,
    method: str,
    alpha: float,
    similarity_threshold: float,
    db: Session
) -> List[Dict[str, Any]]:
    """
    单领域检索

    Args:
        query: 查询文本
        namespace: 领域命名空间
        top_k: 返回结果数
        method: 检索方法(vector/bm25/hybrid)
        alpha: 混合检索权重
        similarity_threshold: 相似度阈值
        db: 数据库会话

    Returns:
        检索结果列表
    """
    if method == 'vector':
        # 纯向量检索
        return await vector_retrieval_service.search_by_namespace(
            db=db,
            query_text=query,
            namespace=namespace,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )

    elif method == 'bm25':
        # 纯BM25检索
        bm25_service = get_bm25_service(db)
        results = await bm25_service.search_by_namespace(
            query=query,
            namespace=namespace,
            top_k=top_k
        )
        # 转换格式(去掉score元组)
        return [chunk for chunk, score in results]

    elif method == 'hybrid':
        # 混合检索
        hybrid_service = get_hybrid_retrieval(db)
        return await hybrid_service.search_by_namespace(
            query=query,
            namespace=namespace,
            top_k=top_k,
            alpha=alpha
        )

    else:
        raise ValueError(f"未知的检索方法: {method}")


async def _chunk_to_result(
    chunk: Dict[str, Any],
    namespace: str,
    db: Session
) -> ChunkResult:
    """
    将文档块转换为ChunkResult格式

    Args:
        chunk: 文档块字典
        namespace: 领域命名空间
        db: 数据库会话

    Returns:
        ChunkResult对象
    """
    # 获取领域信息
    domain = db.query(KnowledgeDomain).filter(
        KnowledgeDomain.namespace == namespace
    ).first()

    return ChunkResult(
        chunk_id=chunk['id'],
        content=chunk['content'],
        score=chunk.get('similarity', chunk.get('fusion_score', 0.0)),
        namespace=namespace,
        domain_display_name=domain.display_name if domain else namespace,
        domain_color=domain.color if domain else '#999999',
        domain_icon=domain.icon if domain else 'folder',
        document_id=chunk['document_id'],
        document_title=chunk.get('filename', '未知文档'),
        chunk_index=chunk.get('chunk_index'),
        metadata=chunk.get('metadata', {})
    )


@router.get("/query/methods", summary="获取支持的检索方法")
async def get_retrieval_methods():
    """
    获取所有支持的检索方法及说明
    """
    return {
        "success": True,
        "data": {
            "retrieval_methods": [
                {
                    "method": "vector",
                    "name": "向量检索",
                    "description": "基于语义相似度的检索",
                    "pros": ["理解语义", "支持同义词", "跨语言"],
                    "cons": ["依赖embedding质量", "计算成本较高"],
                    "use_cases": ["语义查询", "模糊查询"]
                },
                {
                    "method": "bm25",
                    "name": "关键词检索",
                    "description": "基于BM25算法的关键词匹配",
                    "pros": ["精确匹配", "速度快", "可解释性强"],
                    "cons": ["无法理解语义", "对同义词不敏感"],
                    "use_cases": ["精确查询", "关键词搜索"]
                },
                {
                    "method": "hybrid",
                    "name": "混合检索",
                    "description": "结合向量和BM25的混合检索(推荐)",
                    "pros": ["准确度最高", "兼顾语义和关键词", "鲁棒性强"],
                    "cons": ["计算成本略高"],
                    "use_cases": ["通用场景(推荐默认使用)"]
                }
            ],
            "retrieval_modes": [
                {
                    "mode": "auto",
                    "name": "自动模式",
                    "description": "自动识别领域并选择检索策略"
                },
                {
                    "mode": "single",
                    "name": "单领域模式",
                    "description": "在指定领域内精确检索"
                },
                {
                    "mode": "cross",
                    "name": "跨领域模式",
                    "description": "在多个领域中检索并融合结果"
                }
            ]
        }
    }


@router.get("/query/test", summary="测试查询功能")
async def test_query(
    query: str = "如何配置API",
    namespace: Optional[str] = None,
    method: str = "hybrid",
    db: Session = Depends(get_db)
):
    """
    快速测试查询功能
    """
    try:
        request = QueryRequestV2(
            query=query,
            namespace=namespace,
            retrieval_mode='single' if namespace else 'auto',
            retrieval_method=method,
            top_k=5
        )

        # 创建临时用户对象(测试用)
        class TempUser:
            id = 1
            username = "test"

        # 模拟查询
        results = await _single_domain_retrieval(
            query=query,
            namespace=namespace or 'default',
            top_k=5,
            method=method,
            alpha=0.5,
            similarity_threshold=0.0,
            db=db
        )

        return {
            "success": True,
            "query": query,
            "namespace": namespace,
            "method": method,
            "result_count": len(results),
            "results": results[:3]  # 只返回前3个结果
        }

    except Exception as e:
        logger.error(f"测试查询失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }
