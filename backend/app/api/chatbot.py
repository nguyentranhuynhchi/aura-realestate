# backend/app/api/chatbot.py
from fastapi import APIRouter, HTTPException
from app.schemas import ChatRequest
from app.services.chatbot_service import chatbot_service

router = APIRouter()

# backend/app/api/chatbot.py

@router.post("/chat", summary="Chatbot tư vấn bất động sản kết hợp dữ liệu RAG")
async def chat(payload: ChatRequest):
    try:
        # Đổi thành tên hàm mới đã tích hợp kết nối ChromaDB
        reply = chatbot_service.ask_rag_bot(payload.message) 
        return {
            "success": True,
            "data": {
                "reply": reply
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))