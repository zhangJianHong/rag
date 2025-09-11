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

# 创建路由器实例
router = APIRouter()
logger = logging.getLogger(__name__)

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

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """处理文档上传请求"""
    try:
        # 验证文件类型
        if not file.filename.endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")
        
        # 读取文件内容
        file_content = await file.read()
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
        
        # 生成向量嵌入
        embedding = await embedding_service.create_embedding(text_content)
        
        # 创建文档记录
        document = Document(
            content=text_content,
            embedding=embedding,
            doc_metadata=json.dumps({
                "filename": file.filename,
                "size": len(file_content),
                "type": file.filename.split('.')[-1]
            }),
            filename=file.filename,
            created_at=str(datetime.now())
        )
        
        # 保存到数据库
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return {
            "message": "Document uploaded successfully",
            "document_id": document.id,
            "filename": file.filename
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