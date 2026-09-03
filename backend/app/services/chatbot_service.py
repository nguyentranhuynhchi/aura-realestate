import os
from typing import List, Dict
from dotenv import load_dotenv

import chromadb
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
import psycopg
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()

class ChatbotService:
    def __init__(self):
        # 1. Khởi tạo LLM Local qua Ollama
        self.llm = ChatOpenAI(
            model=os.getenv("VLLM_MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct-AWQ"),
            base_url=os.getenv("VLLM_BASE_URL", "http://vllm:8000/v1"),
            api_key=os.getenv("VLLM_API_KEY", "none_required"),
            temperature=0.2,
            max_tokens=None, 
            timeout=60,
            extra_body={"max_tokens": 256, # ◄ KHÓA CHẶT: Bot chỉ được nói tối đa 256 tokens!
                "repetition_penalty": 1.15}  
        )
        # 2. Khởi tạo Embeddings & ChromaDB Client (Dense Retriever)
        self.embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.chroma_http_client = chromadb.HttpClient(host="chromadb", port=8000)
        
        self.vector_store = Chroma(
            client=self.chroma_http_client,
            collection_name="realestate_collection",
            embedding_function=self.embedding_function
        )

        # 3. Khởi tạo BM25 Retriever (Sparse Retriever)
        self.sparse_retriever = self._build_bm25_retriever()

        # 4. Quản lý bộ nhớ hội thoại & RAG Chain
        self.db_url = os.environ.get(
            "DATABASE_URL", 
            "postgresql://postgres:postgres@postgres:5432/aura_realestate_db"
        )
        self.rag_chain = self._build_rag_chain()

