"""
文档模型类
存储文档内容和嵌入向量信息
"""
from sqlalchemy import Column, Integer, String, Text, ARRAY, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Document(Base):
    """
    文档模型类
    存储文档内容和嵌入向量信息
    """
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    content = Column(Text, comment="文档内容")
    embedding = Column(ARRAY(Float), comment="文档嵌入向量")  # 使用PostgreSQL ARRAY类型
    doc_metadata = Column(String, comment="文档元数据")  # 重命名避免与SQLAlchemy的metadata冲突
    filename = Column(String, comment="文件名")
    created_at = Column(String, default=lambda: str(datetime.now()), comment="创建时间")

class DocumentChunk(Base):
    """
    文档块模型类
    用于存储文档的分块内容
    """
    __tablename__ = 'document_chunks'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, comment="文档ID")
    content = Column(Text, comment="文档块内容")
    chunk_index = Column(Integer, comment="块索引")
    embedding = Column(ARRAY(Float), comment="文档块嵌入向量")  # 使用PostgreSQL ARRAY类型
    chunk_metadata = Column(String, comment="元数据信息")  # 重命名避免与SQLAlchemy保留字冲突
    filename = Column(String, comment="文件名")  # 添加filename字段
    created_at = Column(String, default=lambda: str(datetime.now()), comment="创建时间")
