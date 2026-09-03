# backend/app/api/chatbot.py
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
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

@router.post("/chat", summary="Chatbot tư vấn bất động sản kết hợp dữ liệu RAG (Blocking)")
async def chat(payload: ChatRequest, background_tasks: BackgroundTasks):
    try:
        reply = await run_in_threadpool(
            chatbot_service.ask_rag_bot,
            user_message=payload.message,
            session_id=payload.session_id
        )

        background_tasks.add_task(
            post_chat_background_worker, 
            payload.session_id, 
            payload.message, 
            reply
        )

        return {
            "success": True,
            "data": {
                "reply": reply
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream", summary="Chatbot tư vấn bất động sản Streaming SSE (Real-time)")
async def chat_stream(payload: ChatRequest, background_tasks: BackgroundTasks):
    """Endpoint Server-Sent Events (SSE) bắn từng token về giao diện theo thời gian thực"""
    async def event_generator():
        full_reply = []
        try:
            async for token in chatbot_service.astream_rag_bot(
                user_message=payload.message,
                session_id=payload.session_id
            ):
                full_reply.append(token)
                # Đóng gói theo chuẩn Server-Sent Events (SSE format: data: {...}\n\n)
                payload_json = json.dumps({"token": token}, ensure_ascii=False)
                yield f"data: {payload_json}\n\n"
            
            # Kết thúc stream: Gửi tín hiệu [DONE]
            yield "data: [DONE]\n\n"

            # Lưu lại câu trả lời hoàn chỉnh vào database và nén memory ngầm
            complete_reply_text = "".join(full_reply)
            background_tasks.add_task(
                post_chat_background_worker,
                payload.session_id,
                payload.message,
                complete_reply_text
            )
        except Exception as e:
            err_json = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {err_json}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")