from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Tạo Engine kết nối tới Supabase
engine = create_engine(settings.DATABASE_URL)

# Khởi tạo Session cho từng truy vấn độc lập
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Lớp Base chuẩn để các Model sau này kế thừa
Base = declarative_base()

# Hàm cung cấp kết nối (Dependency Injection) cho FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()