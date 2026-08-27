# === FIX LỖI SQLITE3 CHO CHROMADB ===
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
# =====================================

import os
import sys
import re
import pandas as pd
import numpy as np
import chromadb
from chromadb.utils import embedding_functions

# Đường dẫn cấu hình hệ thống
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_NEW_DATA = os.path.abspath(os.path.join(CURRENT_DIR, "..", "data", "raw", "new_data.csv"))

# =========================================================================
# CÁC HÀM TRÍCH XUẤT LÀM SẠCH TỪ FILE 1_DATA_PREPROCESSING.PY
# =========================================================================
def clean_price(price_str):
    if pd.isna(price_str) or 'thỏa thuận' in str(price_str).lower():
        return 0.0
    try:
        s = str(price_str).strip().lower().replace(',', '.')
        m = re.search(r'([\d.]+)\s*tỷ', s)
        if m:
            return float(m.group(1))
        m = re.search(r'([\d.]+)\s*triệu', s)
        if m:
            return float(m.group(1)) / 1000.0
        m = re.search(r'([\d.]+)', s)
        return float(m.group(1)) if m else 0.0
    except ValueError:
        # Gặp chuỗi dị dạng thì trả về 0.0 để loại bỏ an toàn
        return 0.0

def clean_area(area_str):
    if pd.isna(area_str):
        return 0.0
    try:
        s = str(area_str).strip().lower().replace(',', '.')
        m = re.search(r'([\d.]+)', s)
        return float(m.group(1)) if m else 0.0
    except ValueError:
        # Bọc lỗi dứt điểm cho con hàng '4.335.7'
        return 0.0

def clean_to_integer(val):
    if pd.isna(val):
        return 0
    m = re.search(r'(\d+)', str(val))
    return int(m.group(1)) if m else 0

def extract_district(address):
    if pd.isna(address):
        return 'Không rõ'
    addr = str(address).lower().strip()
    if 'thủ đức' in addr: return 'TP. Thủ Đức'
    if 'bình chánh' in addr: return 'Huyện Bình Chánh'
    if 'cần giờ' in addr: return 'Huyện Cần Giờ'
    if 'củ chi' in addr: return 'Huyện Củ Chi'
    if 'hóc môn' in addr: return 'Huyện Hóc Môn'
    if 'nhà bè' in addr: return 'Huyện Nhà Bè'
    if 'bình thạnh' in addr or 'q. bình' in addr: return 'Quận Bình Thạnh'
    if 'bình tân' in addr: return 'Quận Bình Tân'
    if 'gò vấp' in addr or 'q. gò' in addr: return 'Quận Gò Vấp'
    if 'phú nhuận' in addr or 'q. phú' in addr: return 'Quận Phú Nhuận'
    if 'tân bình' in addr: return 'Quận Tân Bình'
    if 'tân phú' in addr: return 'Quận Tân Phú'
    match_num = re.search(r'(?:quận|q\.?)\s*([0-9]+)', addr)
    if match_num:
        num = int(match_num.group(1))
        if 1 <= num <= 12: return f"Quận {num}"
    return 'Không rõ'

def clean_legal(legal):
    if pd.isna(legal): return 'Không rõ'
    legal = str(legal).lower().strip()
    if any(k in legal for k in ['sổ hồng', 'sổ đỏ', 'đã có sổ', 'sổ riêng', 'chính chủ', 'hoàn công']):
        return 'Có Sổ'
    elif any(k in legal for k in ['hợp đồng mua bán', 'hdmb', 'chờ sổ', 'giấy tay', 'đang chờ']):
        return 'Chưa Sổ / HDMB'
    return 'Không rõ'

def clean_direction(direction):
    if pd.isna(direction): return 'Không rõ'
    d = str(direction).lower().replace('-', ' ').strip()
    for v in ['đông nam', 'đông bắc', 'tây nam', 'tây bắc', 'đông', 'tây', 'nam', 'bắc']:
        if v in " ".join(d.split()):
            return v.title()
    return 'Không rõ'

