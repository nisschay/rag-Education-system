from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.schemas import Course, Unit, User, UploadedFile, ChatSession, Message
from app.core.security import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import hashlib
from app.services.document_processor import document_processor
from app.services.vector_store import vector_store
from app.utils.logging_config import get_logger

logger = get_logger("courses")
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

@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific course by ID"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return course

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
async def upload_documents(
    course_id: int,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    unit_id: Optional[int] = Form(None),
    topic_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload documents quickly; process text in background."""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    MAX_FILE_SIZE = 15 * 1024 * 1024
    MAX_FILES = 10
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.pptx'}

    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_FILES} files allowed")

    uploaded_files = []

    for file in files:
        ext = '.' + file.filename.lower().split('.')[-1]
        if ext not in ALLOWED_EXTENSIONS:
            logger.warning(f"Skipping unsupported file type: {file.filename}")
            continue

        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File {file.filename} exceeds size limit")
            continue

        try:
            extracted_text = await document_processor.extract_text_from_bytes(content, file.filename)
        except Exception as e:
            logger.error(f"Failed to extract text from {file.filename}: {e}")
            continue

        text_hash = hashlib.sha256(extracted_text.encode()).hexdigest()

        existing = db.query(UploadedFile).filter(
            UploadedFile.course_id == course_id,
            UploadedFile.text_hash == text_hash
        ).first()

        if existing:
            logger.info(f"Skipping duplicate document: {file.filename}")
            continue

        target_unit_id = await _get_or_create_unit(db, course_id, course.name, unit_id, topic_name)

        uploaded_file = UploadedFile(
            course_id=course_id,
            filename=file.filename,
            original_filename=file.filename,
            file_size=file_size,
            extracted_text=extracted_text,
            text_hash=text_hash,
            processing_status="pending",
            chunks_count=0
        )
        db.add(uploaded_file)
        db.flush()

        background_tasks.add_task(
            process_document_background,
            uploaded_file.id,
            course_id,
            target_unit_id,
            course.name
        )

        uploaded_files.append({
            "id": uploaded_file.id,
            "filename": file.filename,
            "size": file_size,
            "status": "processing",
            "text_length": len(extracted_text)
        })

    db.commit()

    return {
        "message": f"Uploaded {len(uploaded_files)} document(s), processing in background",
        "files": uploaded_files,
        "processing": True
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


@router.get("/{course_id}/documents")
async def get_course_documents(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all documents uploaded to a course"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    files = db.query(UploadedFile).filter(UploadedFile.course_id == course_id).all()
    
    return {
        "course_id": course_id,
        "documents": [
            {
                "id": f.id,
                "filename": f.original_filename,
                "file_size": f.file_size,
                "chunks_count": f.chunks_count,
                "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
            }
            for f in files
        ]
    }

async def _get_or_create_unit(
    db: Session,
    course_id: int,
    course_name: str,
    unit_id: Optional[int],
    topic_name: Optional[str]
) -> int:
    """Resolve target unit for upload, creating topic unit if needed."""
    if unit_id:
        return unit_id

    if topic_name:
        existing_unit = db.query(Unit).filter(
            Unit.course_id == course_id,
            Unit.name == topic_name
        ).first()
        if not existing_unit:
            next_order = db.query(Unit).filter(Unit.course_id == course_id).count()
            existing_unit = Unit(
                course_id=course_id,
                name=topic_name,
                order=next_order,
                level=1
            )
            db.add(existing_unit)
            db.commit()
            db.refresh(existing_unit)
        return existing_unit.id

    default_unit = db.query(Unit).filter(
        Unit.course_id == course_id,
        Unit.level == 0
    ).first()

    if not default_unit:
        default_unit = Unit(
            course_id=course_id,
            name=f"{course_name} - Main",
            order=0,
            level=0
        )
        db.add(default_unit)
        db.commit()
        db.refresh(default_unit)

    return default_unit.id


async def process_document_background(
    file_id: int,
    course_id: int,
    unit_id: int,
    course_name: str
):
    """Background task: chunk + embed extracted text."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not file:
            return

        file.processing_status = "processing"
        db.commit()

        chunks = document_processor.create_semantic_chunks(
            file.extracted_text or "",
            {
                "unit_id": unit_id,
                "unit_name": course_name,
                "source": file.filename,
                "file_id": file_id
            }
        )

        documents = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        ids = [f"course_{course_id}_file_{file_id}_chunk_{i}" for i in range(len(chunks))]

        await vector_store.add_documents_batched(
            course_id=course_id,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        file.processing_status = "completed"
        file.chunks_count = len(chunks)
        db.commit()

    except Exception as e:
        logger.error(f"Background processing failed for file {file_id}: {e}")
        file.processing_status = "failed"
        db.commit()
    finally:
        db.close()


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a course and all its data"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    logger.info(f"Deleting course {course_id}: {course.name}")
    
    try:
        # Delete from vector store
        vector_store.delete_collection(course_id)
        
        # Delete uploaded files from disk
        files = db.query(UploadedFile).filter(UploadedFile.course_id == course_id).all()
        for f in files:
            if f.file_path and os.path.exists(f.file_path):
                os.remove(f.file_path)
        
        # Delete chat sessions and messages
        sessions = db.query(ChatSession).filter(ChatSession.course_id == course_id).all()
        for session in sessions:
            db.query(Message).filter(Message.session_id == session.id).delete()
        db.query(ChatSession).filter(ChatSession.course_id == course_id).delete()
        
        # Delete uploaded files records
        db.query(UploadedFile).filter(UploadedFile.course_id == course_id).delete()
        
        # Delete units
        db.query(Unit).filter(Unit.course_id == course_id).delete()
        
        # Delete course
        db.delete(course)
        db.commit()
        
        logger.info(f"Successfully deleted course {course_id}")
        return {"message": "Course deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting course {course_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting course: {str(e)}")


@router.delete("/{course_id}/documents/{document_id}")
async def delete_document(
    course_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific document from a course"""
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    file = db.query(UploadedFile).filter(
        UploadedFile.id == document_id,
        UploadedFile.course_id == course_id
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Delete file from disk
        if file.file_path and os.path.exists(file.file_path):
            os.remove(file.file_path)
        
        # Delete record
        db.delete(file)
        db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")
