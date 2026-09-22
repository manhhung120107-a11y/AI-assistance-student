import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from supabase import create_client, Client

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Document, User
from app.schemas.schemas import DocumentResponse
from app.services.document import process_and_store_pdf
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/documents", tags=["Documents"])

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user) # Nguồn định danh duy nhất và tuyệt đối
):
    # 1. Chặn file rác
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Hệ thống chỉ hỗ trợ xử lý file PDF.")
        
    # 2. Xác thực User bằng ID trích xuất từ Token JWT
    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin người dùng trong cơ sở dữ liệu.")

    # 3. Tạo ID file vật lý
    safe_filename = f"{current_user_id}/{uuid.uuid4()}.pdf"
    
    # 4. Tải lên Supabase Storage
    try:
        file_bytes = await file.read()
        supabase.storage.from_("documents").upload(
            path=safe_filename,
            file=file_bytes,
            file_options={"content-type": "application/pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi máy chủ lưu trữ: {str(e)}")

    # 5. Lấy link public và lưu Database
    public_url = supabase.storage.from_("documents").get_public_url(safe_filename)

    new_doc = Document(
        user_id=current_user_id,
        title=file.filename,
        file_url=public_url
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # 6. Kích hoạt RAG Engine
    process_and_store_pdf(public_url=public_url, document_id=str(new_doc.id), db=db)

    return new_doc

@router.get("/user/{user_id}", response_model=list[DocumentResponse])
async def get_user_documents(user_id: str, db: Session = Depends(get_db), current_user_id: str = Depends(get_current_user)):
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Không có quyền truy cập tài liệu của người khác")
    docs = db.query(Document).filter(Document.user_id == user_id).order_by(Document.created_at.desc()).all()
    return docs