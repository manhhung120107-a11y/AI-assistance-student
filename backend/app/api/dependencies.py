from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.core.config import settings

# Lấy cấu hình từ biến môi trường của bạn (hoặc bạn có thể điền chuỗi trực tiếp nếu đang test)
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # Nhờ lõi Supabase xác thực tính hợp lệ của Token
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")
        
        # Trả về ID của user để các hàm xử lý dữ liệu sử dụng
        return user_response.user.id
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập không hợp lệ.",
            headers={"WWW-Authenticate": "Bearer"},
        )