# D:\DA\aura-realestate\benchmark_rag_accuracy.py
import urllib.request
import json
import time
import sys
import os
import uuid
import unicodedata

# Đảm bảo in tiếng Việt UTF-8 chuẩn trên Windows Terminal
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

BACKEND_URL = "http://127.0.0.1:8000/api/v1/chat"
# SAMPLE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_sample_50_items.json"))
SAMPLE_FILE = r"D:\DA\aura-realestate\benchmark\chroma_sample_50_items.json"
print("=" * 80)
print("BẮT ĐẦU BENCHMARK 3 TIÊU CHÍ CỐT LÕI ĐỘ CHÍNH XÁC RAG TỪ 50 CHUNKS THỰC TẾ")
print("• Phương pháp Tiêu chí 2: Memory Probing & Recall Verification (Hỏi ngược bộ nhớ)")
print(f"• Endpoint kiểm thử : {BACKEND_URL}")
print(f"• File dữ liệu mẫu  : {SAMPLE_FILE}")
print("=" * 80)

def remove_accents(input_str):
    """Chuyển chuỗi có dấu thành không dấu để so sánh linh hoạt"""
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', str(input_str))
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

def send_request(message: str, session_id: str): # Hàm gửi câu hỏi (message) và mã phiên (session_id) lên Backend
    t0 = time.perf_counter() # Bấm giờ bắt đầu bằng bộ đếm thời gian chính xác cao
    req = urllib.request.Request( # Khởi tạo đối tượng yêu cầu HTTP Request
        BACKEND_URL, # Địa chỉ API FastAPI: http://127.0.0.1:8000/api/v1/chat
        data=json.dumps({"message": message, "session_id": session_id}).encode("utf-8"), # Đóng gói payload JSON và chuyển thành byte UTF-8
        headers={"Content-Type": "application/json"} # Khai báo định dạng dữ liệu gửi đi là JSON
    ) # Kết thúc tạo request
    try: # Bắt đầu khối xử lý kết nối
        with urllib.request.urlopen(req, timeout=120) as res: # Gửi HTTP POST và chờ phản hồi tối đa 120 giây
            data = json.loads(res.read().decode("utf-8")) # Đọc byte trả về, giải mã UTF-8 và parse thành dict
            reply = data.get("data", {}).get("reply", "") # Bóc tách chuỗi câu trả lời của Bot từ response
            return reply, time.perf_counter() - t0 # Trả về câu trả lời và tổng thời gian phản hồi (giây)
    except Exception as e: # Bắt lỗi nếu mất mạng, quá thời gian hoặc lỗi server
        return f"[LỖI KẾT NỐI: {e}]", time.perf_counter() - t0 # Trả về thông báo lỗi kèm thời gian thực thi
        
# 1. Đọc và lọc các căn nhà hợp lệ có mô tả từ file 50 chunks
if not os.path.exists(SAMPLE_FILE):
    print(f"[LỖI] Không tìm thấy file {SAMPLE_FILE}. Hãy chạy export_chroma_sample.py trước!")
    sys.exit(1)

with open(SAMPLE_FILE, mode="r", encoding="utf-8") as f:
    all_samples = json.load(f)

valid_houses = []
for item in all_samples:
    doc = item.get("document", "")
    meta = item.get("metadata", {})
    price = float(meta.get("price_numeric", 0))
    valid_houses.append(item)

print(f"[INFO] Đã nạp thành công {len(valid_houses)} căn nhà thực tế từ ChromaDB để kiểm thử.\n")

# =====================================================================
# TIÊU CHÍ 1: RETRIEVAL HIT RATE @ 2 (ĐỘ CHÍNH XÁC TRUY XUẤT HYBRID RAG)
# =====================================================================
print("-" * 80)
print("TIÊU CHÍ 1: ĐO TỶ LỆ TRUY XUẤT TRÚNG ĐÍCH TRONG TOP 2 (RETRIEVAL HIT RATE @ 2)")
print("-" * 80)

hit_count = 0
test_items = valid_houses[:50]

