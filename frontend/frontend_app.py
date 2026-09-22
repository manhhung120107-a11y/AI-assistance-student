import streamlit as st
import requests
import uuid
from supabase import create_client, Client

# BẮT BUỘC NẰM Ở ĐÂY: Khởi tạo trang trước bất kỳ lệnh UI nào khác
st.set_page_config(page_title="AI Study Assistant", layout="wide")

API_URL = "https://ai-assistance-backend-j0no.onrender.com"
SUPABASE_URL = "https://zmhdrmcpyjxmdvljvsiq.supabase.co"
SUPABASE_KEY = "sb_publishable_H_mQDQpI_Ma_cuMFV-g8Bw_iu5KXI9w"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Gom gọn khởi tạo state vào 1 khối duy nhất
if "user" not in st.session_state:
    st.session_state.user = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "document_id" not in st.session_state:
    st.session_state.document_id = None

# MÀN HÌNH XÁC THỰC
if not st.session_state.user:
    st.title("🔐 Xác thực hệ thống")
    tab_login, tab_register = st.tabs(["Đăng nhập", "Đăng ký mới"])
    
    with tab_login:
        email_login = st.text_input("Email", key="login_email")
        pass_login = st.text_input("Mật khẩu", type="password", key="login_pass")
        if st.button("Đăng nhập", type="primary"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email_login, "password": pass_login})
                st.session_state.user = res.user
                st.session_state.access_token = res.session.access_token
                st.rerun()
            except Exception as e:
                st.error("Sai tài khoản hoặc mật khẩu.")
                
    with tab_register:
        email_reg = st.text_input("Email", key="reg_email")
        pass_reg = st.text_input("Mật khẩu", type="password", key="reg_pass")
        if st.button("Đăng ký"):
            try:
                supabase.auth.sign_up({"email": email_reg, "password": pass_reg})
                st.success("Tạo tài khoản thành công! Hãy quay lại tab Đăng nhập.")
            except Exception as e:
                st.error(f"Lỗi hệ thống: {str(e)}")
    st.stop()

# ĐÃ XÁC THỰC: Tạo Headers chứa Token dùng chung cho mọi API
headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

st.title("📚 Trợ lý học tập AI")

# Sidebar: Nạp tri thức
with st.sidebar:
    st.header("👤 Bảng điều khiển")
    st.write(f"Tài khoản: {st.session_state.user.email}")
    if st.button("Đăng xuất"):
        supabase.auth.sign_out()
        st.session_state.user = None
        st.session_state.access_token = None
        st.rerun()
        
    st.divider()
    
    st.header("1. Kho tài liệu của bạn")
    # Đã kẹp Token vào Request
    res = requests.get(f"{API_URL}/documents/user/{st.session_state.user.id}", headers=headers)
    if res.status_code == 200 and res.json():
        docs = res.json()
        doc_dict = {doc["title"]: doc["id"] for doc in docs}
        
        selected_doc_title = st.selectbox("Chọn tài liệu để học:", list(doc_dict.keys()))
        if selected_doc_title:
            st.session_state.document_id = doc_dict[selected_doc_title]
    else:
        st.info("Kho lưu trữ trống.")

    st.divider()
    
    st.header("2. Tải lên tài liệu mới")
    uploaded_file = st.file_uploader("Chọn file PDF", type=["pdf"])
    
    if st.button("Vector hóa dữ liệu") and uploaded_file:
        with st.spinner("Đang xử lý toán học & nhúng vector..."):
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            payload = {"user_id": st.session_state.user.id} 
            
            # Đã kẹp Token vào Request Upload
            upload_res = requests.post(f"{API_URL}/documents/upload", files=files, data=payload, headers=headers)
            
            if upload_res.status_code == 201:
                st.session_state.document_id = upload_res.json().get("id")
                st.success("Đồng bộ thành công!")
                st.rerun()
            else:
                st.error(f"Lỗi: {upload_res.text}")

