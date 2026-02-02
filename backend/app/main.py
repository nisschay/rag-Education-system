from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.api import auth, courses, chat, processing_status
from app.database import init_db
from app.core.config import settings
from app.utils.logging_config import get_logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
import os

logger = get_logger("main")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} API...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    init_db()
    logger.info("Database initialized (PostgreSQL)")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME} API...")

app = FastAPI(
    title=settings.PROJECT_NAME, 
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration - Allow all origins in production for now
origins = [
    "https://rag-education-system.vercel.app",
    "https://rag-education-system-1.onrender.com",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000",
]

# Also check environment variable
cors_origins_env = os.environ.get("CORS_ORIGINS_STR", "")
if cors_origins_env:
    origins.extend([o.strip() for o in cors_origins_env.split(",") if o.strip()])

# Remove duplicates
origins = list(set(origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include routers
app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(chat.router)
app.include_router(processing_status.router)

@app.get("/")
def read_root():
    return {"message": f"{settings.PROJECT_NAME} API", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
