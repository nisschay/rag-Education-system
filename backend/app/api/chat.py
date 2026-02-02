from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.schemas import ChatSession, Message, User, Course
from app.api.auth import get_current_user
from pydantic import BaseModel
from typing import Optional
from app.services.rag_service import rag_service
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    course_id: int
    current_unit_id: Optional[int] = None

class SessionCreate(BaseModel):
    course_id: int
    teaching_mode: str = "qa"

@router.post("/session")
async def create_session(
    request: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    course = db.query(Course).filter(
        Course.id == request.course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    session = ChatSession(
        user_id=current_user.id,
        course_id=request.course_id,
        teaching_mode=request.teaching_mode,
        context={}
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {"session_id": session.id}

@router.post("/message")
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get response (non-streaming)"""
    from app.services.gemini_service import RateLimitError
    
    # Get or create session
    if request.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id,
            ChatSession.user_id == current_user.id
        ).first()
    else:
        session = ChatSession(
            user_id=current_user.id,
            course_id=request.course_id,
            teaching_mode="qa",
            context={}
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session context
    if request.current_unit_id:
        session.current_unit_id = request.current_unit_id
    
    session_context = session.context or {}
    session_context["current_unit_id"] = request.current_unit_id
    
    # Save user message
    user_message = Message(
        session_id=session.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    
    try:
        # Retrieve context
        chunks = await rag_service.retrieve_context(
            course_id=request.course_id,
            query=request.message,
            session_context=session_context
        )
        
        # Get course info
        course = db.query(Course).filter(Course.id == request.course_id).first()
        
        # Generate response
        response_text = await rag_service.generate_response(
            query=request.message,
            retrieved_chunks=chunks,
            session_context=session_context,
            course_name=course.name
        )
    except RateLimitError as e:
        # Return a friendly error message
        response_text = f"⚠️ **Rate Limit Reached**\n\nThe AI service has reached its request limit. Please wait about {e.retry_after} seconds before trying again.\n\nThis happens because the free tier of the Gemini API has a limit of 20 requests per minute."
        chunks = []
    except Exception as e:
        response_text = f"⚠️ **Error**\n\nSorry, there was an error generating a response. Please try again.\n\nError details: {str(e)[:100]}"
        chunks = []
    
    # Save assistant message
    assistant_message = Message(
        session_id=session.id,
        role="assistant",
        content=response_text,
        metadata={"chunks_used": len(chunks)}
    )
    db.add(assistant_message)
    
    db.commit()
    
    return {
        "response": response_text,
        "session_id": session.id,
        "chunks_retrieved": len(chunks)
    }

@router.post("/message/stream")
async def send_message_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get streaming response"""
    
    # Get or create session
    if request.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.id == request.session_id,
            ChatSession.user_id == current_user.id
        ).first()
    else:
        session = ChatSession(
            user_id=current_user.id,
            course_id=request.course_id,
            teaching_mode="qa",
            context={}
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update context
    session_context = session.context or {}
    if request.current_unit_id:
        session_context["current_unit_id"] = request.current_unit_id
    
    # Save user message
    user_message = Message(
        session_id=session.id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    db.commit()
    
    # Retrieve context
    chunks = await rag_service.retrieve_context(
        course_id=request.course_id,
        query=request.message,
        session_context=session_context
    )
    
    course = db.query(Course).filter(Course.id == request.course_id).first()
    
    # Stream response
    async def generate():
        full_response = ""
        async for chunk in rag_service.generate_streaming_response(
            query=request.message,
            retrieved_chunks=chunks,
            session_context=session_context,
            course_name=course.name
        ):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # Save complete response
        assistant_message = Message(
            session_id=session.id,
            role="assistant",
            content=full_response
        )
        db.add(assistant_message)
        db.commit()
        
        yield f"data: {json.dumps({'done': True, 'session_id': session.id})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/sessions")
async def get_sessions(
    course_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all sessions for user"""
    query = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)
    
    if course_id:
        query = query.filter(ChatSession.course_id == course_id)
    
    sessions = query.all()
    return sessions

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages in a session"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.timestamp).all()
    
    return messages
