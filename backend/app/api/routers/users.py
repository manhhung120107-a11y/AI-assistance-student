from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import UserCreate, UserResponse

# Khởi tạo Router, gom nhóm các API liên quan đến User
router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Bắt lỗi: Kiểm tra xem email đã tồn tại trong Supabase chưa
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký.")
    
    # Ánh xạ từ Schema (đầu vào) sang Model (CSDL)
    new_user = User(email=user.email)
    db.add(new_user)
    db.commit()          # Lưu thay đổi vật lý xuống DB
    db.refresh(new_user) # Cập nhật lại object để lấy UUID vừa được DB tạo tự động
    
    return new_user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
    return user