# Không gian chính
tab_chat, tab_quiz, tab_flashcard = st.tabs(["💬 Trợ giảng AI", "📝 Trắc nghiệm", "🗂️ Flashcard"])

with tab_chat:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Nhập câu hỏi thảo luận..."):
        if not st.session_state.document_id:
            st.warning("Vui lòng tải lên tài liệu trước.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("ai"):
                with st.spinner("Đang quét pgvector..."):
                    payload = {
                        "session_id": st.session_state.session_id,
                        "document_id": st.session_state.document_id,
                        "question": prompt
                    }
                    # Đã kẹp Token
                    res = requests.post(f"{API_URL}/chat/", json=payload, headers=headers)
                    
                    if res.status_code == 200:
                        answer = res.json()["answer"]
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "ai", "content": answer})
                    else:
                        st.error("RAG Engine không phản hồi hoặc bạn chưa có quyền.")

with tab_quiz:
    col1, col2 = st.columns([3, 1])
    with col1:
        quiz_topic = st.text_input("Chủ đề trọng tâm:", value="Tổng hợp", key="q_topic")
    with col2:
        quiz_num = st.number_input("Số câu hỏi:", min_value=1, max_value=10, value=3)
        
    if st.button("Sinh bài tập"):
        if not st.session_state.document_id:
            st.warning("Cần nạp tài liệu trước.")
        else:
            with st.spinner("Đang sinh cấu trúc JSON..."):
                # Đã kẹp Token
                res = requests.post(f"{API_URL}/quiz/generate?document_id={st.session_state.document_id}&topic={quiz_topic}&num_questions={quiz_num}", headers=headers)
                if res.status_code == 200:
                    st.session_state.quiz_data = res.json().get("questions", [])
                else:
                    st.error("Lỗi sinh câu hỏi.")

    if "quiz_data" in st.session_state:
        with st.form("quiz_form"):
            for idx, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**Câu {idx + 1}: {q['question']}")
                options = [opt["text"] for opt in q["options"]]
                st.radio("Chọn đáp án:", options, key=f"ans_{idx}")
                st.divider()
                
            if st.form_submit_button("Nộp bài"):
                for idx, q in enumerate(st.session_state.quiz_data):
                    correct_opt = next(opt for opt in q["options"] if opt["is_correct"])
                    user_choice = st.session_state[f"ans_{idx}"]
                    if user_choice == correct_opt["text"]:
                        st.success(f"Câu {idx + 1}: Chính xác!")
                    else:
                        st.error(f"Câu {idx + 1}: Sai. Đáp án đúng là: {correct_opt['text']}")
                    st.info(f"Giải thích: {q['explanation']}")

with tab_flashcard:
    col3, col4 = st.columns([3, 1])
    with col3:
        fc_topic = st.text_input("Chủ đề thẻ:", value="Thuật ngữ lõi", key="f_topic")
    with col4:
        fc_num = st.number_input("Số lượng thẻ:", min_value=1, max_value=20, value=5)
        
    if st.button("Tạo bộ Flashcard"):
        if not st.session_state.document_id:
            st.warning("Cần nạp tài liệu trước.")
        else:
            with st.spinner("Đang trích xuất thuật ngữ..."):
                # Gom tham số vào dictionary để requests tự động mã hóa URL (URL Encoding)
                req_params = {
                    "document_id": st.session_state.document_id,
                    "topic": fc_topic,
                    "num_cards": fc_num
                }
                res = requests.post(
                    f"{API_URL}/quiz/flashcards", 
                    params=req_params, 
                    headers=headers
                )
                
                if res.status_code == 200:
                    st.session_state.fc_data = res.json().get("cards", [])
                else:
                    st.error(f"Chi tiết lỗi: {res.text}")

    if "fc_data" in st.session_state:
        for idx, card in enumerate(st.session_state.fc_data):
            # Vá lỗi hiển thị bằng cách gọi đúng biến 'front'
            with st.expander(f"🎴 Thẻ {idx + 1}: **"):
                st.write(card['back'])