# ===========================================================================================
    def _build_bm25_retriever(self) -> BM25Retriever:
        """Lấy toàn bộ dữ liệu từ ChromaDB để lập chỉ mục BM25 Sparse Index"""
        try:
            raw_data = self.vector_store.get()
            docs = []
            if raw_data and raw_data.get("documents"):
                for text, meta in zip(raw_data["documents"], raw_data["metadatas"]):
                    docs.append(Document(page_content=text, metadata=meta or {}))
            
            if docs:
                bm25 = BM25Retriever.from_documents(docs)
                bm25.k = 5
                return bm25
        except Exception as e:
            print(f"[Warning] Không thể khởi tạo BM25 Retriever: {e}")
        return None

    def _condense_query(self, user_message: str, chat_history: List, summary: str) -> str:
        """Kỹ thuật Query Rewriting: Tự động tổng hợp History + Summary + Câu hỏi hiện tại
        thành 1 câu tìm kiếm độc lập trước khi ném vào ChromaDB / BM25.
        """
        if not chat_history and (not summary or summary == "Chưa có thông tin ghi nhớ."):
            return user_message

        recent_context = "\n".join([f"{type(m).__name__}: {m.content}" for m in chat_history[-3:]])

        rewrite_prompt = (
            "Bạn là trợ lý phân tích ngữ cảnh bất động sản.\n"
            "Nhiệm vụ: Dựa vào 'Hồ sơ khách hàng' và 'Lịch sử hội thoại', hãy viết lại 'Câu hỏi mới nhất' "
            "thành MỘT CÂU TÌM KIẾM ĐỘC LẬP đầy đủ thông tin (Quận/Vị trí, Khoảng giá, Loại nhà) để tra cứu dữ liệu.\n"
            "- Nếu câu hỏi là câu tiếp nối (ví dụ: '15 tỷ thì sao', 'tôi đang tìm gì', 'còn căn nào khác không'): Bắt buộc bổ sung thông tin vị trí/tầm giá từ lịch sử vào câu tìm kiếm.\n"
            "- Nếu câu hỏi là chào hỏi xã giao (ví dụ: 'hi', 'chào bạn'): Giữ nguyên câu hỏi gốc.\n"
            "TUYỆT ĐỐI chỉ trả về câu tìm kiếm ngắn gọn, không giải thích gì thêm.\n\n"
            f"Hồ sơ khách hàng: {summary}\n"
            f"Lịch sử hội thoại:\n{recent_context}\n\n"
            f"Câu hỏi mới nhất: {user_message}\n\n"
            f"Câu tìm kiếm viết lại:"
        )
        try:
            standalone_query = self.llm.invoke(rewrite_prompt).content.strip()
            print(f"[Query Rewriting] '{user_message}' ➔ '{standalone_query}'")
            return standalone_query if standalone_query else user_message
        except Exception:
            return user_message

    def _retrieve_documents(self, search_query: str) -> str:
        """Truy xuất tài liệu qua Hybrid Search (Dense + Sparse)"""
        total_in_db = self.vector_store._collection.count()

        # Nhánh 1: Dense Search (Vector)
        dense_docs = self.vector_store.similarity_search(search_query, k=5)

        # Nhánh 2: Sparse Search (BM25)
        sparse_docs = []
        if self.sparse_retriever:
            try:
                sparse_docs = self.sparse_retriever.invoke(search_query)
            except Exception:
                sparse_docs = []

        # Gộp kết quả bằng RRF
        if sparse_docs:
            docs = self._reciprocal_rank_fusion(dense_docs, sparse_docs)
        else:
            docs = dense_docs

        if not docs:
            return "HỆ THỐNG: Hiện chưa có bất động sản nào trong kho phù hợp với tiêu chí trên."

        formatted_docs = []
        # Lấy Top 2 kết quả xuất sắc nhất sau RRF
        for d in docs[:2]:
            meta = d.metadata
            info_block = (
                f" BẤT ĐỘNG SẢN THẬT:\n"
                f"- Vị trí: {meta.get('district', 'N/A')} (Thuộc phạm vi TP.HCM)\n"
                f"- Giá bán: {meta.get('price_numeric', 'N/A')} tỷ\n"
                f"- Diện tích: {meta.get('area_numeric', 'N/A')} m2\n"
                f"- Kết cấu: {meta.get('floors', 'N/A')} tầng, {meta.get('bathrooms', 'N/A')} WC\n"
                f"- Hướng nhà: {meta.get('direction', 'N/A')} | Pháp lý: {meta.get('legal_status', 'N/A')}\n"
                f"- Link URL truy cập nguồn: {meta.get('url', 'N/A')}\n"
                f"- Chi tiết mô tả: {d.page_content}"
            )
            formatted_docs.append(info_block)

        return (
            f"=== KHO DỮ LIỆU THỰC TẾ TRÙNG KHỚP (HYBRID SEARCH: DENSE + SPARSE) ===\n"
            f"Tổng kho đang vận hành: {total_in_db} chunks.\n" + "\n---\n".join(formatted_docs)
        )

    def _reciprocal_rank_fusion(self, dense_docs: List[Document], sparse_docs: List[Document], k: int = 60) -> List[Document]:
        """Thuật toán Reciprocal Rank Fusion (RRF) chuẩn toán học để gộp 2 danh sách"""
        doc_scores = {}
        
        # 1. Chấm điểm kết quả từ Sparse (BM25)
        for rank, doc in enumerate(sparse_docs):
            content = doc.page_content
            if content not in doc_scores:
                doc_scores[content] = {"doc": doc, "score": 0.0}
            doc_scores[content]["score"] += 0.5 * (1.0 / (k + rank + 1))
            
        # 2. Chấm điểm kết quả từ Dense (ChromaDB)
        for rank, doc in enumerate(dense_docs):
            content = doc.page_content
            if content not in doc_scores:
                doc_scores[content] = {"doc": doc, "score": 0.0}
            doc_scores[content]["score"] += 0.5 * (1.0 / (k + rank + 1))
            
        # 3. Sắp xếp các tài liệu theo tổng điểm RRF từ cao xuống thấp
        sorted_docs = sorted(doc_scores.values(), key=lambda x: x["score"], reverse=True)
        return [item["doc"] for item in sorted_docs]

