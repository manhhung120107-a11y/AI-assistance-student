from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.api.routers import documents
from app.api.routers import documents, chat, quiz

# 1. IMPORT THÊM ROUTER
from app.api.routers import users

app = FastAPI(title="AI Study Assistant API")

# Mở khóa CORS để Frontend React (thường chạy port 5173) có thể gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Khi deploy thật sẽ đổi thành URL cụ thể của Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. ĐĂNG KÝ ROUTER
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(quiz.router)

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Gửi một truy vấn giả để ép kết nối thực tế tới Supabase
        db.execute(text("SELECT 1"))
        return {"status": "success", "message": "Kết nối Supabase thành công!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kết nối CSDL: {str(e)}")