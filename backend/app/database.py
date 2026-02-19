from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.models.schemas import Base
import os

# Get DATABASE_URL from environment (Render sets this directly)
# Don't use load_dotenv() in production - it can cause issues
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./education.db")

# Handle Render's postgres:// vs postgresql:// URL format
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"
    },
    pool_pre_ping=True,  # Helps with connection reliability
    pool_recycle=300,    # Recycle connections every 5 minutes
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_user_password_column()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_user_password_column():
    """Add password_hash to users table if missing (for existing DBs)."""
    try:
        inspector = inspect(engine)
        if "users" not in inspector.get_table_names():
            return
        columns = [col["name"] for col in inspector.get_columns("users")]
        if "password_hash" in columns:
            return

        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))
            conn.commit()
    except Exception as e:
        print(f"Warning: Could not ensure password column: {e}")
