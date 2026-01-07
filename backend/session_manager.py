from sqlalchemy.orm import Session as DBSession
from models import Session, Message
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import List, Optional
import uuid


class SessionManager:
    def __init__(self, db: DBSession):
        self.db = db

    def create_session(self, session_name: Optional[str] = None) -> Session:
        session = Session(id=str(uuid.uuid4()), session_name=session_name)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self.db.query(Session).filter(Session.id == session_id).first()

    def enable_rag(self, session_id: str, documents_path: str, description: str = None) -> Session:
        session = self.get_session(session_id)
        if session:
            session.rag_enabled = True
            session.rag_documents_path = documents_path
            session.rag_description = description
            self.db.commit()
            self.db.refresh(session)
        return session

    def save_message(self, session_id: str, role: str, content: str) -> Message:
        message = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_chat_history(self, session_id: str) -> List[BaseMessage]:
        session = self.get_session(session_id)
        if not session:
            return []
        
        chat_history = []
        for msg in session.messages:
            if msg.role == "human":
                chat_history.append(HumanMessage(content=msg.content))
            elif msg.role == "ai":
                chat_history.append(AIMessage(content=msg.content))
        
        return chat_history

    def list_sessions(self) -> List[Session]:
        return self.db.query(Session).all()

    def delete_session(self, session_id: str) -> bool:
        session = self.get_session(session_id)
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        return False
