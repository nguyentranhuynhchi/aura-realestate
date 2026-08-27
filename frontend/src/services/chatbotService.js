// frontend/src/services/chatbotService.js
import api from './api';

// 1. Hàm lấy hoặc tự tạo session_id riêng cho từng máy (lưu vĩnh viễn trên trình duyệt máy đó)
const getOrCreateSessionId = () => {
    let sessionId = localStorage.getItem('aura_chat_session_id');
    if (!sessionId) {
        sessionId = crypto.randomUUID(); // Tự sinh mã UUID ngẫu nhiên không bao giờ trùng
        localStorage.setItem('aura_chat_session_id', sessionId);
    }
    return sessionId;
};

export const chatbotService = {
    /**
     * Gửi tin nhắn hội thoại đến hệ thống RAG Chatbot
     * @param {string} message - Nội dung tin nhắn người dùng nhập vào
     * @returns {Promise<string>} - Phản hồi dạng văn bản từ LLM kết hợp RAG
     */
    sendMessage: async (message) => {
        try {
            const sessionId = getOrCreateSessionId(); // Lấy mã riêng của máy này

            // 2. Gửi kèm session_id lên Backend
            const response = await api.post('/api/v1/chat', { 
                message: message,
                session_id: sessionId 
            });
            
            // Trích xuất cấu trúc dữ liệu theo định dạng trả về chuẩn của FastAPI
            if (response.data && response.data.success) {
                return response.data.data.reply;
            }
            throw new Error('Cấu trúc dữ liệu phản hồi từ máy chủ không hợp lệ.');
        } catch (error) {
            console.error('Error in chatbotService.sendMessage:', error);
            const errorMessage = error.response?.data?.detail || error.message || 'Lỗi kết nối máy chủ.';
            throw new Error(errorMessage);
        }
    }
};