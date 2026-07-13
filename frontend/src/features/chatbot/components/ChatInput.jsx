// frontend/src/features/chatbot/components/ChatInput.jsx
import React, { useState } from 'react';
import { Send } from 'lucide-react';

const ChatInput = ({ onSendMessage, isLoading }) => {
    const [inputValue, setInputValue] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading) return;
        
        onSendMessage(inputValue.trim());
        setInputValue('');
    };

    return (
        <form onSubmit={handleSubmit} className="flex items-center gap-2 p-3 border-t border-gray-200 bg-white">
            <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                disabled={isLoading}
                placeholder={isLoading ? "Trợ lý đang xử lý dữ liệu RAG..." : "Nhập câu hỏi thương lượng hoặc pháp lý..."}
                className="flex-1 p-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-blue-500 disabled:bg-gray-50 text-gray-800"
            />
            <button
                type="submit"
                disabled={!inputValue.trim() || isLoading}
                className="p-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
                <Send size={18} />
            </button>
        </form>
    );
};

export default ChatInput;