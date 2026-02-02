from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.schemas import UploadedFile, User, Course
from app.api.auth import get_current_user
from app.utils.logging_config import get_logger

logger = get_logger("processing_status")
router = APIRouter(prefix="/api/processing", tags=["processing"])


@router.get("/{course_id}/status")
async def get_processing_status(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get processing status for all documents in a course.
    Frontend can poll this endpoint to track background processing.
    """
    # Verify user owns this course
    course = db.query(Course).filter(
        Course.id == course_id,
        Course.user_id == current_user.id
    ).first()
    
    if not course:
        return {"error": "Course not found", "files": [], "all_completed": True}
    
    files = db.query(UploadedFile).filter(
        UploadedFile.course_id == course_id
    ).order_by(UploadedFile.uploaded_at.desc()).all()
    
    return {
        "course_id": course_id,
        "files": [
            {
                "id": f.id,
                "filename": f.filename,
                "status": f.processing_status or "completed",
                "chunks_count": f.chunks_count or 0,
                "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None
            }
            for f in files
        ],
        "all_completed": all(
            (f.processing_status or "completed") == "completed" 
            for f in files
        ),
        "pending_count": sum(
            1 for f in files 
            if (f.processing_status or "completed") in ["pending", "processing"]
        )
    }


@router.get("/{course_id}/file/{file_id}/status")
async def get_file_status(
    course_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get processing status for a specific file."""
    file = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.course_id == course_id
    ).first()
    
    if not file:
        return {"error": "File not found"}
    
    return {
        "id": file.id,
        "filename": file.filename,
        "status": file.processing_status or "completed",
        "chunks_count": file.chunks_count or 0,
        "file_size": file.file_size,
        "text_length": len(file.extracted_text) if file.extracted_text else 0
    }
