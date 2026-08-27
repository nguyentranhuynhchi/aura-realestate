# backend/app/api/chatbot.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.schemas import ChatRequest
from app.services.chatbot_service import chatbot_service

router = APIRouter()

def post_chat_background_worker(session_id: str, user_msg: str, bot_reply: str):
    """Tác vụ chạy ngầm sau khi đã trả kết quả về cho người dùng:
    1. Lưu 2 tin nhắn mới (User & Bot) vào chat_history
    2. Kiểm tra nếu tổng số tin >= 5 thì nén 2 tin cũ nhất vào chat_summaries
    """
    chatbot_service.save_message(session_id, "human", user_msg)
    chatbot_service.save_message(session_id, "ai", bot_reply)
    chatbot_service.compress_memory_if_needed(session_id)

@router.post("/chat", summary="Chatbot tư vấn bất động sản kết hợp dữ liệu RAG")
async def chat(payload: ChatRequest, background_tasks: BackgroundTasks):
    try:
        # 1. Sinh câu trả lời ngay lập tức (không chờ lưu DB hay nén)
        reply = chatbot_service.ask_rag_bot(
            user_message=payload.message,
            session_id=payload.session_id  
        ) 

        # 2. Đẩy tác vụ lưu DB và nén xuống Background Tasks
        background_tasks.add_task(
            post_chat_background_worker, 
            payload.session_id, 
            payload.message, 
            reply
        )

        # 3. Bắn kết quả phản hồi về cho Frontend ngay
        return {
            "success": True,
            "data": {
                "reply": reply
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))