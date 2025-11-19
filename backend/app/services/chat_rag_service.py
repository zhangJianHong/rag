"""
Chat专用的RAG服务
整合领域分类、混合检索、跨域检索，提供简化的chat接口
"""

import time
import logging
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session

from app.services.domain_classifier import HybridClassifier
from app.services.hybrid_retrieval import HybridRetrieval
from app.services.cross_domain_retrieval import CrossDomainRetrieval
from app.services.bm25_retrieval import BM25Retrieval
from app.services.llm_service import LLMService
from app.services.query_performance import QueryPerformanceLogger

logger = logging.getLogger(__name__)


class ChatRAGService:
    """
    Chat专用的RAG检索服务

    特点:
    - 自动领域分类
    - 自动选择检索模式(单领域/跨领域)
    - 多层降级策略
    - 性能监控集成
    - 返回兼容旧格式的结果
    """

    def __init__(self, db: Session):
        """
        初始化Chat RAG服务

        Args:
            db: 数据库会话
        """
        self.db = db

        # 初始化各个服务组件
        self.llm_service = LLMService(db=db)
        self.classifier = HybridClassifier(db=db, llm_service=self.llm_service)
        self.hybrid_retrieval = HybridRetrieval(db=db)
        self.cross_domain_retrieval = CrossDomainRetrieval(db=db)
        self.bm25_retrieval = BM25Retrieval(db=db)
        self.perf_logger = QueryPerformanceLogger(db=db)

        # 配置参数
        self.classification_confidence_threshold = 0.6  # 分类置信度阈值
        self.default_top_k = 5
        self.default_alpha = 0.5  # 混合检索权重
        self.default_similarity_threshold = 0.2

    async def search_for_chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        namespace: Optional[str] = None  # 新增:可选的知识领域参数
    ) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        为Chat优化的检索接口

        流程:
        1. 领域分类(如果未提供namespace)
        2. 根据置信度决定检索模式(单领域/跨领域)
        3. 执行混合检索(向量+BM25)
        4. 多层降级策略
        5. 记录性能日志

        Args:
            query: 用户查询
            session_id: 会话ID(用于性能追踪)
            top_k: 返回结果数量
            similarity_threshold: 相似度阈值
            namespace: 可选的知识领域过滤,如果提供则跳过自动分类,直接使用指定领域

        Returns:
            (sources, metadata)
            - sources: 兼容旧格式的检索结果列表
              格式: [{"chunk_id": int, "content": str, "similarity": float, "filename": str}]
            - metadata: 扩展信息(领域分类、性能统计等)
        """
        start_time = time.time()
        top_k = top_k or self.default_top_k
        similarity_threshold = similarity_threshold or self.default_similarity_threshold

        # 用于性能追踪的数据
        performance_data = {
            'top_k': top_k,
            'similarity_threshold': similarity_threshold,
            'alpha': self.default_alpha
        }

        classification_result = None
        retrieval_mode = 'unknown'
        target_namespace = namespace or 'default'  # 使用提供的namespace或默认值
        confidence = 1.0  # 默认置信度

        try:
            # Step 1: 领域分类(如果未提供namespace)
            classification_latency = 0.0

            if namespace:
                # 用户显式指定了领域,跳过自动分类
                logger.info(f"使用用户指定的领域: namespace={namespace}")
                classification_result = {
                    'namespace': namespace,
                    'confidence': 1.0,  # 用户指定的领域,置信度为1.0
                    'method': 'user_specified'
                }
                retrieval_mode = 'single'  # 直接使用单领域检索
            else:
                # 执行自动领域分类
                classification_start = time.time()
                classification_result = await self._classify_query(query)
                classification_latency = (time.time() - classification_start) * 1000
                performance_data['classification_latency_ms'] = classification_latency

                target_namespace = classification_result.get('namespace', 'default')
                confidence = classification_result.get('confidence', 0.0)

                logger.info(
                    f"领域分类结果: namespace={target_namespace}, "
                    f"confidence={confidence:.2f}, "
                    f"latency={classification_latency:.0f}ms"
                )

                # 根据置信度决定检索模式
                if confidence >= self.classification_confidence_threshold:
                    retrieval_mode = 'single'
                else:
                    retrieval_mode = 'cross'
                    logger.info(f"置信度较低({confidence:.2f}), 启用跨领域检索")

            # Step 2: 执行检索
            retrieval_start = time.time()

            if retrieval_mode == 'single':
                # 单领域检索
                results, error = await self._single_domain_search(
                    query=query,
                    namespace=target_namespace,
                    top_k=top_k
                )
            else:
                # 跨领域检索
                results, error = await self._cross_domain_search(
                    query=query,
                    top_k=top_k
                )

            retrieval_latency = (time.time() - retrieval_start) * 1000
            performance_data['retrieval_latency_ms'] = retrieval_latency
            performance_data['namespace'] = target_namespace

            # Step 3: 转换为兼容格式
            sources = self._convert_to_legacy_format(results)

            # Step 4: 构建元数据
            total_latency = (time.time() - start_time) * 1000
            metadata = {
                'classification': classification_result,
                'retrieval_mode': retrieval_mode,
                'retrieval_method': 'hybrid',
                'total_latency_ms': total_latency,
                'classification_latency_ms': classification_latency,
                'retrieval_latency_ms': retrieval_latency,
                'total_results': len(sources),
                'error': error
            }

            # Step 5: 记录性能日志
            self._log_performance(
                query=query,
                retrieval_mode=retrieval_mode,
                performance_data=performance_data,
                result_data={
                    'total_candidates': len(results),
                    'total_results': len(sources),
                    'namespace': target_namespace
                },
                session_id=session_id,
                error=error
            )

            logger.info(
                f"检索完成: mode={retrieval_mode}, "
                f"results={len(sources)}, "
                f"total_latency={total_latency:.0f}ms"
            )

            return sources, metadata

        except Exception as e:
            logger.error(f"Chat RAG检索失败: {e}", exc_info=True)

            # 记录错误
            total_latency = (time.time() - start_time) * 1000
            self._log_performance(
                query=query,
                retrieval_mode=retrieval_mode,
                performance_data=performance_data,
                result_data={'total_results': 0},
                session_id=session_id,
                error=str(e)
            )

            # 返回空结果，但不中断对话
            return [], {
                'error': str(e),
                'total_latency_ms': total_latency,
                'retrieval_mode': retrieval_mode
            }

    async def _classify_query(self, query: str) -> Dict[str, Any]:
        """
        领域分类(带降级)

        Args:
            query: 用户查询

        Returns:
            分类结果字典
        """
        try:
            # 调用混合分类器
            result = await self.classifier.classify(query)
            return result.to_dict() if hasattr(result, 'to_dict') else {
                'namespace': getattr(result, 'namespace', 'default'),
                'confidence': getattr(result, 'confidence', 0.5),
                'method': getattr(result, 'method', 'hybrid'),
                'reasoning': getattr(result, 'reasoning', ''),
                'fallback_to_cross_domain': getattr(result, 'fallback_to_cross_domain', False)
            }
        except Exception as e:
            logger.warning(f"领域分类失败，使用默认领域: {e}")
            # 降级: 返回默认领域
            return {
                'namespace': 'default',
                'confidence': 0.3,
                'method': 'fallback',
                'reasoning': f'分类失败: {str(e)}',
                'fallback_to_cross_domain': True  # 分类失败时启用跨域
            }

    async def _single_domain_search(
        self,
        query: str,
        namespace: str,
        top_k: int
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        单领域混合检索(带多层降级)

        降级链: 混合检索 → 向量检索 → BM25检索 → 空结果

        Args:
            query: 用户查询
            namespace: 领域命名空间
            top_k: 返回结果数量

        Returns:
            (results, error_message)
        """
        # Level 1: 混合检索 (最佳效果)
        try:
            results = await self.hybrid_retrieval.search_by_namespace(
                query=query,
                namespace=namespace,
                top_k=top_k,
                alpha=self.default_alpha,
                use_rrf=True
            )

            if results:
                logger.debug(f"混合检索成功: {len(results)} 条结果")
                return results, None
            else:
                logger.info("混合检索无结果，尝试降级")

        except Exception as e:
            logger.warning(f"混合检索失败: {e}")

        # Level 2: 向量检索 (降级)
        try:
            # 使用hybrid_retrieval的向量检索能力
            results = await self.hybrid_retrieval.search_by_namespace(
                query=query,
                namespace=namespace,
                top_k=top_k,
                alpha=1.0,  # alpha=1.0 表示纯向量检索
                use_rrf=False
            )

            if results:
                logger.info(f"向量检索成功(降级): {len(results)} 条结果")
                return results, "降级到向量检索"
            else:
                logger.info("向量检索无结果，继续降级")

        except Exception as e:
            logger.warning(f"向量检索失败: {e}")

        # Level 3: BM25检索 (再次降级)
        try:
            results = await self.bm25_retrieval.search_by_namespace(
                query=query,
                namespace=namespace,
                top_k=top_k
            )

            if results:
                logger.info(f"BM25检索成功(降级): {len(results)} 条结果")
                return results, "降级到BM25检索"
            else:
                logger.info("BM25检索无结果")

        except Exception as e:
            logger.warning(f"BM25检索失败: {e}")

        # Level 4: 返回空结果
        logger.warning(f"所有检索方法失败，领域: {namespace}")
        return [], "所有检索方法均失败"

    async def _cross_domain_search(
        self,
        query: str,
        top_k: int
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        跨领域检索(带降级)

        Args:
            query: 用户查询
            top_k: 返回结果数量

        Returns:
            (results, error_message)
        """
        try:
            # 获取所有启用的领域
            from app.models.knowledge_domain import KnowledgeDomain
            domains = self.db.query(KnowledgeDomain).filter(
                KnowledgeDomain.is_active == True
            ).all()

            namespaces = [d.namespace for d in domains]

            if not namespaces:
                logger.warning("没有启用的领域，降级到单领域检索")
                return await self._single_domain_search(
                    query=query,
                    namespace='default',
                    top_k=top_k
                )

            # 调用跨领域检索服务
            results = await self.cross_domain_retrieval.search_across_domains(
                query=query,
                namespaces=namespaces,
                top_k=top_k,
                alpha=self.default_alpha
            )

            if results:
                logger.info(f"跨领域检索成功: {len(results)} 条结果")
                return results, None
            else:
                logger.info("跨领域检索无结果")
                return [], "跨领域检索无结果"

        except Exception as e:
            logger.error(f"跨领域检索失败: {e}")
            # 降级到默认领域的单领域检索
            logger.info("跨领域检索失败，降级到默认领域")
            return await self._single_domain_search(
                query=query,
                namespace='default',
                top_k=top_k
            )

    def _convert_to_legacy_format(self, results: List[Any]) -> List[Dict[str, Any]]:
        """
        将检索结果转换为旧格式，保持向后兼容

        新格式:
        - Dict 格式: {chunk_id, content, score, ...}
        - Tuple 格式: (chunk_dict, score)

        旧格式: {chunk_id, content, similarity, filename}

        Args:
            results: 检索结果列表 (可能是Dict或Tuple)

        Returns:
            兼容旧格式的结果列表
        """
        legacy_sources = []

        for item in results:
            # 处理不同的返回格式
            if isinstance(item, tuple):
                # 检查元组长度
                if len(item) == 3:
                    # 跨领域检索返回 (chunk_dict, namespace, score) 格式
                    result, namespace, score = item
                    result = dict(result)  # 确保是字典
                    if 'score' not in result and 'similarity' not in result:
                        result['similarity'] = score
                    # 保留namespace信息
                    if 'namespace' not in result:
                        result['namespace'] = namespace
                elif len(item) == 2:
                    # BM25 返回 (chunk_dict, score) 格式
                    result, score = item
                    result = dict(result)  # 确保是字典
                    if 'score' not in result and 'similarity' not in result:
                        result['similarity'] = score
                else:
                    logger.warning(f"未知的元组长度: {len(item)}, 跳过")
                    continue
            elif isinstance(item, dict):
                # 向量检索返回 dict 格式
                result = item
            else:
                logger.warning(f"未知的结果格式: {type(item)}, 跳过")
                continue

            # 提取必要字段
            legacy_source = {
                'chunk_id': result.get('chunk_id') or result.get('id'),
                'content': result.get('content', ''),
                'similarity': result.get('score') or result.get('similarity') or result.get('fusion_score', 0.0),
                'filename': result.get('document_title') or result.get('filename', '未知文档')
            }

            # 可选: 保留一些额外信息(不影响兼容性)
            if 'namespace' in result:
                legacy_source['namespace'] = result['namespace']
            if 'domain_display_name' in result:
                legacy_source['domain_display_name'] = result['domain_display_name']

            legacy_sources.append(legacy_source)

        return legacy_sources

    def _log_performance(
        self,
        query: str,
        retrieval_mode: str,
        performance_data: Dict[str, Any],
        result_data: Dict[str, Any],
        session_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        记录性能日志

        Args:
            query: 查询内容
            retrieval_mode: 检索模式
            performance_data: 性能数据
            result_data: 结果数据
            session_id: 会话ID
            error: 错误信息
        """
        try:
            self.perf_logger.log_query(
                query=query,
                retrieval_mode=retrieval_mode,
                retrieval_method='hybrid',
                performance_data=performance_data,
                result_data=result_data,
                session_id=session_id,
                error=error
            )
        except Exception as e:
            # 性能日志失败不应影响主流程
            logger.warning(f"性能日志记录失败: {e}")


def get_chat_rag_service(db: Session) -> ChatRAGService:
    """
    获取ChatRAGService实例(工厂函数)

    Args:
        db: 数据库会话

    Returns:
        ChatRAGService实例
    """
    return ChatRAGService(db=db)
