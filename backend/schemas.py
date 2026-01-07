from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class MessageSchema(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class SessionSchema(BaseModel):
    id: str
    session_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    rag_enabled: bool
    rag_documents_path: Optional[str] = None
    rag_description: Optional[str] = None
    messages: List[MessageSchema] = []

    class Config:
        from_attributes = True


class CreateSessionRequest(BaseModel):
    session_name: Optional[str] = None


class EnableRAGRequest(BaseModel):
    documents_path: str
    description: Optional[str] = None  


class QueryRequest(BaseModel):
    query: str
    session_id: str


class SessionResponse(BaseModel):
    session_id: str
    session_name: Optional[str] = None
    message: str