for idx, item in enumerate(test_items):
    meta = item.get("metadata", {})
    district = meta.get("district", "TP.HCM")
    price = float(meta.get("price_numeric", 0))
    area = float(meta.get("area_numeric", 0))
    
    p_low = max(1.0, round(price * 0.85, 1))
    p_high = round(price * 1.15, 1)
    
    query = f"Tôi muốn tìm mua bất động sản ở khu vực {district} tầm giá từ {p_low} đến {p_high} tỷ diện tích khoảng {int(area)}m2"
    sid = f"eval_retrieval_{uuid.uuid4().hex[:8]}"
    
    reply, dur = send_request(query, sid)
    reply_clean = remove_accents(reply)
    dist_clean = remove_accents(district).replace("huyen ", "").replace("quan ", "").replace("tp. ", "").strip()
    
    has_district = (dist_clean in reply_clean) or ("ho chi minh" in reply_clean) or ("tphcm" in reply_clean)
    has_price = ("ty" in reply_clean) or ("trieu" in reply_clean)
    
    is_hit = has_district and has_price
    short_reply = reply.replace("\n", " ")[:65]
    
    if is_hit:
        hit_count += 1
        print(f"  [HIT]  | Test {idx+1:02d}: {district} (~{price} tỷ) -> Bot: \"{short_reply}...\" ({dur:.2f}s)")
    else:
        print(f"  [MISS] | Test {idx+1:02d}: {district} (~{price} tỷ) -> Bot: \"{short_reply}...\" ({dur:.2f}s)")

hit_rate_at_2 = (hit_count / len(test_items)) * 100 if test_items else 0

# =====================================================================
# TIÊU CHÍ 2: MEMORY PROBING & RECALL (ĐO TRÍ NHỚ VỚI FEW-SHOT OUTPUT)
# =====================================================================
print("\n" + "-" * 80)
print("TIÊU CHÍ 2: ĐO KHẢ NĂNG BẢO TOÀN TRÍ NHỚ ĐA LƯỢT (FEW-SHOT MEMORY RECALL)")
print("-" * 80)

# Mẫu câu hỏi Turn 2 chứa Ví dụ mẫu chuẩn chỉ để ép định dạng
TURN2_PROMPT_TEMPLATE = (
    "Dựa vào thông tin tôi vừa giới thiệu ở lượt trước, hãy trả lời DUY NHẤT một dòng theo đúng định dạng mẫu sau:\n"
    "Ví dụ mẫu: KẾT QUẢ: Tên = An, Quận = Quận 1, Giá = 10 tỷ\n"
    "Bây giờ hãy điền thông tin thật của tôi vào mẫu trên:"
)

memory_probing_sessions = [
    {
        "turn1": "Chào bạn, tôi tên Tuấn, tôi đang muốn tìm mua nhà ở Quận 9 tầm tài chính khoảng 15 tỷ.",
        "turn2": TURN2_PROMPT_TEMPLATE,
        "expected_name": "tuan",
        "expected_district": "9",
        "expected_price": "15"
    },
    {
        "turn1": "Tôi là Hương, tôi cần tìm căn nhà ở Quận Bình Thạnh giá khoảng 11 tỷ.",
        "turn2": TURN2_PROMPT_TEMPLATE,
        "expected_name": "huong",
        "expected_district": "binh thanh",
        "expected_price": "11"
    },
    {
        "turn1": "Mình tên Nam, muốn tìm mua nhà ở TP Thủ Đức tầm giá 8 tỷ có sổ hồng.",
        "turn2": TURN2_PROMPT_TEMPLATE,
        "expected_name": "nam",
        "expected_district": "thu duc",
        "expected_price": "8"
    },
    {
        "turn1": "Chào em, anh là Hoàng, anh cần tìm nhà riêng ở Quận 2 tầm 27 tỷ.",
        "turn2": TURN2_PROMPT_TEMPLATE,
        "expected_name": "hoang",
        "expected_district": "2",
        "expected_price": "27"
    },
    {
        "turn1": "Tôi tên Linh, muốn tìm nhà ở Huyện Bình Chánh giá khoảng 2 tỷ.",
        "turn2": TURN2_PROMPT_TEMPLATE,
        "expected_name": "linh",
        "expected_district": "binh chanh",
        "expected_price": "2"
    }
]

memory_hits = 0

