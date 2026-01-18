from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    password_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    courses = relationship("Course", back_populates="user")
    sessions = relationship("ChatSession", back_populates="user")

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="courses")
    units = relationship("Unit", back_populates="course")
    sessions = relationship("ChatSession", back_populates="course")

class Unit(Base):
    __tablename__ = "units"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    parent_unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    name = Column(String)
    order = Column(Integer)
    level = Column(Integer)
    summary = Column(Text, nullable=True)
    
    course = relationship("Course", back_populates="units")
    parent = relationship("Unit", remote_side=[id], backref="children")
    documents = relationship("Document", back_populates="unit")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"))
    content = Column(Text)
    chunk_type = Column(String)
    doc_metadata = Column(JSON)  # Renamed from 'metadata' to avoid conflict
    vector_id = Column(String)
    
    unit = relationship("Unit", back_populates="documents")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    current_unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    teaching_mode = Column(String, default="qa")
    context = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="sessions")
    course = relationship("Course", back_populates="sessions")
    messages = relationship("Message", back_populates="session")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)
    msg_metadata = Column(JSON)  # Renamed from 'metadata' to avoid conflict
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="messages")

class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    filename = Column(String)
    original_filename = Column(String)
    file_size = Column(Integer)  # Size in bytes
    file_path = Column(String)
    chunks_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    course = relationship("Course", backref="uploaded_files")
