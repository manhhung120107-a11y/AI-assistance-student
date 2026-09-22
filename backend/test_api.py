import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Các mô hình hỗ trợ Embedding trên API Key này:")
for m in genai.list_models():
    if "embedContent" in m.supported_generation_methods:
        print("-", m.name)