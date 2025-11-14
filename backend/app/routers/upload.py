# 导入必要的FastAPI和数据库相关模块
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.embedding import embedding_service
from app.models.document import DocumentChunk
from app.models.database import Document, UserDocument, User
from app.models.schemas import DocumentResponse
from app.middleware.auth import get_current_active_user, require_document_upload, require_document_delete, require_document_read
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
MAX_CHUNK_SIZE = 8800  # 每个块的最大字符数
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
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_document_upload)
):
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
        
        # 第一步：创建主文档记录
        from app.models.database import Document
        import uuid

        main_document = Document(
            content=text_content,  # 完整文档内容
            embedding=None,  # 主文档暂时不需要嵌入向量（如果需要可以为完整文档生成）
            doc_metadata=json.dumps({
                "filename": file.filename,
                "size": len(file_content),
                "type": file.filename.split('.')[-1],
                "total_chunks": len(text_chunks),
                "total_size": len(text_content),
                "user_id": current_user.id
            }),
            filename=file.filename,
            created_at=str(datetime.now())
        )

        db.add(main_document)
        db.commit()
        db.refresh(main_document)

        # 创建用户文档关联
        user_document = UserDocument(
            user_id=current_user.id,
            document_id=main_document.id,
            permission_level="write"
        )
        db.add(user_document)

        # 第二步：为每个块创建文档块记录
        document_chunk_ids = []
        for i, chunk in enumerate(text_chunks):
            try:
                # 生成向量嵌入
                embedding = await embedding_service.create_embedding(chunk)

                # 创建文档块记录，关联到主文档
                document_chunk = DocumentChunk(
                    document_id=main_document.id,  # ✅ 关联到主文档
                    content=chunk,
                    embedding=embedding,  # 直接使用向量列表（PostgreSQL ARRAY类型）
                    chunk_metadata=json.dumps({
                        "chunk_index": i,
                        "total_chunks": len(text_chunks),
                        "chunk_size": len(chunk)
                    }),
                    chunk_index=i,
                    filename=f"{file.filename}_chunk_{i+1}",
                    created_at=str(datetime.now())
                )

                # 保存到数据库
                db.add(document_chunk)
                db.commit()
                db.refresh(document_chunk)
                document_chunk_ids.append(document_chunk.id)

            except Exception as chunk_error:
                logger.error(f"Error processing chunk {i+1}: {chunk_error}")
                # 继续处理其他块，不中断整个上传过程
                continue
        
        if not document_chunk_ids:
            raise HTTPException(status_code=500, detail="Failed to process any chunks")

        return {
            "message": "Document uploaded successfully",
            "document_id": main_document.id,  # 主文档ID
            "document_chunk_ids": document_chunk_ids,  # 所有分块ID
            "filename": file.filename,
            "chunks_created": len(document_chunk_ids),
            "total_chunks": len(text_chunks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_document_read)
):
    """获取所有已上传的文档列表"""
    try:
        # 根据用户权限获取文档列表
        from app.services.auth import auth_service
        is_admin = auth_service.has_permission(db, current_user, "user_management")

        if is_admin:
            # 管理员可以看到所有文档
            documents = db.query(Document).all()
        else:
            # 普通用户只能看到自己的文档
            user_documents = db.query(UserDocument).filter(
                UserDocument.user_id == current_user.id
            ).all()
            document_ids = [ud.document_id for ud in user_documents]
            documents = db.query(Document).filter(Document.id.in_(document_ids)).all()

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

@router.get("/documents/stats")
async def get_document_stats(db: Session = Depends(get_db)):
    """获取文档统计信息"""
    try:
        total_docs = db.query(Document).count()

        # 按文件类型统计
        docs_by_type = {}
        documents = db.query(Document).all()
        for doc in documents:
            metadata = json.loads(doc.doc_metadata) if doc.doc_metadata else {}
            file_type = metadata.get("file_type", "unknown")
            docs_by_type[file_type] = docs_by_type.get(file_type, 0) + 1

        # 最近7天的文档
        from datetime import datetime, timedelta
        recent_date = datetime.now() - timedelta(days=7)
        # 使用 cast 将字符串转换为日期时间进行比较
        from sqlalchemy import cast, DateTime
        recent_docs = db.query(Document).filter(
            cast(Document.created_at, DateTime) >= recent_date
        ).count()

        return {
            "total": total_docs,
            "by_type": docs_by_type,
            "recent": recent_docs
        }
    except Exception as e:
        logger.error(f"Error getting document stats: {e}")
        return {
            "total": 0,
            "by_type": {},
            "recent": 0
        }

@router.get("/documents/{document_id}")
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """获取单个文档详情"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            content=document.content,
            metadata=json.loads(document.doc_metadata) if document.doc_metadata else {},
            created_at=document.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document")

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_document_delete)
):
    """删除文档"""
    try:
        # 检查用户是否有权限删除此文档
        user_document = db.query(UserDocument).filter(
            UserDocument.user_id == current_user.id,
            UserDocument.document_id == document_id
        ).first()

        # 如果不是文档所有者，检查是否是管理员
        if not user_document:
            from app.services.auth import auth_service
            is_admin = auth_service.has_permission(db, current_user, "user_management")
            if not is_admin:
                raise HTTPException(status_code=403, detail="Permission denied")

        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # 删除用户文档关联
        if user_document:
            db.delete(user_document)

        # 删除文档
        db.delete(document)
        db.commit()
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

@router.post("/documents/batch")
async def delete_multiple_documents(document_ids: dict, db: Session = Depends(get_db)):
    """批量删除文档"""
    try:
        ids = document_ids.get("ids", [])
        if not ids:
            raise HTTPException(status_code=400, detail="No document IDs provided")

        deleted_count = db.query(Document).filter(Document.id.in_(ids)).delete(synchronize_session=False)
        db.commit()
        return {"message": f"Successfully deleted {deleted_count} documents"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error batch deleting documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete documents")

@router.get("/documents/search")
async def search_documents(query: str = "", db: Session = Depends(get_db)):
    """搜索文档"""
    try:
        if not query:
            return []

        documents = db.query(Document).filter(
            Document.filename.contains(query) |
            Document.content.contains(query)
        ).all()

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
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to search documents")

