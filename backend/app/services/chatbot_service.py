import os
import json
import re
import chromadb
from google import genai
from google.genai import types
from dotenv import load_dotenv
from chromadb.utils import embedding_functions

load_dotenv()

class ChatbotService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Không tìm thấy GEMINI_API_KEY trong file .env.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-flash-latest"
        self.chroma_client = chromadb.HttpClient(host="chromadb", port=8000)
        
        self.sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.chroma_client.get_or_create_collection(
            name="realestate_collection", 
            embedding_function=self.sentence_transformer_ef
        )
        # Khởi tạo phiên Chat để giữ lịch sử hội thoại đa lượt (Multi-turn)
        self.chat_session = self.client.chats.create(model=self.model_name)

    def _extract_search_intent(self, user_message: str) -> dict:
        """Sử dụng Gemini làm Middleware phân tích cú pháp câu hỏi ra bộ lọc JSON"""
        prompt = (
            "Bạn là bộ lọc dữ liệu thông minh. Hãy trích xuất các tiêu chí tìm kiếm bất động sản từ câu nói của người dùng thành cấu trúc JSON.\n"
            "Các trường cần trích xuất (Nếu không có hoặc không rõ trong câu nói, bắt buộc phải để null):\n"
            "- district: Tên quận chuẩn hóa (Ví dụ: 'Quận 1', 'Quận 5', 'Quận Tân Bình', 'TP. Thủ Đức', 'Huyện Bình Chánh'...)\n"
            "- price_max: Giá trị số float thể hiện mức giá tối đa người dùng muốn (đơn vị: Tỷ VNĐ). Nếu nói '1 tỷ' -> 1.0, '5.8 tỷ' -> 5.8\n"
            "- price_min: Mức giá tối thiểu (đơn vị: Tỷ VNĐ)\n"
            "- direction: Hướng nhà chuẩn hóa ('Bắc', 'Nam', 'Tây', 'Đông', 'Đông Nam', 'Đông Bắc', 'Tây Nam', 'Tây Bắc')\n"
            "- legal_status: Tình trạng pháp lý ('Có Sổ', 'Chưa Sổ / HDMB')\n"
            "- core_query: Chuỗi văn bản ngắn thể hiện nhu cầu cốt lõi ngoài thông số (Ví dụ: 'kinh doanh thời trang', 'hẻm xe hơi', 'nhà ở yên tĩnh')\n\n"
            f"Câu nói của người dùng: \"{user_message}\"\n\n"
            "Chỉ trả ra chuỗi JSON duy nhất, không thêm bớt từ giải thích."
        )
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0, response_mime_type="application/json")
            )
            return json.loads(response.text)
        except:
            return {"district": None, "price_max": None, "price_min": None, "direction": None, "legal_status": None, "core_query": user_message}

    def ask_rag_bot(self, user_message: str) -> str:
        try:
            total_in_db = self.collection.count()
            
            # 1. Trích xuất ý định bộ lọc
            intent = self._extract_search_intent(user_message)
            
            # 2. Xây dựng bộ lọc logic phức hợp where cho ChromaDB
            and_filters = []
            if intent.get("district"):
                and_filters.append({"district": {"$eq": intent["district"]}})
            if intent.get("price_max"):
                and_filters.append({"price_numeric": {"$lte": float(intent["price_max"])}})
            if intent.get("price_min"):
                and_filters.append({"price_numeric": {"$gte": float(intent["price_min"])}})
            if intent.get("direction"):
                and_filters.append({"direction": {"$eq": intent["direction"]}})
            if intent.get("legal_status"):
                and_filters.append({"legal_status": {"$eq": intent["legal_status"]}})

            # Cấu hình tham số truy vấn lai
            query_args = {"query_texts": [intent.get("core_query") or user_message], "n_results": 3}
            if and_filters:
                query_args["where"] = {"$and": and_filters} if len(and_filters) > 1 else and_filters[0]

            results = self.collection.query(**query_args)
            
            # 3. Tổng hợp bối cảnh
            valid_docs = []
            if results and results.get('documents') and results['documents'][0]:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                
                for doc, meta in zip(documents, metadatas):
                    # Khôi phục thông số chuẩn từ metadata ra khối thông tin thô
                    info_block = (
                        f" BẤT ĐỘNG SẢN THẬT:\n"
                        f"- Vị trí: {meta.get('district')} (Thuộc phạm vi TP.HCM)\n"
                        f"- Giá bán: {meta.get('price_numeric')} tỷ\n"
                        f"- Diện tích: {meta.get('area_numeric')} m2\n"
                        f"- Kết cấu: {meta.get('floors')} tầng, {meta.get('bathrooms')} WC\n"
                        f"- Hướng nhà: {meta.get('direction')} | Pháp lý: {meta.get('legal_status')}\n"
                        f"- Link URL truy cập nguồn: {meta.get('url')}\n"
                        f"- Chi tiết mô tả: {doc}"
                    )
                    valid_docs.append(info_block)

            if valid_docs:
                context = f"=== KHO DỮ LIỆU THỰC TẾ TRÙNG KHỚP ===\nTổng kho đang vận hành: {total_in_db} chunks.\n" + "\n---\n".join(valid_docs)
            else:
                context = f"HỆ THỐNG PHÁT HIỆN: KHÔNG CÓ BẤT ĐỘNG SẢN NÀO TRONG KHO THỎA MÃN ĐÚNG TIÊU CHÍ KHÁCH HỎI.\nThông tin kho: Tổng kho hiện quản lý {total_in_db} chunks."

            # 4. Định nghĩa System Instruction động nghiêm ngặt theo kịch bản mới 
            system_instruction = (
                "Bạn là một Chuyên viên tư vấn bất động sản trung gian uy tín, khéo léo của Aura Realestate tại thị trường TP.HCM.\n\n"
                
                "QUY TẮC PHẠM VI ĐỊA LÝ TỐI CAO:\n"
                "- Bạn CHỈ ĐƯỢC PHÉP tư vấn, thảo luận và trả lời các bất động sản nằm trong phạm vi Thành phố Hồ Chí Minh (TP.HCM).\n"
                "- Nếu khách hàng gặng hỏi hoặc yêu cầu tìm kiếm các tỉnh thành khác (như Hà Nội, Bình Dương, Đồng Nai...), bạn phải từ chối lịch sự và khéo léo kéo họ về giỏ hàng tại TP.HCM.\n\n"
                
                "QUY TẮC PHẢN HỒI KỊCH BẢN (MỀM DẺO - THẢ MỒI):\n"
                "1. Khi đã chọn được câu trả lời/căn nhà phù hợp từ 'KHO DỮ LIỆU THỰC TẾ TRÙNG KHỚP', bạn KHÔNG ĐƯỢC bung hết toàn bộ thông tin chi tiết ra ngay câu đầu tiên.\n"
                "2. Hãy viết thật mềm dẻo, chỉ liệt kê một vài THÔNG TIN QUAN TRỌNG NHẤT (Ví dụ: Vị trí quận, diện tích, số tầng, giá bán sơ bộ và ưu điểm nổi bật như mặt tiền kinh doanh/hẻm xe hơi).\n"
                "3. TUYỆT ĐỐI KHÔNG ĐƯỢC tự ý in Link URL truy cập ra ở lượt phản hồi đầu tiên này.\n"
                "4. Cuối câu trả lời, bạn BẮT BUỘC phải hỏi gợi mở xem người dùng có muốn nhận đầy đủ thông tin chi tiết còn lại kèm đường link URL truy cập trực tiếp của căn nhà này để xem hình ảnh/sổ sách không.\n"
                "5. CHỈ KHI người dùng phản hồi đồng ý (Ví dụ: 'ok', 'cho xin link đi', 'gửi đi em'), ở lượt chat kế tiếp bạn mới bung đầy đủ chi tiết và link URL thật ra.\n\n"
                
                "QUY TẮC PHÒNG CHỐNG ẢO TƯỞNG:\n"
                "- Chỉ dùng data có sẵn, không sửa đổi thông số giá/quận, không bịa dự án ma khi kho báo rỗng.\n\n"
                f"{context}"
            )

            config = types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.2)
            
            # Gửi tin nhắn qua chat_session để GIỮ TRÍ NHỚ ĐA LƯỢT
            response = self.chat_session.send_message(message=user_message, config=config)
            return response.text
        except Exception as e:
            return f"Lỗi xử lý hệ thống RAG: {str(e)}"

chatbot_service = ChatbotService()