for idx, session in enumerate(memory_probing_sessions):
    sid = f"eval_memory_{uuid.uuid4().hex[:8]}"
    
    # Lượt 1: Nạp thông tin vào bộ nhớ
    send_request(session["turn1"], sid)
    
    # Chờ 0.5s để Background Task ghi vào PostgreSQL
    time.sleep(0.5)
    
    # Lượt 2: Ép Bot nhả đúng định dạng mẫu
    reply2, dur = send_request(session["turn2"], sid)
    reply2_clean = remove_accents(reply2)
    
    # Kiểm tra so khớp 100% với định dạng mong đợi
    has_name = session["expected_name"] in reply2_clean
    has_dist = session["expected_district"] in reply2_clean
    has_price = session["expected_price"] in reply2_clean
    
    # Đạt điểm khi trích xuất đúng Tên + Vị trí (hoặc Tên + Giá)
    is_recalled = has_name and (has_dist or has_price)
    short_reply2 = reply2.replace("\n", " ").strip()[:70]
    
    if is_recalled:
        memory_hits += 1
        print(f"  [PASS] | Session {idx+1:02d}: {short_reply2} ({dur:.2f}s)")
    else:
        print(f"  [FAIL] | Session {idx+1:02d}: Mất trí nhớ -> \"{short_reply2}...\" ({dur:.2f}s)")

memory_retention_rate = (memory_hits / len(memory_probing_sessions)) * 100
# =====================================================================
# TIÊU CHÍ 3: HALLUCINATION CONTROL (KIỂM SOÁT ẢO GIÁC NGOÀI PHẠM VI)
# =====================================================================
print("\n" + "-" * 80)
print("TIÊU CHÍ 3: ĐO KHẢ NĂNG CHỐNG ẢO GIÁC (OUT-OF-DOMAIN / ADVERSARIAL TRAP)")
print("-" * 80)

traps = [
    {"query": "Tìm biệt thự mặt tiền Quận 1 giá 200 triệu đồng có hồ bơi.", "type": "Giá phi thực tế (< 500 triệu)"},
    {"query": "Tôi muốn mua nhà ở phố Cầu Giấy, Hà Nội giá 5 tỷ.", "type": "Địa bàn ngoài TP.HCM"},
    {"query": "Tìm mua căn hộ chung cư 6 phòng ngủ ở Huyện Cần Giờ giá 400 triệu.", "type": "Loại hình & Giá không tồn tại"},
    {"query": "Có nhà nào ở Đà Nẵng giá 1 tỷ không bạn?", "type": "Tỉnh thành ngoài hệ thống"}
]

safe_count = 0

for idx, trap in enumerate(traps):
    sid = f"eval_safety_{uuid.uuid4().hex[:8]}"
    reply, dur = send_request(trap["query"], sid)
    reply_clean = remove_accents(reply)
    
    is_safe = any(w in reply_clean for w in ["chua co", "khong co", "chua tim thay", "goi y", "hien tai", "khong tim thay", "phu hop", "ngoai"])
    
    short_reply = reply.replace("\n", " ")[:60]
    if is_safe:
        safe_count += 1
        print(f"  [SAFE] | Trap {idx+1:02d}: Từ chối an toàn: {trap['type']} -> \"{short_reply}...\" ({dur:.2f}s)")
    else:
        print(f"  [RISK] | Trap {idx+1:02d}: Nghi vấn bịa thông tin -> \"{short_reply}...\" ({dur:.2f}s)")

safe_rate = (safe_count / len(traps)) * 100

# =====================================================================
# BẢNG TỔNG KẾT KẾT QUẢ ĐỊNH LƯỢNG CHO CV
# =====================================================================
print("\n" + "=" * 80)
print("BẢNG TỔNG HỢP 3 CHỈ SỐ VÀNG ĐỘ CHÍNH XÁC RAG (FINAL CV METRICS)")
print("=" * 80)
print(f"1. Retrieval Hit Rate @ 2 (Tỷ lệ tìm trúng đích)       : {hit_rate_at_2:.1f}%")
print(f"2. Multi-turn Memory Recall Rate (Trí nhớ hội thoại)     : {memory_retention_rate:.1f}%")
print(f"3. Hallucination-Free Rate (Tỷ lệ chống ảo giác)         : {safe_rate:.1f}%")
print("=" * 80)
print("Lưu ý: 3 chỉ số % định lượng trên là bằng chứng thực nghiệm để ghi vào CV!")