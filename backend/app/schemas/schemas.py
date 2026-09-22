from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# --- USER SCHEMAS ---
class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    pass # Nếu tự làm Auth, sẽ thêm password vào đây. Vì dùng Supabase Auth, email là đủ.

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- DOCUMENT SCHEMAS ---
class DocumentBase(BaseModel):
    title: str
    file_url: Optional[str] = None

class DocumentCreate(DocumentBase):
    user_id: UUID

class DocumentResponse(DocumentBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- CHAT SCHEMAS ---
class ChatMessageBase(BaseModel):
    role: str
    content: str

class ChatMessageCreate(ChatMessageBase):
    session_id: UUID

class ChatMessageResponse(ChatMessageBase):
    id: UUID
    session_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ChatSessionCreate(BaseModel):
    user_id: UUID
    document_id: UUID

class ChatSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    document_id: UUID
    created_at: datetime
    messages: List[ChatMessageResponse] = [] # Tự động lồng lịch sử tin nhắn vào phiên chat
    
    model_config = ConfigDict(from_attributes=True)

class QuizOption(BaseModel):
    text: str
    is_correct: bool

class QuizQuestion(BaseModel):
    question: str
    options: List[QuizOption]
    explanation: str

class QuizResponse(BaseModel):
    questions: List[QuizQuestion]

class Flashcard(BaseModel):
    front: str # Thuật ngữ hoặc Câu hỏi ngắn
    back: str  # Định nghĩa hoặc Câu trả lời cốt lõi

class FlashcardResponse(BaseModel):
    cards: List[Flashcard]