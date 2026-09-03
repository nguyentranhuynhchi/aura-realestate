import React, { useState, useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { chatbotService } from '../../../services/chatbotService';

const ChatbotPage = () => {
    const [messages, setMessages] = useState([
        {
            text: "Xin chào! Tôi là trợ lý ảo Aura Realestate. Bạn cần tôi hỗ trợ phân tích thông tin quy hoạch hay tư vấn tầm giá bất động sản khu vực nào hôm nay?",
            isUser: false
        }
    ]);
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    const handleSendMessage = async (userText) => {
        // 1. Thêm tin nhắn của User vào giao diện
        setMessages((prev) => [...prev, { text: userText, isUser: true }]);
        setIsLoading(true);

        let botReplyAccumulator = "";
        let isFirstToken = true;

        // 2. Gọi hàm Streaming SSE
        await chatbotService.sendMessageStream(
            userText,
            // onChunk: Mỗi khi nhận được 1 token mới
            (token) => {
                if (isFirstToken) {
                    setIsLoading(false); // Tắt animation chờ ngay khi chữ đầu tiên xuất hiện!
                    isFirstToken = false;
                    // Tạo một khung tin nhắn mới cho Bot
                    setMessages((prev) => [...prev, { text: token, isUser: false }]);
                    botReplyAccumulator = token;
                } else {
                    botReplyAccumulator += token;
                    // Cập nhật chữ rơi trực tiếp vào tin nhắn cuối cùng của Bot
                    setMessages((prev) => {
                        const updated = [...prev];
                        updated[updated.length - 1] = {
                            text: botReplyAccumulator,
                            isUser: false
                        };
                        return updated;
                    });
                }
            },
            // onFinish: Khi Bot sinh xong toàn bộ câu
            () => {
                setIsLoading(false);
            },
            // onError: Nếu có lỗi kết nối
            (error) => {
                setIsLoading(false);
                setMessages((prev) => [
                    ...prev,
                    { text: `Lỗi kết nối Streaming: ${error.message}`, isUser: false }
                ]);
            }
        );
    };

    return (
        <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-140px)] bg-white border border-slate-100 rounded-2xl shadow-[0_12px_40px_rgb(0,0,0,0.03)] overflow-hidden">
            {/* Header Mini Chatbot sang chảnh */}
            <div className="bg-white px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
                    <div>
                        <h2 className="font-bold text-sm text-[#0F172A]">AI tư vấn, đề xuất nhà & hỗ trợ chính sách</h2>
                        <p className="text-[11px] text-slate-400">Hệ tri thức kết hợp định tuyến dữ liệu RAG thời gian thực (SSE Streaming)</p>
                    </div>
                </div>
            </div>

            {/* Danh sách tin nhắn */}
            <div className="flex-1 p-6 overflow-y-auto bg-slate-50/50 space-y-2">
                {messages.map((msg, index) => (
                    <ChatMessage key={index} message={msg.text} isUser={msg.isUser} />
                ))}
                
                {isLoading && (
                    <div className="flex items-start gap-3 my-2">
                        <div className="px-4 py-3 bg-white text-slate-400 rounded-2xl border border-slate-100 text-xs italic shadow-sm animate-pulse">
                            Aura AI đang tìm thông tin phù hợp với yêu cầu của bạn, vui lòng chờ trong giây lát nhé...
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Ô nhập tin nhắn */}
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
        </div>
    );
};

export default ChatbotPage;