# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import predict
from app.api import predict, chatbot

app = FastAPI(
    title="AI Prediction & RAG Chatbot API",
    description="Backend service phục vụ dự đoán và chatbot tư vấn",
    version="1.0.0"
)

# Cấu hình CORS để Frontend (ví dụ chạy ở port 3000) có thể gọi API mà không bị chặn bảo mật
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Trong thực tế deploy nên giới hạn domain cụ thể thay vì "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các router (endpoints)
app.include_router(predict.router, prefix="/api/v1", tags=["Prediction"])
app.include_router(chatbot.router, prefix="/api/v1", tags=["Chatbot"]) 

@app.get("/", tags=["Health Check"])
async def root():
    return {"message": "Backend đang hoạt động bình thường!", "status": "healthy"}