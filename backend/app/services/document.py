import tempfile
import requests
import pymupdf4llm
from sqlalchemy.orm import Session
from fastapi import HTTPException
from langchain_text_splitters import MarkdownTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings
from app.models.models import DocumentChunk

# Khởi tạo mô hình Embedding của Google
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2",
    task_type="RETRIEVAL_DOCUMENT",
    google_api_key=settings.GEMINI_API_KEY
)

def process_and_store_pdf(public_url: str, document_id: str, db: Session):
    try:
        # 1. Tải file từ Supabase về hệ thống cục bộ
        response = requests.get(public_url)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(response.content)
            temp_pdf_path = temp_file.name

        # 2. Ép kiểu PDF sang Markdown để bảo toàn Bảng biểu & Công thức Toán học
        md_text = pymupdf4llm.to_markdown(temp_pdf_path)

        # 3. Băm nhỏ văn bản theo cấu trúc ngữ nghĩa (Heading, Paragraph, Math Block)
        text_splitter = MarkdownTextSplitter(
            chunk_size=1000,
            chunk_overlap=200 
        )
        
        # Trích xuất danh sách chuỗi văn bản từ các Document objects
        doc_objects = text_splitter.create_documents([md_text])
        chunks = [doc.page_content for doc in doc_objects]

        if not chunks:
            return 0

        # 4. Biến đổi toàn bộ chữ thành Vector trong 1 lần gọi API duy nhất (Batching)
        vector_data_list = embeddings.embed_documents(chunks)
        
        # 5. Phân bổ dữ liệu vào PostgreSQL
        for chunk_text, vector_data in zip(chunks, vector_data_list):
            new_chunk = DocumentChunk(
                document_id=document_id,
                content=chunk_text,
                embedding=vector_data
            )
            db.add(new_chunk)
        
        db.commit()
        return len(chunks)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý AI: {str(e)}")