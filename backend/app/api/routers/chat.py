from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.services.chat import ask_document

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    session_id: str # Thêm trường này
    document_id: str
    question: str

@router.post("/")
async def chat_with_doc(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        answer = ask_document(request.session_id, request.question, request.document_id, db)
        return {"session_id": request.session_id, "question": request.question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi truy vấn AI: {str(e)}")