"""Authentication API - Production ready with JWT"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.schemas import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.utils.logging_config import get_logger
from datetime import timedelta

logger = get_logger("auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str
    name: str = None


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class GoogleAuthRequest(BaseModel):
    credential: str  # Google ID token


class TokenResponse(BaseModel):
    user_id: int
    email: str
    name: str
    token: str
    token_type: str = "bearer"


def _create_token_response(user: User) -> dict:
    """Create standardized token response"""
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "token": access_token,
        "token_type": "bearer"
    }


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Create new user
    user = User(
        email=request.email,
        name=request.name,
        password_hash=hash_password(request.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"New user registered: {user.email}")
    return _create_token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password"""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # For development: auto-register new users
        if settings.ENVIRONMENT == "development":
            user = User(
                email=request.email,
                name=request.name or request.email.split('@')[0],
                password_hash=hash_password(request.password)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Auto-registered new user: {user.email}")
        else:
            raise HTTPException(status_code=401, detail="Invalid email or password")
    else:
        # Verify password
        if user.password_hash:
            if not verify_password(request.password, user.password_hash):
                raise HTTPException(status_code=401, detail="Invalid email or password")
        else:
            # First login - set password
            user.password_hash = hash_password(request.password)
            db.add(user)
            db.commit()
            db.refresh(user)
    
    logger.info(f"User logged in: {user.email}")
    return _create_token_response(user)


@router.post("/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate with Google ID token"""
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests
        
        # Verify the Google ID token
        if not settings.GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")
        
        idinfo = id_token.verify_oauth2_token(
            request.credential, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        
        email = idinfo.get('email')
        name = idinfo.get('name', email.split('@')[0])
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")
        
        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                name=name,
                password_hash=None  # Google auth users don't need password
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"New Google user created: {email}")
        else:
            logger.info(f"Google user logged in: {email}")
        
        return _create_token_response(user)
    
    except ValueError as e:
        logger.error(f"Google auth failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid Google token")
    except ImportError:
        raise HTTPException(status_code=500, detail="Google auth libraries not installed")


# Re-export get_current_user from security module for backwards compatibility
from app.core.security import get_current_user

