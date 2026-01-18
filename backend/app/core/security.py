"""Security utilities - JWT tokens and password hashing"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database import get_db
from app.models.schemas import User

security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    password_bytes = password.encode('utf-8')[:72]  # bcrypt limit
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        password_bytes = password.encode('utf-8')[:72]
        return bcrypt.checkpw(password_bytes, hashed.encode('utf-8'))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token"""
    token = credentials.credentials
    
    # Support both legacy tokens and JWT
    if token.startswith("user_"):
        # Legacy token format: user_{id}_{random}
        try:
            parts = token.split("_")
            user_id = int(parts[1])
        except (IndexError, ValueError):
            raise HTTPException(status_code=401, detail="Invalid token format")
    else:
        # JWT token
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        user_id = int(user_id)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
