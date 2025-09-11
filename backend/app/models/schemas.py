from pydantic import BaseModel
from typing import List, Optional
import json

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    sources: List[dict]

class DocumentResponse(BaseModel):
    id: int
    filename: str
    content: str
    metadata: dict
    created_at: str