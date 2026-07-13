// frontend/src/features/chatbot/components/ChatMessage.jsx
import React from 'react';
import { User, Bot } from 'lucide-react';

const ChatMessage = ({ message, isUser }) => {
    return (
        <div className={`flex w-full my-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex max-w-[75%] items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                {/* Icon đại diện */}
                <div className={`p-2 rounded-full flex-shrink-0 ${isUser ? 'bg-blue-600 text-white' : 'bg-gray-300 text-gray-700'}`}>
                    {isUser ? <User size={18} /> : <Bot size={18} />}
                </div>

                {/* Bong bóng nội dung tin nhắn */}
                <div className={`p-3 rounded-lg text-sm leading-relaxed shadow-sm whitespace-pre-line
                    ${isUser ? 'bg-blue-500 text-white rounded-tr-none' : 'bg-white text-gray-800 border border-gray-200 rounded-tl-none'}`}>
                    {message}
                </div>
            </div>
        </div>
    );
};

export default ChatMessage;