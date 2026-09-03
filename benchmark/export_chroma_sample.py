# D:\DA\aura-realestate\export_chroma_sample.py
import urllib.request
import json
import random
import os
import sys

# Dam bao in tieng Viet UTF-8 chuan tren Windows Terminal
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

CHROMA_BASE_URL = "http://127.0.0.1:8001/api/v1"
OUTPUT_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_sample_50_items.json"))

print("=" * 75)
print("DANG KET NOI VAO CHROMADB (PORT 8001) QUA REST API TRUC TIEP...")
print("=" * 75)

try:
    # 1. Lay danh sach collections
    req = urllib.request.Request(f"{CHROMA_BASE_URL}/collections")
    with urllib.request.urlopen(req, timeout=10) as res:
        collections = json.loads(res.read().decode("utf-8"))
    
    target_col = None
    for col in collections:
        if col.get("name") == "realestate_collection":
            target_col = col
            break
            
    if not target_col:
        print("[LOI] Khong tim thay Collection 'realestate_collection' trong ChromaDB!")
        print(f"[DEBUG] Danh sach Collection hien co: {[c.get('name') for c in collections]}")
        sys.exit(1)

    col_id = target_col.get("id")
    print(f"[INFO] Da tim thay Collection: 'realestate_collection' (ID: {col_id})")

    # 2. Lay du lieu items tu collection
    get_payload = json.dumps({"limit": 500}).encode("utf-8")
    req_items = urllib.request.Request(
        f"{CHROMA_BASE_URL}/collections/{col_id}/get",
        data=get_payload,
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req_items, timeout=30) as res:
        raw_data = json.loads(res.read().decode("utf-8"))

    ids = raw_data.get("ids", [])
    docs = raw_data.get("documents", [])
    metas = raw_data.get("metadatas", [])

    print(f"[INFO] Da doc duoc {len(ids)} ban ghi tu ChromaDB.")

    # 3. Khu trung lap theo house_id de lay cac can nha doc nhat
    unique_houses = []
    seen_ids = set()

    for item_id, doc_text, meta in zip(ids, docs, metas):
        meta_dict = meta if isinstance(meta, dict) else {}
        h_id = meta_dict.get("house_id", item_id)
        if h_id not in seen_ids:
            seen_ids.add(h_id)
            unique_houses.append({
                "id": item_id,
                "document": doc_text,
                "metadata": meta_dict
            })

    # 4. Lay mau ngau nhien 50 can nha
    random.seed(42)
    sample_50 = random.sample(unique_houses, min(50, len(unique_houses)))

    # 5. Ghi ra file JSON dung chuan ChromaDB
    with open(OUTPUT_FILE, mode="w", encoding="utf-8") as f:
        json.dump(sample_50, f, ensure_ascii=False, indent=2)

    print(f"[THANH CONG] Da luu {len(sample_50)} items ChromaDB mau vao file:")
    print(f"-> {OUTPUT_FILE}")
    print("=" * 75)

except Exception as e:
    print(f"[LOI KET NOI CHROMADB]: {e}")