import re
import json
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.services.chat import llm
from app.services.document import embeddings # Tận dụng chung cấu hình embeddings

def generate_quiz(document_id: str, topic: str, num_questions: int, db: Session):
    # 1. Chuyển đổi topic thành vector để quét chính xác đoạn tài liệu liên quan nhất
    topic_vector = embeddings.embed_query(topic)
    
    query = text("""
        SELECT content FROM document_chunks 
        WHERE document_id = :doc_id
        ORDER BY embedding <=> CAST(:q_vector AS vector) LIMIT 5
    """)
    results = db.execute(query, {"doc_id": document_id, "q_vector": str(topic_vector)}).fetchall()
    context = "\n\n".join([row[0] for row in results]) if results else "Không tìm thấy dữ liệu phù hợp."

    prompt = f"""
    Dựa vào TÀI LIỆU sau, hãy tạo {num_questions} câu hỏi trắc nghiệm học thuật về chủ đề "{topic}".
    YÊU CẦU TỐI THƯỢNG: Chỉ trả về duy nhất chuỗi JSON thuần túy theo đúng cấu trúc sau, không dùng markdown block (```json), không giải thích:
    {{
        "questions": [
            {{
                "question": "Nội dung câu hỏi...",
                "options": [
                    {{"text": "Lựa chọn 1", "is_correct": true}},
                    {{"text": "Lựa chọn 2", "is_correct": false}}
                ],
                "explanation": "Giải thích chi tiết vì sao đúng..."
            }}
        ]
    }}
    
    TÀI LIỆU:
    {context}
    """
    
    response = llm.invoke(prompt)
    raw_content = response.content
    
    # 2. Xử lý an toàn định dạng trả về từ Gemini (phòng hờ trường hợp trả về list hoặc string)
    if isinstance(raw_content, list):
        raw_text = "".join([block.get("text", "") for block in raw_content if isinstance(block, dict) and "text" in block])
    else:
        raw_text = str(raw_content)
        
    # 3. Làm sạch chuỗi JSON
    cleaned_text = raw_text.strip().replace("```json", "").replace("```", "")
    
    return json.loads(cleaned_text)

def generate_flashcards(document_id: str, topic: str, num_cards: int, db: Session):
    # Quét tài liệu bằng vector tương tự như Quiz
    topic_vector = embeddings.embed_query(topic)
    
    query = text("""
        SELECT content FROM document_chunks 
        WHERE document_id = :doc_id
        ORDER BY embedding <=> CAST(:q_vector AS vector) LIMIT 5
    """)
    results = db.execute(query, {"doc_id": document_id, "q_vector": str(topic_vector)}).fetchall()
    context = "\n\n".join([row[0] for row in results]) if results else "Không tìm thấy dữ liệu."

    prompt = f"""
    Dựa vào TÀI LIỆU sau, hãy trích xuất {num_cards} cặp thẻ ghi nhớ (Flashcard) quan trọng nhất về chủ đề "{topic}".
    YÊU CẦU: Chỉ trả về duy nhất chuỗi JSON thuần túy, không dùng markdown, không giải thích.
    Mặt trước (front) là thuật ngữ/khái niệm ngắn gọn. Mặt sau (back) là định nghĩa/giải thích cốt lõi dễ nhớ.
    {{
        "cards": [
            {{
                "front": "Tên thuật ngữ",
                "back": "Định nghĩa chi tiết"
            }}
        ]
    }}
    
    TÀI LIỆU:
    {context}
    """
    
    response = llm.invoke(prompt)
    raw_content = response.content
    
    if isinstance(raw_content, list):
        raw_text = "".join([block.get("text", "") for block in raw_content if isinstance(block, dict) and "text" in block])
    else:
        raw_text = str(raw_content)
        
    # Sử dụng Regex để khoanh vùng khối JSON
    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    if not match:
        raise ValueError("AI không sinh ra cấu trúc JSON hợp lệ.")
        
    cleaned_text = match.group(0)
    
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        # Trả về chuỗi thô để dễ dàng debug nếu JSON vẫn hỏng
        raise ValueError(f"Lỗi giải mã cấu trúc: {str(e)} - Data thô: {cleaned_text[:150]}...")