# =========================================================================================
    def get_recent_history(self, session_id: str) -> List:
        """CHỈ lấy 2 tin nhắn gần nhất (1 Human + 1 AI), phần thông tin dài đã có trong summary"""
        messages = []
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT message FROM (
                        SELECT id, message FROM chat_history 
                        WHERE session_id = %s 
                        ORDER BY id DESC 
                        LIMIT 4
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

    def get_summary_text(self, session_id: str) -> str:
        """Lấy chuỗi tóm tắt hồ sơ khách hàng"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT summary FROM chat_summaries WHERE session_id = %s;", (session_id,))
                row = cur.fetchone()
                return row[0] if (row and row[0]) else "Chưa có thông tin ghi nhớ."

    def save_message(self, session_id: str, role: str, content: str):
        """Lưu tin nhắn đơn lẻ vào bảng chat_history chuẩn JSONB"""
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
        """Nếu >= 5 tin thì nén 2 tin đầu vào chat_summaries và xóa khỏi chat_history"""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, message FROM chat_history WHERE session_id = %s ORDER BY id ASC;",
                    (session_id,)
                )
                rows = cur.fetchall()

                # Nếu dưới 5 tin thì dừng, chưa cần nén
                if len(rows) < 5:
                    return

                # Lấy summary cũ
                cur.execute("SELECT summary FROM chat_summaries WHERE session_id = %s;", (session_id,))
                sum_row = cur.fetchone()
                current_summary = sum_row[0] if sum_row else ""

                # Lấy 2 tin cũ nhất để nén
                to_compress = rows[0:2]
                conv_text = ""
                for _, msg_json in to_compress:
                    r = msg_json.get("type", "unknown")
                    c = msg_json.get("data", {}).get("content", "")
                    conv_text += f"{r.upper()}: {c}\n"

                # Sinh bản tóm tắt mới
                prompt = (
                    f"Bạn là bộ nhớ trích xuất thông tin khách hàng bất động sản.\n"
                    f"Tóm tắt hồ sơ cũ: {current_summary if current_summary else 'Chưa có'}\n\n"
                    f"Hội thoại mới diễn ra:\n{conv_text}\n\n"
                    f"YÊU CẦU QUAN TRỌNG: Chỉ trích xuất thông tin mà HUMAN (Khách hàng) tự giới thiệu hoặc yêu cầu (Tên, Quận quan tâm, Ngân sách giá, Mục đích mua/thuê). "
                    f"TUYỆT ĐỐI KHÔNG lấy các thông số chi tiết nhà do AI tư vấn đưa vào tóm tắt. "
                    f"Viết ngắn gọn dưới 35 từ."
                )
                new_summary = self.llm.invoke(prompt).content.strip()

                # Ghi đè vào bảng chat_summaries
                cur.execute("""
                    INSERT INTO chat_summaries (session_id, summary, updated_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (session_id) 
                    DO UPDATE SET summary = EXCLUDED.summary, updated_at = CURRENT_TIMESTAMP;
                """, (session_id, new_summary))

                # Xóa 2 tin cũ nhất
                del_ids = [rows[0][0], rows[1][0]]
                cur.execute("DELETE FROM chat_history WHERE id = ANY(%s);", (del_ids,))
                conn.commit()

# =========================================================================================
    def _build_rag_chain(self):
        system_instruction = (
            "Bạn là chuyên viên tư vấn bất động sản Aura Realestate tại TP.HCM. BẮT BUỘC phản hồi 100% bằng TIẾNG VIỆT tự nhiên, TUYỆT ĐỐI CẤM sử dụng chữ Hán/tiếng Trung hay tiếng nước ngoài.\n\n"
            "GHI CHÚ HỒ SƠ KHÁCH HÀNG:\n"
            "{summary}\n\n"
            "DỮ LIỆU NHÀ ĐẤT TRONG HỆ THỐNG:\n"
            "{context}\n\n"
            "QUY TẮC PHẢN HỒI (THEO THỨ TỰ ƯU TIÊN):\n"
            "1. NẾU KHÁCH HỎI VỀ NHU CẦU / THÔNG TIN ĐÃ NÓI (ví dụ: 'tôi đang tìm gì', 'bạn nhớ tôi tìm gì không', 'tôi tên gì'): BẮT BUỘC đọc thông tin từ GHI CHÚ HỒ SƠ KHÁCH HÀNG và lịch sử để trả lời rõ ràng rằng khách đang tìm nhà ở khu vực nào, tầm giá nào.\n"
            "2. NẾU KHÁCH CHỈ CHÀO HỎI XÃ GIAO (ví dụ: 'hi', 'hello', 'chào bạn'): Chào lại ngắn gọn và hỏi khách cần tìm nhà ở khu vực nào.\n"
            "3. KHI KHÁCH HỎI TÌM NHÀ:\n"
            "   - Nếu có nhà phù hợp trong DỮ LIỆU: Báo ngay giá, diện tích, kết cấu và ưu điểm cho khách.\n"
            "   - Nếu không có nhà đúng tiêu chí: Thông báo lịch sự hiện kho chưa có căn đúng 100% yêu cầu, và gợi ý khu vực lân cận hoặc tầm giá tương đương.\n"
            "4. Câu trả lời cần tự nhiên, xưng hô lịch sự, ngắn gọn và trọng tâm."
        )

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_instruction),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_message}")
        ])

        return prompt_template | self.llm | StrOutputParser()

    def ask_rag_bot(self, user_message: str, session_id: str = "default_session") -> str:
        """Lấy ngữ cảnh RAG + Memory nén và sinh phản hồi"""
        try:
            # 1. Lấy lịch sử gần nhất và hồ sơ tóm tắt từ database
            chat_history = self.get_recent_history(session_id)
            summary = self.get_summary_text(session_id)

            # 2. Viết lại câu query thông minh (kết hợp History + Request + Summary)
            standalone_search_query = self._condense_query(
                user_message=user_message,
                chat_history=chat_history,
                summary=summary
            )

            # 3. Dùng câu query đã viết lại để truy xuất tài liệu trong RAG
            context = self._retrieve_documents(standalone_search_query)

            # 4. Gửi vào LLM sinh câu trả lời
            response = self.rag_chain.invoke({
                "summary": summary,
                "context": context,
                "chat_history": chat_history,
                "user_message": user_message
            })

            return response
        except Exception as e:
            return f"Lỗi xử lý hệ thống RAG: {str(e)}"

    async def astream_rag_bot(self, user_message: str, session_id: str = "default_session"):
        """Luồng sinh câu trả lời Streaming bất đồng bộ (Yield từng token qua SSE)"""
        try:
            # 1. Lấy lịch sử và hồ sơ tóm tắt từ database
            chat_history = self.get_recent_history(session_id)
            summary = self.get_summary_text(session_id)

            # 2. Viết lại câu query thông minh
            standalone_search_query = self._condense_query(
                user_message=user_message,
                chat_history=chat_history,
                summary=summary
            )

            # 3. Truy xuất tài liệu RAG
            context = self._retrieve_documents(standalone_search_query)

            # 4. Stream từng token từ vLLM qua LangChain astream
            async for chunk in self.rag_chain.astream({
                "summary": summary,
                "context": context,
                "chat_history": chat_history,
                "user_message": user_message
            }):
                if chunk:
                    yield chunk

        except Exception as e:
            yield f"\n[Lỗi hệ thống Streaming: {str(e)}]"
                   
chatbot_service = ChatbotService()