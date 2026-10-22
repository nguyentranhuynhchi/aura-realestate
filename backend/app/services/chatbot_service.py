import os
import re
import json
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
import psycopg
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

class ChatbotService:
    # 1. Danh sách 23 Quận/Huyện chuẩn hóa lấy nguyên văn từ DISTRICT_MAPPING của Pipeline
    VALID_DISTRICTS = [
        'Huyện Cần Giờ', 'Huyện Củ Chi', 'Huyện Hóc Môn', 'Huyện Nhà Bè', 'Huyện Bình Chánh',
        'Quận 6', 'Quận 4', 'Quận 11', 'Quận 5', 'Quận 8', 'Quận 9', 'Quận 3',
        'Quận 10', 'Quận 2', 'Quận Tân Phú', 'Quận Tân Bình', 'Quận Phú Nhuận',
        'Quận Gò Vấp', 'Quận Bình Thạnh', 'Quận 12', 'Quận 7', 'TP. Thủ Đức', 'Quận 1'
    ]

    # Bảng ánh xạ từ viết tắt / tên phụ sang Quận/Huyện chuẩn xác 100%
    DISTRICT_ALIASES = {
        'q1': 'Quận 1', 'quan 1': 'Quận 1', 'q 1': 'Quận 1',
        'q2': 'Quận 2', 'quan 2': 'Quận 2', 'q 2': 'Quận 2', 'thảo điền': 'Quận 2', 'an khánh': 'Quận 2', 'cát lái': 'Quận 2', 'bình trưng': 'Quận 2',
        'q3': 'Quận 3', 'quan 3': 'Quận 3', 'q 3': 'Quận 3',
        'q4': 'Quận 4', 'quan 4': 'Quận 4', 'q 4': 'Quận 4',
        'q5': 'Quận 5', 'quan 5': 'Quận 5', 'q 5': 'Quận 5',
        'q6': 'Quận 6', 'quan 6': 'Quận 6', 'q 6': 'Quận 6',
        'q7': 'Quận 7', 'quan 7': 'Quận 7', 'q 7': 'Quận 7', 'phú mỹ hưng': 'Quận 7', 'tân thuận': 'Quận 7',
        'q8': 'Quận 8', 'quan 8': 'Quận 8', 'q 8': 'Quận 8',
        'q9': 'Quận 9', 'quan 9': 'Quận 9', 'q 9': 'Quận 9',
        'q10': 'Quận 10', 'quan 10': 'Quận 10', 'q 10': 'Quận 10',
        'q11': 'Quận 11', 'quan 11': 'Quận 11', 'q 11': 'Quận 11',
        'q12': 'Quận 12', 'quan 12': 'Quận 12', 'q 12': 'Quận 12',
        'thủ đức': 'TP. Thủ Đức', 'tp thủ đức': 'TP. Thủ Đức', 'tp.thủ đức': 'TP. Thủ Đức',
        'bình thạnh': 'Quận Bình Thạnh', 'gò vấp': 'Quận Gò Vấp',
        'phú nhuận': 'Quận Phú Nhuận', 'tân bình': 'Quận Tân Bình', 'tân phú': 'Quận Tân Phú',
        'bình chánh': 'Huyện Bình Chánh', 'hóc môn': 'Huyện Hóc Môn',
        'củ chi': 'Huyện Củ Chi', 'nhà bè': 'Huyện Nhà Bè', 'cần giờ': 'Huyện Cần Giờ'
    }

    def __init__(self):
        # 1. Khởi tạo LLM Local qua vLLM
        self.llm = ChatOpenAI(
            model=os.getenv("VLLM_MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct-AWQ"),
            base_url=os.getenv("VLLM_BASE_URL", "http://vllm:8000/v1"),
            api_key=os.getenv("VLLM_API_KEY", "none_required"),
            temperature=0.2,
            max_tokens=None, 
            timeout=60,
            extra_body={
                "max_tokens": 256,
                "repetition_penalty": 1.15
            }  
        )

        # 2. Khởi tạo Embeddings & ChromaDB Client (Dense Retriever thuần túy)
        self.embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.chroma_http_client = chromadb.HttpClient(host="chromadb", port=8000)
        
        self.vector_store = Chroma(
            client=self.chroma_http_client,
            collection_name="realestate_collection",
            embedding_function=self.embedding_function
        )

        # 3. Quản lý database PostgreSQL
        self.db_url = os.environ.get(
            "DATABASE_URL", 
            "postgresql://postgres:postgres@postgres:5432/aura_realestate_db"
        )
        self.rag_chain = self._build_rag_chain()

    # =========================================================================================
    # TẦNG A: REGEX BÓC TÁCH & MÁY TRẠNG THÁI GHI ĐÈ METADATA (SLOT FILLING)
    # =========================================================================================
    def _extract_district(self, text: str) -> Optional[str]:
        """Bóc tách Quận/Huyện bằng Regex đối chiếu Whitelist và Bảng bí danh"""
        if not text:
            return None
        text_lower = text.lower()

        # 1. Ưu tiên 23 quận chuẩn (sắp xếp dài trước để tránh 'Quận 1' ăn nhầm 'Quận 10')
        sorted_districts = sorted(self.VALID_DISTRICTS, key=len, reverse=True)
        for district in sorted_districts:
            pattern = r'(?i)\b' + re.escape(district) + r'\b'
            if re.search(pattern, text):
                return district

        # 2. Kiểm tra bí danh (q1, q2, thủ đức, tân bình...)
        for alias, district in self.DISTRICT_ALIASES.items():
            pattern = r'(?i)\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text_lower):
                return district

        return None

    def _extract_price_range(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        """Bóc tách tầm giá (min, max) bằng Regex toán học chính xác 100%"""
        if not text:
            return None, None
        text_clean = text.lower().replace(',', '.')

        # Khoảng giá: "từ 7 đến 10 tỷ", "7 - 10 tỷ", "7 đến 10 tỷ"
        m_range = re.search(r'(?:từ\s*)?(\d+(?:\.\d+)?)\s*(?:-|đến|tới)\s*(\d+(?:\.\d+)?)\s*tỷ', text_clean)
        if m_range:
            return float(m_range.group(1)), float(m_range.group(2))

        # Dưới mức: "dưới 5 tỷ", "tối đa 5 tỷ", "< 5 tỷ", "nhỏ hơn 5 tỷ"
        m_below = re.search(r'(?:dưới|<|tối đa|nhỏ hơn)\s*(\d+(?:\.\d+)?)\s*tỷ', text_clean)
        if m_below:
            return None, float(m_below.group(1))

        # Trên mức: "trên 10 tỷ", "tối thiểu 10 tỷ", "> 10 tỷ", "hơn 10 tỷ"
        m_above = re.search(r'(?:trên|>|tối thiểu|lớn hơn|hơn)\s*(\d+(?:\.\d+)?)\s*tỷ', text_clean)
        if m_above:
            return float(m_above.group(1)), None

        # Tầm giá đơn: "tầm 5 tỷ", "khoảng 5 tỷ", "mức giá 5 tỷ", "5 tỷ"
        m_approx = re.search(r'(?:tầm|khoảng|giá|mức giá)?\s*(\d+(?:\.\d+)?)\s*tỷ', text_clean)
        if m_approx:
            val = float(m_approx.group(1))
            return None, val

        return None, None

    def get_search_state(self, session_id: str) -> Dict:
        """Đọc JSON A lưu trữ trạng thái tiêu chí hiện tại từ PostgreSQL"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT summary FROM chat_summaries WHERE session_id = %s;", (session_id,))
                row = cur.fetchone()
                if row and row[0]:
                    try:
                        return json.loads(row[0])
                    except Exception:
                        pass
        return {"district": None, "price_min": None, "price_max": None}

    def update_search_state(self, session_id: str, user_message: str) -> Dict:
        """Cơ chế ghi đè tuyệt đối: Feature nào xuất hiện mới thì ghi đè, không nhắc thì kế thừa"""
        current_state = self.get_search_state(session_id)
        msg_lower = user_message.lower()

        # 1. Reset nếu khách muốn bắt đầu lại
        if any(w in msg_lower for w in ["tìm lại từ đầu", "reset", "xóa bộ lọc", "tìm nhà khác"]):
            current_state = {"district": None, "price_min": None, "price_max": None}

        # 2. Bóc tách slot từ câu mới nhất bằng Regex
        new_district = self._extract_district(user_message)
        new_price_min, new_price_max = self._extract_price_range(user_message)

        # 3. Ghi đè (Overwrite) hoặc Kế thừa (Inherit)
        if new_district:
            current_state["district"] = new_district
        if new_price_min is not None or new_price_max is not None:
            current_state["price_min"] = new_price_min
            current_state["price_max"] = new_price_max

        # 4. Lưu lại JSON A xuống Database
        state_json = json.dumps(current_state, ensure_ascii=False)
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_summaries (session_id, summary, updated_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (session_id) 
                    DO UPDATE SET summary = EXCLUDED.summary, updated_at = CURRENT_TIMESTAMP;
                """, (session_id, state_json))
                conn.commit()

        return current_state

    # =========================================================================================
    # QUERY REWRITING: KẾT HỢP B + A + PROMPT VIẾT LẠI THÀNH 1 QUERY GỌN
    # =========================================================================================
    def _condense_query(self, user_message: str, chat_history: List, state_a: Dict) -> str:
        """Viết lại câu hỏi thành 1 query duy nhất, ưu tiên tuyệt đối các thông tin đã ghi đè trong State A"""
        if not chat_history and not state_a.get("district") and not state_a.get("price_max") and not state_a.get("price_min"):
            return user_message

        recent_context = "\n".join([f"{type(m).__name__}: {m.content}" for m in chat_history[-4:]])
        state_desc = []
        if state_a.get("district"):
            state_desc.append(f"Khu vực chốt: {state_a['district']}")
        if state_a.get("price_min") and state_a.get("price_max"):
            state_desc.append(f"Giá: {state_a['price_min']}-{state_a['price_max']} tỷ")
        elif state_a.get("price_max"):
            state_desc.append(f"Giá: khoảng hoặc dưới {state_a['price_max']} tỷ")
        elif state_a.get("price_min"):
            state_desc.append(f"Giá: trên {state_a['price_min']} tỷ")
        
        state_str = " | ".join(state_desc) if state_desc else "Chưa có tiêu chí cụ thể"

        rewrite_prompt = (
            "Bạn là chuyên viên chuẩn hóa truy vấn tìm kiếm bất động sản TP.HCM. BẮT BUỘC TRẢ LỜI BẰNG TIẾNG VIỆT.\n"
            "Nhiệm vụ: Dựa vào 'Tiêu chí hiện tại (State A)' và 'Lịch sử hội thoại', hãy viết lại 'Câu hỏi mới nhất' "
            "thành MỘT CÂU TÌM KIẾM ĐỘC LẬP duy nhất để tra cứu dữ liệu.\n"
            "QUY TẮC:\n"
            "1. Nếu câu hỏi mới nhất có thay đổi tiêu chí (Quận mới, Giá mới), BẮT BUỘC lấy tiêu chí mới nhất ghi đè vào câu tìm kiếm.\n"
            "2. Nếu câu hỏi mới nối tiếp câu cũ, giữ nguyên tiêu chí đã chốt trong State A.\n"
            "3. Bỏ toàn bộ lời chào ('xin chào', 'tôi tên là').\n"
            "CHỈ trả về duy nhất 1 câu tìm kiếm ngắn gọn, không giải thích.\n\n"
            f"Tiêu chí hiện tại (State A): {state_str}\n"
            f"Lịch sử hội thoại gần nhất:\n{recent_context}\n\n"
            f"Câu hỏi mới nhất: {user_message}\n\n"
            f"Câu tìm kiếm viết lại:"
        )
        try:
            standalone_query = self.llm.invoke(rewrite_prompt).content.strip()
            print(f"[Query Rewriting] '{user_message}' ➔ '{standalone_query}' (State A: {state_a})")
            return standalone_query if standalone_query else user_message
        except Exception:
            return user_message

    # =========================================================================================
    # LỌC CỨNG TẬP M TẠI CHROMADB & TÌM K SAMPLE PHÙ HỢP NHẤT (KHÔNG CẦN BM25 & RRF)
    # =========================================================================================
    def _retrieve_documents(self, search_query: str, state_a: Dict) -> str:
        """Lọc cứng tập M theo Quận và Giá, sau đó Vector Search tìm K sample tốt nhất"""
        total_in_db = self.vector_store._collection.count()
        target_district = state_a.get("district")
        price_min = state_a.get("price_min")
        price_max = state_a.get("price_max")

        # 1. Lọc cứng cấp Metadata (ChromaDB) theo Quận để khoanh vùng chính xác
        dense_filter = {"district": target_district} if target_district else None
        if target_district:
            print(f"[ChromaDB Pre-Filtering] ➔ ĐÃ KHÓA CỨNG CHỈ TÌM TRONG: '{target_district}'")

        # Lấy tập ứng viên ban đầu trong quận đó
        raw_candidates = self.vector_store.similarity_search(search_query, k=15, filter=dense_filter)

        if not raw_candidates:
            return "HỆ THỐNG: Hiện chưa có bất động sản nào trong kho phù hợp với tiêu chí trên."

        # 2. Lọc định lượng số học để xác định chính xác tập M
        matched_m = []
        for doc in raw_candidates:
            p = doc.metadata.get("price_numeric")
            try:
                p_val = float(p) if p is not None else 0.0
            except (ValueError, TypeError):
                p_val = 0.0

            if p_val > 0:
                if price_min is not None and p_val < price_min:
                    continue
                if price_max is not None and p_val > (price_max * 1.15):  # Dung sai 15%
                    continue
                matched_m.append(doc)

        # 3. Lấy K sample tốt nhất từ tập M (nếu tập M rỗng thì fallback lấy các căn gần nhất để tư vấn)
        final_docs = matched_m if matched_m else raw_candidates

        formatted_docs = []
        for d in final_docs[:4]:
            meta = d.metadata
            info_block = (
                f" BẤT ĐỘNG SẢN THẬT:\n"
                f"- Vị trí: {meta.get('district', 'N/A')} (Thuộc phạm vi TP.HCM)\n"
                f"- Giá bán: {meta.get('price_numeric', 'N/A')} tỷ\n"
                f"- Diện tích: {meta.get('area_numeric', 'N/A')} m2\n"
                f"- Kết cấu: {meta.get('floors', 'N/A')} tầng, {meta.get('bathrooms', 'N/A')} WC\n"
                f"- Hướng nhà: {meta.get('direction', 'N/A')} | Pháp lý: {meta.get('legal_status', 'N/A')}\n"
                f"- Chi tiết mô tả: {d.page_content}"
            )
            formatted_docs.append(info_block)

        return (
            f"=== KHO DỮ LIỆU THỰC TẾ TRÙNG KHỚP (TẬP M ĐÃ LỌC CỨNG) ===\n"
            f"Tổng kho đang vận hành: {total_in_db} chunks.\n" + "\n---\n".join(formatted_docs)
        )

    # =========================================================================================
    # TẦNG B: CỬA SỔ TRƯỢT SLIDING WINDOW (FIFO 6 TIN GẦN NHẤT)
    # =========================================================================================
    def get_recent_history(self, session_id: str) -> List:
        """Cửa sổ trượt B: Lấy đúng 6 tin nhắn gần nhất nguyên văn (3 cặp User - AI)"""
        messages = []
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT message FROM (
                        SELECT id, message FROM chat_history 
                        WHERE session_id = %s 
                        ORDER BY id DESC 
                        LIMIT 6
                    ) sub ORDER BY id ASC;
                    """,
                    (session_id,)
                )
                for r in cur.fetchall():
                    msg_json = r[0]
                    role = msg_json.get("type")
                    content = msg_json.get("data", {}).get("content", "")
                    if role == "human":
                        messages.append(HumanMessage(content=content))
                    elif role == "ai":
                        messages.append(AIMessage(content=content))
        return messages

    def save_message(self, session_id: str, role: str, content: str):
        """Lưu tin nhắn vào chat_history chuẩn JSONB"""
        msg_payload = {
            "type": role,
            "data": {
                "content": content,
                "additional_kwargs": {},
                "response_metadata": {},
                "type": role,
                "name": None,
                "id": None,
                "example": False
            }
        }
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_history (session_id, message) VALUES (%s, %s::jsonb);",
                    (session_id, psycopg.types.json.Jsonb(msg_payload))
                )
                conn.commit()

    def compress_memory_if_needed(self, session_id: str):
        """Giữ tối đa 12 tin trong DB, trượt qua là xóa luôn. 
        TUYỆT ĐỐI KHÔNG DÙNG LLM NÉN TÓM TẮT ĐỂ TRÁNH ẢO GIÁC."""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM chat_history 
                    WHERE session_id = %s 
                    AND id NOT IN (
                        SELECT id FROM chat_history 
                        WHERE session_id = %s 
                        ORDER BY id DESC 
                        LIMIT 12
                    );
                    """,
                    (session_id, session_id)
                )
                conn.commit()

    # =========================================================================================
    # RAG CHAIN: PHẢN HỒI TỰ NHIÊN, KHÔNG CÂU NỆ MÁY MÓC
    # =========================================================================================
    def _build_rag_chain(self):
        system_instruction = (
            "Bạn là chuyên viên tư vấn bất động sản Aura Realestate tại TP.HCM. BẮT BUỘC phản hồi 100% bằng TIẾNG VIỆT tự nhiên, thân thiện và chính xác.\n"
            "TUYỆT ĐỐI CẤM SỬ DỤNG TIẾNG TRUNG/CHỮ HÁN HOẶC TIẾNG ANH.\n"
            "TUYỆT ĐỐI CẤM mở đầu câu bằng 'Theo hồ sơ của bạn' hay nhắc đến cụm từ 'hồ sơ/ghi chú'. Hãy xưng hô lịch sự và trả lời trực diện vào câu hỏi của khách.\n\n"
            "DỮ LIỆU NHÀ ĐẤT TRONG HỆ THỐNG:\n"
            "{context}\n\n"
            "QUY TẮC TƯ VẤN:\n"
            "1. KHI CÓ NHÀ PHÙ HỢP TRONG DỮ LIỆU:\n"
            "   - Báo ngay các thông số thực tế: Vị trí, Giá bán, Diện tích, Kết cấu (tầng, WC), Hướng và Pháp lý.\n"
            "   - Trình bày dạng gạch đầu dòng rõ ràng, làm nổi bật ưu điểm căn nhà.\n"
            "2. KHI KHÔNG CÓ CĂN NÀO ĐÚNG 100% TIÊU CHÍ (ví dụ không có căn đúng giá trong quận đó):\n"
            "   - Nói thẳng thắn, lịch sự: Hiện kho dữ liệu chưa có căn đúng mức giá mong muốn tại khu vực này.\n"
            "   - Giới thiệu rõ ràng giá và thông số của các căn có sẵn gần mức giá đó nhất trong dữ liệu để khách tham khảo.\n"
            "3. KHI KHÁCH CHỈ CHÀO HỎI:\n"
            "   - Chào lại ngắn gọn và hỏi khách cần tìm nhà ở khu vực nào và tầm tài chính bao nhiêu.\n"
            "4. Câu trả lời tự nhiên, chuyên nghiệp và trung thực với dữ liệu."
        )

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_instruction),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_message}")
        ])

        return prompt_template | self.llm | StrOutputParser()

    def ask_rag_bot(self, user_message: str, session_id: str = "default_session") -> str:
        try:
            # 1. Cập nhật State A (Ghi đè/Kế thừa)
            state_a = self.update_search_state(session_id, user_message)

            # 2. Lấy Cửa sổ trượt B (6 tin gần nhất)
            chat_history = self.get_recent_history(session_id)

            # 3. Viết lại Query và Lọc tập M tại ChromaDB
            standalone_query = self._condense_query(user_message, chat_history, state_a)
            context = self._retrieve_documents(standalone_query, state_a)

            # 4. Gửi vào LLM sinh câu trả lời
            response = self.rag_chain.invoke({
                "context": context,
                "chat_history": chat_history,
                "user_message": user_message
            })
            return response
        except Exception as e:
            return f"Lỗi xử lý hệ thống RAG: {str(e)}"

    async def astream_rag_bot(self, user_message: str, session_id: str = "default_session"):
        try:
            # 1. Cập nhật State A (Ghi đè/Kế thừa)
            state_a = self.update_search_state(session_id, user_message)

            # 2. Lấy Cửa sổ trượt B (6 tin gần nhất)
            chat_history = self.get_recent_history(session_id)

            # 3. Viết lại Query và Lọc tập M tại ChromaDB
            standalone_query = self._condense_query(user_message, chat_history, state_a)
            context = self._retrieve_documents(standalone_query, state_a)

            # 4. Stream từng token về client qua SSE
            async for chunk in self.rag_chain.astream({
                "context": context,
                "chat_history": chat_history,
                "user_message": user_message
            }):
                if chunk:
                    yield chunk
        except Exception as e:
            yield f"\n[Lỗi hệ thống Streaming: {str(e)}]"

chatbot_service = ChatbotService()