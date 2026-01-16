from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.schemas import Course, Unit, User
from app.api.auth import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import aiofiles
import os
from app.services.document_processor import document_processor
from app.services.vector_store import vector_store

router = APIRouter(prefix="/api/courses", tags=["courses"])

class CourseCreate(BaseModel):
    name: str
    description: str = ""

class UnitCreate(BaseModel):
    name: str
    parent_unit_id: Optional[int] = None
    order: int
    level: int

class CourseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/", response_model=CourseResponse)
async def create_course(
    course: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new course"""
    new_course = Course(
        user_id=current_user.id,
        name=course.name,
        description=course.description
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    
    return new_course

@router.get("/", response_model=List[CourseResponse])
async def get_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all courses for current user"""
    courses = db.query(Course).filter(Course.user_id == current_user.id).all()
    return courses

@router.post("/{course_id}/units")
async def create_unit(
    course_id: int,
    unit: UnitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a unit in a course"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    new_unit = Unit(
        course_id=course_id,
        parent_unit_id=unit.parent_unit_id,
        name=unit.name,
        order=unit.order,
        level=unit.level
    )
    db.add(new_unit)
    db.commit()
    db.refresh(new_unit)
    
    return new_unit

@router.post("/{course_id}/upload")
async def upload_document(
    course_id: int,
    file: UploadFile = File(...),
    unit_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a PDF document to a course"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Save file
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{course_id}_{file.filename}")
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Extract text
    text = await document_processor.extract_text_from_pdf(file_path)
    
    # Get or create default unit
    if not unit_id:
        default_unit = db.query(Unit).filter(
            Unit.course_id == course_id,
            Unit.level == 0
        ).first()
        
        if not default_unit:
            default_unit = Unit(
                course_id=course_id,
                name=f"{course.name} - Main",
                order=0,
                level=0
            )
            db.add(default_unit)
            db.commit()
            db.refresh(default_unit)
        
        unit_id = default_unit.id
    
    # Create hierarchical chunks
    chunks = await document_processor.create_hierarchical_chunks(
        text=text,
        unit_id=unit_id,
        unit_name=course.name
    )
    
    # Add to vector store
    documents = [chunk["content"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    ids = [f"course_{course_id}_chunk_{i}" for i in range(len(chunks))]
    
    await vector_store.add_documents(
        course_id=course_id,
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    
    return {
        "message": "Document uploaded and processed",
        "chunks_created": len(chunks),
        "file_path": file_path
    }

@router.get("/{course_id}/structure")
async def get_course_structure(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get hierarchical structure of course units"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Get all units
    units = db.query(Unit).filter(Unit.course_id == course_id).order_by(Unit.order).all()
    
    # Build tree structure
    def build_tree(parent_id=None):
        children = [u for u in units if u.parent_unit_id == parent_id]
        result = []
        for child in children:
            result.append({
                "id": child.id,
                "name": child.name,
                "level": child.level,
                "order": child.order,
                "children": build_tree(child.id)
            })
        return result
    
    tree = build_tree(None)
    
    return {
        "course_id": course_id,
        "course_name": course.name,
        "units": tree
    }
