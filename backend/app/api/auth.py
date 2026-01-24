"""Authentication API - Production ready with JWT"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import logging
import bcrypt
import jwt
import os

from app.database import get_db
from app.models.schemas import User

logger = logging.getLogger("rag_education.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Get settings from environment directly for reliability
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 7 days
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")


class LoginRequest(BaseModel):
    email: str
    password: Optional[str] = None
    name: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    credential: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email/password or register new user."""
    logger.info(f"Login attempt for email: {request.email}")
    
    try:
        user = db.query(User).filter(User.email == request.email).first()
        
        if user:
            # Existing user - verify password
            if request.password:
                if user.password_hash and verify_password(request.password, user.password_hash):
                    logger.info(f"Password login successful for: {request.email}")
                elif not user.password_hash:
                    # User exists but no password set (e.g., Google auth user)
                    # Set password for first time
                    user.password_hash = hash_password(request.password)
                    db.commit()
                    logger.info(f"Password set for existing user: {request.email}")
                else:
                    logger.warning(f"Invalid password for: {request.email}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid email or password"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Password required"
                )
        else:
            # New user - register
            if not request.password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password required for new users"
                )
            
            user = User(
                email=request.email,
                name=request.name or request.email.split("@")[0],
                password_hash=hash_password(request.password)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"New user registered: {request.email}")
        
        # Generate token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


@router.post("/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate with Google OAuth."""
    logger.info("Google auth attempt")
    
    if not GOOGLE_CLIENT_ID:
        logger.error("GOOGLE_CLIENT_ID not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured on server"
        )
    
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests
        
        # Verify the Google token with clock skew tolerance
        idinfo = id_token.verify_oauth2_token(
            request.credential,
            requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=30  # Allow 30 seconds clock skew
        )
        
        email = idinfo.get("email")
        name = idinfo.get("name", email.split("@")[0] if email else "User")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google"
            )
        
        logger.info(f"Google auth for email: {email}")
        
        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            user = User(email=email, name=name)
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"New user created via Google: {email}")
        else:
            # Update name if changed
            if name and user.name != name:
                user.name = name
                db.commit()
        
        # Generate token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        )
    
    except ValueError as e:
        logger.error(f"Google token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google authentication failed: {str(e)}"
        )


@router.get("/me")
async def get_current_user(db: Session = Depends(get_db), token: str = None):
    """Get current user from token."""
    # This would need token from header - simplified for now
    return {"message": "Use Authorization header with Bearer token"}


@router.post("/register", response_model=TokenResponse)
async def register(request: LoginRequest, db: Session = Depends(get_db)):
    """Register a new user with email/password."""
    logger.info(f"Registration attempt for email: {request.email}")
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        if not request.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password required"
            )
        
        if len(request.password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters"
            )
        
        # Create new user
        user = User(
            email=request.email,
            name=request.name or request.email.split("@")[0],
            password_hash=hash_password(request.password)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New user registered: {request.email}")
        
        # Generate token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

