# 导入必要的FastAPI和数据库相关模块
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.embedding import embedding_service
from app.models.database import Document
from app.models.schemas import DocumentResponse
import PyPDF2
import json
from datetime import datetime
import logging
from typing import List

# 创建路由器实例
router = APIRouter()
logger = logging.getLogger(__name__)

# 配置常量
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_CHUNK_SIZE = 8000  # 每个块的最大字符数
CHUNK_OVERLAP = 200   # 块之间的重叠字符数

def extract_text_from_pdf(file_path: str) -> str:
    """从PDF文件中提取文本内容"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise HTTPException(status_code=400, detail="Failed to extract text from PDF")

def extract_text_from_txt(file_path: str) -> str:
    """从文本文件中读取内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error reading text file: {e}")
        raise HTTPException(status_code=400, detail="Failed to read text file")

def split_text_into_chunks(text: str, chunk_size: int = MAX_CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    将文本分割成多个块
    
    Args:
        text (str): 要分割的文本
        chunk_size (int): 每个块的大小
        overlap (int): 块之间的重叠字符数
        
    Returns:
        List[str]: 分割后的文本块列表
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # 确定当前块的结束位置
        end = start + chunk_size
        
        # 如果不是最后一块，尝试在句号、问号、感叹号处分割
        if end < len(text):
            # 查找最后一个句号、问号、感叹号
            last_sentence_end = text.rfind('。', start, end)
            if last_sentence_end == -1:
                last_sentence_end = text.rfind('？', start, end)
            if last_sentence_end == -1:
                last_sentence_end = text.rfind('！', start, end)
            if last_sentence_end == -1:
                last_sentence_end = text.rfind('.', start, end)
            if last_sentence_end == -1:
                last_sentence_end = text.rfind('?', start, end)
            if last_sentence_end == -1:
                last_sentence_end = text.rfind('!', start, end)
            
            # 如果找到句号，在句号后分割
            if last_sentence_end != -1 and last_sentence_end > start + chunk_size // 2:
                end = last_sentence_end + 1
        
        # 提取当前块
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # 计算下一个块的起始位置（考虑重叠）
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """处理文档上传请求"""
    try:
        # 验证文件类型
        if not file.filename.endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
        
        # 读取文件内容
        file_content = await file.read()
        
        # 验证文件大小
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size allowed: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        file_path = f"/tmp/{file.filename}"
        
        # 保存临时文件
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # 根据文件类型提取文本
        if file.filename.endswith('.pdf'):
            text_content = extract_text_from_pdf(file_path)
        else:
            text_content = extract_text_from_txt(file_path)
        
        # 验证文本内容
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No text content found in file")
        
        # 将文本分割成块
        text_chunks = split_text_into_chunks(text_content)
        logger.info(f"Document split into {len(text_chunks)} chunks")
        
        # 为每个块创建嵌入向量和文档记录
        document_ids = []
        for i, chunk in enumerate(text_chunks):
            try:
                # 生成向量嵌入
                embedding = await embedding_service.create_embedding(chunk)
                
                # 创建文档记录
                document = Document(
                    content=chunk,
                    embedding=embedding,
                    doc_metadata=json.dumps({
                        "filename": file.filename,
                        "size": len(file_content),
                        "type": file.filename.split('.')[-1],
                        "chunk_index": i,
                        "total_chunks": len(text_chunks),
                        "chunk_size": len(chunk)
                    }),
                    filename=f"{file.filename}_chunk_{i+1}",
                    created_at=str(datetime.now())
                )
                
                # 保存到数据库
                db.add(document)
                db.commit()
                db.refresh(document)
                document_ids.append(document.id)
                
            except Exception as chunk_error:
                logger.error(f"Error processing chunk {i+1}: {chunk_error}")
                # 继续处理其他块，不中断整个上传过程
                continue
        
        if not document_ids:
            raise HTTPException(status_code=500, detail="Failed to process any chunks")
        
        return {
            "message": "Document uploaded successfully",
            "document_ids": document_ids,
            "filename": file.filename,
            "chunks_created": len(document_ids),
            "total_chunks": len(text_chunks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(db: Session = Depends(get_db)):
    """获取所有已上传的文档列表"""
    try:
        documents = db.query(Document).all()
        return [
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                content=doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                metadata=json.loads(doc.doc_metadata) if doc.doc_metadata else {},
                created_at=doc.created_at
            )
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")