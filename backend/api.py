from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session as DBSession
from database import get_db, init_db
from session_manager import SessionManager
from schemas import (
    CreateSessionRequest,
    EnableRAGRequest,
    QueryRequest,
    SessionResponse,
    SessionSchema
)
from agent import CustomAgentExecutor, QueueCallbackHandler
from tools.rag_tools import prepare_rag_vector_store
import asyncio
import json
from typing import AsyncGenerator

app = FastAPI(title="Beacon Agent API", version="1.0.0")

# Allow browser apps to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.on_event("startup")
async def startup_event():
    init_db()


@app.post("/sessions/create", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest | None = None,
    db: DBSession = Depends(get_db)
):
    """Create a new conversation session"""
    manager = SessionManager(db)
    session = manager.create_session(session_name=request.session_name if request else None)
    return SessionResponse(
        session_id=session.id,
        session_name=session.session_name,
        message="Session created successfully"
    )


@app.get("/sessions/{session_id}", response_model=SessionSchema)
async def get_session(session_id: str, db: DBSession = Depends(get_db)):
    """Get session details including chat history"""
    manager = SessionManager(db)
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/sessions", response_model=list[SessionSchema])
async def list_sessions(db: DBSession = Depends(get_db)):
    """List all sessions"""
    manager = SessionManager(db)
    return manager.list_sessions()


@app.delete("/sessions/{session_id}", response_model=SessionResponse)
async def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    """Delete a session"""
    manager = SessionManager(db)
    success = manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        session_id=session_id,
        message="Session deleted successfully"
    )


@app.post("/sessions/{session_id}/enable-rag", response_model=SessionResponse)
async def enable_rag(
    session_id: str,
    request: EnableRAGRequest,
    db: DBSession = Depends(get_db)
):
    manager = SessionManager(db)
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.rag_enabled:
        return SessionResponse(
            session_id=session_id,
            message="RAG is already enabled for this session"
        )

    success = prepare_rag_vector_store(request.documents_path)
    
    if success:
        manager.enable_rag(session_id, request.documents_path, request.description)
        return SessionResponse(
            session_id=session_id,
            message=f"RAG enabled successfully with documents from: {request.documents_path}"
        )
    else:

        raise HTTPException(
            status_code=400, 
            detail=f"No supported documents found in: {request.documents_path}"
        )


async def generate_stream(
    query: str,
    session_id: str,
    db: DBSession
) -> AsyncGenerator[str, None]:
    manager = SessionManager(db)
    session = manager.get_session(session_id)
    
    if not session:
        yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
        return
    
    chat_history = manager.get_chat_history(session_id)

    rag_documents_path = session.rag_documents_path if session.rag_enabled else None
    rag_description = session.rag_description if session.rag_enabled else None
    agent_executor = CustomAgentExecutor(
        chat_history=chat_history,
        rag_documents_path=rag_documents_path,
        rag_description=rag_description,
    )
    

    queue = asyncio.Queue()
    streamer = QueueCallbackHandler(queue)
    

    task = asyncio.create_task(
        agent_executor.invoke(query, streamer, verbose=False)
    )

    try:
        async for token in streamer:
            if token == "<<STEP_END>>":
                yield f"data: {json.dumps({'type': 'step_end'})}\n\n"
                continue
            elif hasattr(token, 'message'):
                # Check for tool calls
                if tool_calls := token.message.additional_kwargs.get("tool_calls"):
                    if tool_name := tool_calls[0]["function"]["name"]:
                        yield f"data: {json.dumps({'type': 'tool_call', 'tool_name': tool_name})}\n\n"
                    if tool_args := tool_calls[0]["function"]["arguments"]:
                        yield f"data: {json.dumps({'type': 'tool_args', 'args': tool_args})}\n\n"
                content = getattr(token, 'text', None) or (token.message.content if hasattr(token, 'message') else None)
                if content:
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
        
        result = await task
        
        manager.save_message(session_id, "human", query)
        
        if isinstance(result, dict) and "answer" in result:
            answer = result["answer"]
            manager.save_message(session_id, "ai", answer)
            yield f"data: {json.dumps({'type': 'final_answer', 'answer': answer, 'tools_used': result.get('tools_used', [])})}\n\n"
        else:
            manager.save_message(session_id, "ai", str(result))
            yield f"data: {json.dumps({'type': 'final_answer', 'answer': str(result)})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


@app.post("/query/stream")
async def stream_query(
    request: QueryRequest,
    db: DBSession = Depends(get_db)
):
    """Stream agent response for a query"""
    return StreamingResponse(
        generate_stream(request.query, request.session_id, db),
        media_type="text/event-stream"
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Caja Agent API",
        "version": "1.0.0",
        "endpoints": {
            "create_session": "POST /sessions/create",
            "get_session": "GET /sessions/{session_id}",
            "list_sessions": "GET /sessions",
            "delete_session": "DELETE /sessions/{session_id}",
            "enable_rag": "POST /sessions/{session_id}/enable-rag",
            "stream_query": "POST /query/stream"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
