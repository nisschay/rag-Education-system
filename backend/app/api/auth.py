from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.schemas import User
from pydantic import BaseModel
import os

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

class LoginRequest(BaseModel):
    email: str
    name: str = None

@router.post("/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Simple login - creates user if doesn't exist"""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        user = User(email=request.email, name=request.name or request.email)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # In production, generate proper JWT token
    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "token": f"user_{user.id}"  # Simplified token
    }

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from token"""
    token = credentials.credentials
    
    # Simple validation (improve in production)
    if not token.startswith("user_"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = int(token.replace("user_", ""))
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
