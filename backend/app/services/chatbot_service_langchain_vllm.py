import os
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

load_dotenv()


# 1. Schema trích xuất tiêu chí tìm kiếm bất động sản
class SearchFilterIntent(BaseModel):
    district: Optional[str] = Field(None, description="Tên quận/huyện chuẩn hóa (Ví dụ: 'Quận 1', 'Quận 5', 'TP. Thủ Đức', 'Huyện Bình Chánh')")
    price_max: Optional[float] = Field(None, description="Mức giá tối đa người dùng muốn (đơn vị: Tỷ VNĐ, ví dụ: 5.8)")
    price_min: Optional[float] = Field(None, description="Mức giá tối thiểu (đơn vị: Tỷ VNĐ, ví dụ: 1.0)")
    direction: Optional[str] = Field(None, description="Hướng nhà ('Bắc', 'Nam', 'Tây', 'Đông', 'Đông Nam', 'Đông Bắc', 'Tây Nam', 'Tây Bắc')")
    legal_status: Optional[str] = Field(None, description="Tình trạng pháp lý ('Có Sổ', 'Chưa Sổ / HDMB')")
    core_query: Optional[str] = Field(None, description="Nhu cầu cốt lõi ngoài thông số (Ví dụ: 'mặt tiền kinh doanh', 'hẻm xe hơi', 'nhà yên tĩnh')")


class ChatbotService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Không tìm thấy GEMINI_API_KEY trong file .env.")

        self.llm = ChatOpenAI(
            model="qwen2.5:7b",
            base_url="http://host.docker.internal:11434/v1",
            api_key="ollama",  # Bắt buộc điền chuỗi bất kỳ
            temperature=0.2,
            extra_body={"num_ctx": 2048}
            
        )
        # Trình trích xuất ý định (Structured Output)
        self.intent_extractor = self.llm.with_structured_output(SearchFilterIntent)

        # Khởi tạo Embeddings & ChromaDB Client
        self.embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.chroma_http_client = chromadb.HttpClient(host="chromadb", port=8000)
        
        self.vector_store = Chroma(
            client=self.chroma_http_client,
            collection_name="realestate_collection",
            embedding_function=self.embedding_function
        )

        # Quản lý bộ nhớ hội thoại đa lượt
        self._history_store = {}
        self.rag_chain = self._build_rag_chain()

    def _get_chat_history(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self._history_store:
            self._history_store[session_id] = InMemoryChatMessageHistory()
        return self._history_store[session_id]

    def _extract_intent(self, user_message: str) -> SearchFilterIntent:
        """Trích xuất bộ lọc thông minh qua LangChain Structured Output"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Bạn là bộ lọc dữ liệu thông minh. Trích xuất các tiêu chí tìm kiếm bất động sản từ câu nói của người dùng thành cấu trúc được yêu cầu."),
            ("human", "{message}")
        ])
        extractor_chain = prompt | self.intent_extractor
        try:
            return extractor_chain.invoke({"message": user_message})
        except Exception:
            return SearchFilterIntent(core_query=user_message)

    def _retrieve_documents(self, user_message: str) -> str:
        """Truy xuất tài liệu từ ChromaDB kèm Dynamic Metadata Filter"""
        intent = self._extract_intent(user_message)
        total_in_db = self.vector_store._collection.count()

        # Tạo bộ lọc where metadata cho ChromaDB
        and_filters = []
        if intent.district:
            and_filters.append({"district": {"$eq": intent.district}})
        if intent.price_max is not None:
            and_filters.append({"price_numeric": {"$lte": float(intent.price_max)}})
        if intent.price_min is not None:
            and_filters.append({"price_numeric": {"$gte": float(intent.price_min)}})
        if intent.direction:
            and_filters.append({"direction": {"$eq": intent.direction}})
        if intent.legal_status:
            and_filters.append({"legal_status": {"$eq": intent.legal_status}})

        filter_kwargs = {}
        if and_filters:
            filter_kwargs["filter"] = {"$and": and_filters} if len(and_filters) > 1 else and_filters[0]

        # Truy xuất vector qua LangChain Retriever
        query_text = intent.core_query or user_message
        docs: List[Document] = self.vector_store.similarity_search(query=query_text, k=3, **filter_kwargs)

        if not docs:
            return f"HỆ THỐNG PHÁT HIỆN: KHÔNG CÓ BẤT ĐỘNG SẢN NÀO TRONG KHO THỎA MÃN ĐÚNG TIÊU CHÍ KHÁCH HỎI.\nThông tin kho: Tổng kho hiện quản lý {total_in_db} chunks."

        formatted_docs = []
        for d in docs:
            meta = d.metadata
            info_block = (
                f" BẤT ĐỘNG SẢN THẬT:\n"
                f"- Vị trí: {meta.get('district')} (Thuộc phạm vi TP.HCM)\n"
                f"- Giá bán: {meta.get('price_numeric')} tỷ\n"
                f"- Diện tích: {meta.get('area_numeric')} m2\n"
                f"- Kết cấu: {meta.get('floors')} tầng, {meta.get('bathrooms')} WC\n"
                f"- Hướng nhà: {meta.get('direction')} | Pháp lý: {meta.get('legal_status')}\n"
                f"- Link URL truy cập nguồn: {meta.get('url')}\n"
                f"- Chi tiết mô tả: {d.page_content}"
            )
            formatted_docs.append(info_block)

        return f"=== KHO DỮ LIỆU THỰC TẾ TRÙNG KHỚP ===\nTổng kho đang vận hành: {total_in_db} chunks.\n" + "\n---\n".join(formatted_docs)

    def _build_rag_chain(self):
        """Xây dựng LCEL Chain hoàn chỉnh có tích hợp System Instruction và Memory"""
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
            "{context}"
        )

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_instruction),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_message}")
        ])

        # LCEL core pipeline
        core_pipeline = prompt_template | self.llm | StrOutputParser()

        # Bọc lịch sử hội thoại chuẩn LangChain
        return RunnableWithMessageHistory(
            core_pipeline,
            self._get_chat_history,
            input_messages_key="user_message",
            history_messages_key="chat_history"
        )

    def ask_rag_bot(self, user_message: str, session_id: str = "default_session") -> str:
        """Hàm công khai giữ nguyên Input/Output interface ban đầu"""
        try:
            # 1. Lấy context dữ liệu qua VectorStore
            context = self._retrieve_documents(user_message)

            # 2. Chạy qua LCEL Chain với Session ID tương ứng
            response = self.rag_chain.invoke(
                {"context": context, "user_message": user_message},
                config={"configurable": {"session_id": session_id}}
            )
            return response
        except Exception as e:
            return f"Lỗi xử lý hệ thống RAG: {str(e)}"


chatbot_service = ChatbotService()