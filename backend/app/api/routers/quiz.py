from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Document
from app.services.quiz import generate_quiz, generate_flashcards
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/quiz", tags=["Quiz"])

# Hàm nội bộ để xác minh quyền sở hữu tài liệu
def verify_document_ownership(document_id: str, user_id: str, db: Session):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
    if str(doc.user_id) != user_id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thao tác trên tài liệu này.")

@router.post("/generate")
async def create_quiz(
    document_id: str, 
    topic: str = "Tổng hợp", 
    num_questions: int = 5, 
    db: Session = Depends(get_db), 
    current_user_id: str = Depends(get_current_user)
):
    verify_document_ownership(document_id, current_user_id, db)
    try:
        return generate_quiz(document_id, topic, num_questions, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo Quiz: {str(e)}")

@router.post("/flashcards")
async def create_flashcards(
    document_id: str, 
    topic: str = "Khái niệm quan trọng", 
    num_cards: int = 5, 
    db: Session = Depends(get_db), 
    current_user_id: str = Depends(get_current_user)
):
    verify_document_ownership(document_id, current_user_id, db)
    try:
        return generate_flashcards(document_id, topic, num_cards, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo Flashcard: {str(e)}")