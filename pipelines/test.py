import os
import sys
import chromadb

# Định nghĩa đường dẫn tới kho ChromaDB thực tế của ní
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "backend", "chromadb"))

def debug_query(collection, query_text, n_results=3):
    print(f"\n[DEBUG QUERY] Câu hỏi: {query_text}")
    results = collection.query(query_texts=[query_text], n_results=n_results)
    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]

    print(f"[DEBUG] Số lượng docs trả về: {len(documents)}")
    for idx, (doc, dist) in enumerate(zip(documents, distances), 1):
        preview = " ".join(doc.splitlines())[:350]
        print(f"[DEBUG] {idx}. distance={dist:.4f}")
        print(preview)
        print("-" * 60)


def main():
    print(f"\n--- KẾT NỐI KHO VECTOR DB TẠI: {CHROMA_DB_DIR} ---")
    
    if not os.path.exists(CHROMA_DB_DIR):
        print("[ERROR] Không tìm thấy thư mục ChromaDB. Hãy chắc chắn pipeline RAG đã từng chạy thành công.")
        return

    # 1. Kết nối tới Persistent Client
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    
    # 2. Lấy bộ sưu tập dữ liệu bất động sản
    try:
        collection = chroma_client.get_collection(name="realestate_collection")
    except Exception as e:
        print(f"[ERROR] Không tìm thấy collection 'realestate_collection'. Lỗi: {e}")
        return

    # 3. Đếm tổng số lượng chunks đang có trong kho
    total_chunks = collection.count()
    print(f"[INFO] Tổng số lượng đoạn văn bản (Chunks) hiện có trong DB: {total_chunks}")

    if total_chunks == 0:
        print("[INFO] Kho đang trống trơn, chưa có dữ liệu.")
        return

    # 4. Bóc thử 5 đoạn văn bản đầu tiên ra xem "RAG học được những gì"
    print("\n=================================================================")
    print("🔍 BÓC THỬ 5 CHUNKS TRONG CHROMADB XEM NGỮ CẢNH RAG:")
    print("=================================================================\n")
    
    # Lấy dữ liệu mẫu từ SQLite nền của ChromaDB
    results = collection.get(limit=5)

    for i in range(len(results['ids'])):
        print(f"📌 [CHUNK {i+1}] | ID Hệ thống: {results['ids'][i]}")
        print(f"🏠 ID Nhà gốc: {results['metadatas'][i].get('house_id', 'N/A')}")
        print(f"💰 Giá: {results['metadatas'][i].get('price', 'N/A')} tỷ | 📐 Diện tích: {results['metadatas'][i].get('area', 'N/A')} m2")
        print(f"🔗 Link: {results['metadatas'][i].get('url', 'N/A')}")
        print("-" * 50)
        print(f"📝 Nội dung văn bản cấu trúc (AI đọc đoạn này để làm RAG):\n")
        print(results['documents'][i])
        print("\n" + "="*65 + "\n")

    debug_query(collection, "căn hộ 2 phòng ngủ giá tốt")

if __name__ == "__main__":
    main()