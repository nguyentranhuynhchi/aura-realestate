import chromadb

# Vì Docker đang chạy Chroma ở cổng 8000 và map ra ngoài 8001
# Nên ta dùng HttpClient kết nối vào localhost:8001 cho an toàn, không sợ khóa file.
print("[INFO] Đang kết nối tới ChromaDB qua Docker (Port 8001)...")
try:
    chroma_client = chromadb.HttpClient(host="localhost", port=8001)
    
    # Lấy danh sách collections
    existing_collections = chroma_client.list_collections()
    print(f"\n[STATUS] Các phòng dữ liệu (Collections) hiện có:")
    
    for col_item in existing_collections:
        # ChromaDB tùy phiên bản sẽ trả về chuỗi tên hoặc object
        col_name = col_item if isinstance(col_item, str) else col_item.name
        col_obj = chroma_client.get_collection(name=col_name)
        print(f" - Tên: {col_name} (Đang chứa: {col_obj.count()} chunks)")

    # ---------------------------------------------------------
    # ĐOẠN LẤY THỬ VÀI CHUNK RA ĐỂ XEM
    # ---------------------------------------------------------
    collection_name = "realestate_collection"
    
    print(f"\n--- [PEEK DATA] Lấy thử 2 chunks từ '{collection_name}' ---")
    collection = chroma_client.get_collection(name=collection_name)
    
    # Hàm peek(limit=N) sẽ lấy nhanh N bản ghi đầu tiên trong DB
    peek_data = collection.peek(limit=2)
    
    if peek_data and peek_data.get('documents') and len(peek_data['documents']) > 0:
        for i in range(len(peek_data['documents'])):
            print(f"\n🔹 Chunk {i+1} | ID: {peek_data['ids'][i]}")
            print(f"   + Metadata: {peek_data['metadatas'][i]}")
            # In ra 200 ký tự đầu tiên của nội dung cho đỡ bị dài dòng trôi mất màn hình
            doc_content = peek_data['documents'][i]
            preview_text = doc_content[:200].replace('\n', ' ')
            print(f"   + Nội dung: {preview_text}...") 
    else:
        print("[TRỐNG] Collection này hiện chưa có dữ liệu nào (hoặc đọc lỗi)!")

except Exception as e:
    print(f"\n[LỖI] Không thể kết nối hoặc đọc dữ liệu. Chi tiết: {e}")