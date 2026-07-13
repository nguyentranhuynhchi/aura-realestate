// frontend/src/services/chatbotService.js
import api from './api';

export const chatbotService = {
    /**
     * Gửi tin nhắn hội thoại đến hệ thống RAG Chatbot
     * @param {string} message - Nội dung tin nhắn người dùng nhập vào
     * @returns {Promise<string>} - Phản hồi dạng văn bản từ Gemini API kết hợp RAG
     */
    sendMessage: async (message) => {
        try {
            const response = await api.post('/api/v1/chat', { message: message });
            
            // Trích xuất cấu trúc dữ liệu theo định dạng trả về chuẩn của FastAPI
            if (response.data && response.data.success) {
                return response.data.data.reply;
            }
            throw new Error('Cấu trúc dữ liệu phản hồi từ máy chủ không hợp lệ.');
        } catch (error) {
            console.error('Error in chatbotService.sendMessage:', error);
            // Trả về thông báo lỗi chuẩn kỹ thuật sang tầng giao diện hiển thị
            const errorMessage = error.response?.data?.detail || error.message || 'Lỗi kết nối máy chủ.';
            throw new Error(errorMessage);
        }
    }
};