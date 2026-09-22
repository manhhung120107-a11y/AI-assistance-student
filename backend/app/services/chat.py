from sqlalchemy.orm import Session
from sqlalchemy import text
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from app.core.config import settings
from app.models.models import ChatHistory

# 1. Khởi tạo công cụ biến câu hỏi thành Vector (Phải khớp model với lúc Upload)
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2",
    google_api_key=settings.GEMINI_API_KEY
)

# 2. Khởi tạo não bộ tạo sinh (Gemini 1.5 Pro cho chất lượng cao)
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.2 # Nhiệt độ thấp ép AI bám sát fact, giảm thiểu ảo giác (hallucination)
)

def ask_document(session_id: str, question: str, document_id: str, db: Session):
    # 1. Nhúng câu hỏi thành vector
    question_vector = embeddings.embed_query(question)
    
    # 2. Truy quét tài liệu
    query = text("""
        SELECT content FROM document_chunks 
        WHERE document_id = :doc_id
        ORDER BY embedding <=> CAST(:q_vector AS vector) LIMIT 4
    """)
    results = db.execute(query, {"doc_id": document_id, "q_vector": str(question_vector)}).fetchall()
    context_text = "\n\n---\n\n".join([row[0] for row in results]) if results else "Không tìm thấy dữ liệu."
    
    # 3. Truy xuất lịch sử hội thoại (Rolling Window: Giữ 6 tin nhắn gần nhất = 3 lượt hỏi đáp)
    past_messages = db.query(ChatHistory).filter(
        ChatHistory.session_id == session_id
    ).order_by(ChatHistory.created_at.desc()).limit(6).all()
    
    # Đảo ngược mảng để trả lại đúng thứ tự thời gian từ cũ đến mới
    past_messages.reverse()
    history_text = "\n".join([f"{msg.role}: {msg.content}" for msg in past_messages])
    
    # 4. Kỹ thuật Prompt
    prompt = f"""
    Bạn là một trợ lý học tập AI. Trả lời dựa trên TÀI LIỆU THAM KHẢO. 
    Nếu cần, hãy xem xét LỊCH SỬ TRÒ CHUYỆN để hiểu ngữ cảnh câu hỏi mới.
    
    TÀI LIỆU THAM KHẢO:
    {context_text}
    
    LỊCH SỬ TRÒ CHUYỆN:
    {history_text}
    
    CÂU HỎI MỚI: {question}
    """
    
    response = llm.invoke(prompt)
    raw_answer = response.content
    
    if isinstance(raw_answer, list):
        answer = "".join([block.get("text", "") for block in raw_answer if isinstance(block, dict) and "text" in block])
    else:
        answer = str(raw_answer)
    
    # 5. Lưu vết cuộc hội thoại vào Database
    db.add(ChatHistory(session_id=session_id, role="user", content=question))
    db.add(ChatHistory(session_id=session_id, role="ai", content=answer))
    db.commit()
    
    return answer