from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.models.schemas import Base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./education.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
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
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = [col["name"] for col in inspector.get_columns("users")]
    if "password_hash" in columns:
        return

    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))
        conn.commit()
