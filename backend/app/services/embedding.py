import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings
from app.config.settings import OPENAI_API_KEY, EMBEDDING_MODEL, OPENAI_API_URL
from app.config.logging_config import get_app_logger
from typing import List, Optional, Union
import asyncio
from functools import lru_cache

logger = get_app_logger()

class EmbeddingService:
    """
    嵌入服务类
    负责将文本转换为向量表示，并提供向量相似度计算功能
    支持多种嵌入后端：OpenAI、HuggingFace本地模型等
    """
    
    def __init__(self, 
                 backend: str = "openai",
                 model_name: Optional[str] = None,
                 device: str = "auto",
                 cache_size: int = 1000):
        """
        初始化嵌入服务
        
        Args:
            backend (str): 嵌入后端类型，支持 "openai", "huggingface"
            model_name (str): 模型名称，如果为None则使用配置文件中的默认值
            device (str): 设备类型，"auto", "cpu", "cuda"
            cache_size (int): 缓存大小
        """
        self.backend = backend
        self.cache_size = cache_size
        self._embedding_cache = {}
        
        # 初始化嵌入模型
        if backend == "openai":
            self._init_openai_embeddings(model_name)
        elif backend == "huggingface":
            self._init_huggingface_embeddings(model_name, device)
        else:
            raise ValueError(f"不支持的嵌入后端: {backend}")
    
    def _init_openai_embeddings(self, model_name: Optional[str]):
        """初始化OpenAI嵌入模型"""
        model = model_name or EMBEDDING_MODEL
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            openai_api_base=OPENAI_API_URL,
            model=model
        )
        logger.info(f"已初始化OpenAI嵌入模型: {model}")
    
    def _init_huggingface_embeddings(self, model_name: Optional[str], device: str):
        """初始化HuggingFace嵌入模型"""
        model = model_name or "sentence-transformers/all-MiniLM-L6-v2"
        
        # 自动检测设备
        if device == "auto":
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}  # 标准化嵌入向量
        )
        logger.info(f"已初始化HuggingFace嵌入模型: {model} (设备: {device})")
    
    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        import hashlib
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _manage_cache(self, cache_key: str, embedding: List[float]):
        """管理缓存，实现简单的LRU策略"""
        if len(self._embedding_cache) >= self.cache_size:
            # 删除最旧的缓存项
            oldest_key = next(iter(self._embedding_cache))
            del self._embedding_cache[oldest_key]
        
        self._embedding_cache[cache_key] = embedding
    
    async def create_embedding(self, text: str) -> List[float]:
        """
        为单个文本创建嵌入向量
        
        Args:
            text (str): 需要转换为向量的文本
            
        Returns:
            List[float]: 文本对应的嵌入向量
            
        Raises:
            Exception: 当嵌入创建失败时抛出异常
        """
        try:
            # 检查缓存
            cache_key = self._get_cache_key(text)
            if cache_key in self._embedding_cache:
                logger.debug(f"从缓存获取嵌入向量: {text[:50]}...")
                return self._embedding_cache[cache_key]
            
            # 在线程池中执行嵌入计算（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self.embeddings.embed_query, 
                text
            )
            
            # 缓存结果
            self._manage_cache(cache_key, embedding)
            
            logger.debug(f"成功创建嵌入向量: {text[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"创建嵌入向量失败: {e}")
            raise
    
    async def create_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        为多个文本批量创建嵌入向量
        
        Args:
            texts (List[str]): 需要转换为向量的文本列表
            
        Returns:
            List[List[float]]: 文本列表对应的嵌入向量列表
            
        Raises:
            Exception: 当批量嵌入创建失败时抛出异常
        """
        try:
            if not texts:
                return []
            
            # 检查缓存，分离已缓存和未缓存的文本
            cached_embeddings = {}
            uncached_texts = []
            uncached_indices = []
            
            for i, text in enumerate(texts):
                cache_key = self._get_cache_key(text)
                if cache_key in self._embedding_cache:
                    cached_embeddings[i] = self._embedding_cache[cache_key]
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
            
            # 为未缓存的文本创建嵌入向量
            new_embeddings = []
            if uncached_texts:
                loop = asyncio.get_event_loop()
                new_embeddings = await loop.run_in_executor(
                    None,
                    self.embeddings.embed_documents,
                    uncached_texts
                )
                
                # 缓存新创建的嵌入向量
                for text, embedding in zip(uncached_texts, new_embeddings):
                    cache_key = self._get_cache_key(text)
                    self._manage_cache(cache_key, embedding)
            
            # 合并结果，保持原始顺序
            result = [None] * len(texts)
            
            # 填充缓存的嵌入向量
            for i, embedding in cached_embeddings.items():
                result[i] = embedding
            
            # 填充新创建的嵌入向量
            for i, embedding in zip(uncached_indices, new_embeddings):
                result[i] = embedding
            
            logger.debug(f"成功创建批量嵌入向量: {len(texts)}个文本")
            return result
            
        except Exception as e:
            logger.error(f"批量创建嵌入向量失败: {e}")
            raise
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量之间的余弦相似度
        
        Args:
            vec1 (List[float]): 第一个向量
            vec2 (List[float]): 第二个向量
            
        Returns:
            float: 余弦相似度值，范围在-1到1之间
                  1表示完全相似，0表示无关，-1表示完全相反
        """
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            # 计算余弦相似度
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"计算余弦相似度失败: {e}")
            return 0.0
    
    def euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量之间的欧几里得距离
        
        Args:
            vec1 (List[float]): 第一个向量
            vec2 (List[float]): 第二个向量
            
        Returns:
            float: 欧几里得距离
        """
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            return float(np.linalg.norm(vec1 - vec2))
        except Exception as e:
            logger.error(f"计算欧几里得距离失败: {e}")
            return float('inf')
    
    def find_most_similar(self, query_embedding: List[float], 
                         candidate_embeddings: List[List[float]], 
                         top_k: int = 5) -> List[tuple]:
        """
        找到与查询向量最相似的候选向量
        
        Args:
            query_embedding (List[float]): 查询向量
            candidate_embeddings (List[List[float]]): 候选向量列表
            top_k (int): 返回前k个最相似的结果
            
        Returns:
            List[tuple]: [(索引, 相似度分数), ...] 按相似度降序排列
        """
        try:
            similarities = []
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.cosine_similarity(query_embedding, candidate)
                similarities.append((i, similarity))
            
            # 按相似度降序排序
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"查找最相似向量失败: {e}")
            return []
    
    def clear_cache(self):
        """清空嵌入向量缓存"""
        self._embedding_cache.clear()
        logger.info("已清空嵌入向量缓存")
    
    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        return {
            "cache_size": len(self._embedding_cache),
            "max_cache_size": self.cache_size,
            "backend": self.backend
        }

def create_embedding_service(backend: str = "openai", **kwargs) -> EmbeddingService:
    """
    创建嵌入服务实例的工厂函数
    
    Args:
        backend (str): 嵌入后端类型
        **kwargs: 其他初始化参数
        
    Returns:
        EmbeddingService: 嵌入服务实例
    """
    return EmbeddingService(backend=backend, **kwargs)

# 创建默认的嵌入服务实例
# 可以通过环境变量 EMBEDDING_BACKEND 来指定后端类型
import os
default_backend = os.getenv("EMBEDDING_BACKEND", "openai")
embedding_service = create_embedding_service(backend=default_backend)