def chunk_text_pure_python(text, chunk_size=600, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
    return chunks

def main():
    mode = "daily"
    if len(sys.argv) > 1:
        mode = sys.argv[1] 
        
    if mode == "init_all":
        DATA_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "data", "raw", "houses_raw.csv"))
        print(f"\n--- [RAG INIT] ĐANG TÁCH CẤU TRÚC VÀ NẠP TOÀN BỘ KHO DATA ---")
    else:
        DATA_PATH = RAW_NEW_DATA
        print(f"\n--- [RAG DAILY] ĐANG TÁCH CẤU TRÚC VÀ ĐẨY FILE NEW_DATA VÀO CHROMADB ---")

    if not os.path.exists(DATA_PATH):
        print(f"[WARNING] Không tìm thấy file tại {DATA_PATH}.")
        return

    df = pd.read_csv(DATA_PATH)
    if df.empty:
        print("[INFO] Không có dữ liệu để nạp.")
        return

    chroma_host = os.environ.get("CHROMA_HOST", "localhost")
    # lấy biến HROMA_HOST: khi ccos docker
    # lấy biến localhost: khi chạy trực tiếp trên máy
    chroma_port = int(os.environ.get("CHROMA_PORT", 8001))
    # lấy cổng HROMA_HOST: khi ccos docker
    # lấy cổng 8001: khi chạy trực tiếp trên máy
    chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
    # khởi tạo kết nối client - Server qua giao thức HTTP thay vì trực tiếp ghi đè băng PersistentClient
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = chroma_client.get_or_create_collection(name="realestate_collection", embedding_function=sentence_transformer_ef)
    # lấy hoặc tạo Collection

    documents = []
    metadatas = []
    ids = []

    print("[PROCESS] Đang bóc tách dữ liệu sạch thành metadata định lượng...")
    for idx, row in df.iterrows():
        raw_id = str(row.get('id', f"raw_{idx}"))
        
        # 1. Trích xuất sạch các trường phục vụ bộ lọc
        price_num = float(clean_price(row.get('price_raw')))
        area_num = float(clean_area(row.get('area_raw')))
        district_str = str(extract_district(row.get('address_raw')))
        floors_num = int(clean_to_integer(row.get('floors')))
        bathrooms_num = int(clean_to_integer(row.get('bathrooms')))
        direction_str = str(clean_direction(row.get('house_direction')))
        legal_str = str(clean_legal(row.get('legal_status')))
        url_str = str(row.get('url', ''))

        # Lọc bỏ các dòng bị nhiễu nặng y như logic file 1 trước khi đẩy vào RAG
        if district_str == 'Không rõ' or price_num <= 0 or area_num <= 0:
            continue

        # 2. Xây dựng chuỗi văn bản thuần túy (Chỉ chứa từ ngữ, loại bỏ số liệu gây nhiễu vector)
        pure_doc_text = (
            f"Bán nhà riêng tại {district_str}. "
            f"Khu vực bất động sản tọa lạc quanh vị trí {str(row.get('address_raw',''))}. "
            f"Thông tin mô tả từ chủ nhà: {str(row.get('description', ''))}"
        )
        
        text_chunks = chunk_text_pure_python(pure_doc_text, chunk_size=600, overlap=100)
        
        for chunk_idx, chunk_text in enumerate(text_chunks):
            documents.append(chunk_text)
            # Tách dữ liệu có cấu trúc cực rộng để làm bộ lọc vây ráp
            metadatas.append({
                "house_id": raw_id,
                "price_numeric": price_num,
                "area_numeric": area_num,
                "district": district_str,
                "floors": floors_num,
                "bathrooms": bathrooms_num,
                "direction": direction_str,
                "legal_status": legal_str,
                "url": url_str
            })
            ids.append(f"chunk_{raw_id}_{chunk_idx}")

    if documents:
        seen_ids = set()
        clean_ids, clean_documents, clean_metadatas = [], [], []

        for i, chunk_id in enumerate(ids):
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                clean_ids.append(chunk_id)
                clean_documents.append(documents[i])
                clean_metadatas.append(metadatas[i])

        print(f"[VECTOR DB] Đang đồng bộ hóa {len(clean_ids)} chunks sạch xuống đĩa vật lý...")
        collection.upsert(
            ids=clean_ids,
            documents=clean_documents,
            metadatas=clean_metadatas
        )
        print("[SUCCESS] Đã ghi và đồng bộ Metadata thành công xuống local vật lý!")

if __name__ == "__main__":
    main()