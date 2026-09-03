// frontend/src/services/chatbotService.js
import api from './api';

// 1. Hàm lấy hoặc tự tạo session_id riêng cho từng máy
const getOrCreateSessionId = () => {
    let sessionId = localStorage.getItem('aura_chat_session_id');
    if (!sessionId) {
        sessionId = crypto.randomUUID();
        localStorage.setItem('aura_chat_session_id', sessionId);
    }
    return sessionId;
};

export const chatbotService = {
    /**
     * Gửi tin nhắn thông thường (Blocking)
     */
    sendMessage: async (message) => {
        try {
            const sessionId = getOrCreateSessionId();
            const response = await api.post('/api/v1/chat', { 
                message: message,
                session_id: sessionId 
            });
            if (response.data && response.data.success) {
                return response.data.data.reply;
            }
            throw new Error('Cấu trúc dữ liệu phản hồi không hợp lệ.');
        } catch (error) {
            console.error('Error in chatbotService.sendMessage:', error);
            const errorMessage = error.response?.data?.detail || error.message || 'Lỗi kết nối máy chủ.';
            throw new Error(errorMessage);
        }
    },

    /**
     * Gửi tin nhắn và nhận Stream SSE từng token theo thời gian thực (Real-time Streaming)
     * @param {string} message - Câu hỏi của người dùng
     * @param {function} onChunk - Hàm callback gọi mỗi khi có 1 token mới rơi xuống
     * @param {function} onFinish - Hàm callback gọi khi stream kết thúc hoàn tất
     * @param {function} onError - Hàm callback gọi khi xảy ra lỗi
     */
    sendMessageStream: async (message, onChunk, onFinish, onError) => {
        try {
            const sessionId = getOrCreateSessionId();
            const baseUrl = 'http://127.0.0.1:8000';

            const response = await fetch(`${baseUrl}/api/v1/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`Lỗi kết nối máy chủ: HTTP ${response.status}`);
            }

            const reader = response.body.getReader(); // 1. Cái vòi hút dữ liệu nhị phân
            const decoder = new TextDecoder('utf-8');// 2. Bộ thông dịch (Dịch byte thành chữ)
            let buffer = ''; // 3. Cái xô hứng tạm (Vùng đệm)

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Giữ lại phần chưa đủ 1 dòng hoàn chỉnh

                for (const line of lines) {
                    const trimmedLine = line.trim();
                    if (!trimmedLine || !trimmedLine.startsWith('data:')) continue;

                    const dataContent = trimmedLine.slice(5).trim();
                    if (dataContent === '[DONE]') {
                        if (onFinish) onFinish();
                        return;
                    }

                    try {
                        const parsed = JSON.parse(dataContent);
                        if (parsed.token && onChunk) {
                            onChunk(parsed.token);
                        } else if (parsed.error && onError) {
                            onError(new Error(parsed.error));
                        }
                    } catch (e) {
                        // Bỏ qua dòng json chưa parse được
                    }
                }
            }

            if (onFinish) onFinish();

        } catch (error) {
            console.error('Error in sendMessageStream:', error);
            if (onError) onError(error);
        }
    }
};