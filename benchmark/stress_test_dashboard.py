# D:\DA\aura-realestate\stress_test_dashboard.py
import urllib.request
import json
import time
import sys
import statistics
from concurrent.futures import ThreadPoolExecutor

# Đảm bảo hiển thị tiếng Việt chuẩn trên Windows Terminal
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

BACKEND_URL = "http://127.0.0.1:8000/api/v1/chat"

# CẤU HÌNH ÉP TẢI KỊCH KHUNG (SATURATION STRESS TEST)
TOTAL_REQUESTS = 30   # Tổng số request kiểm thử
CONCURRENCY = 16      # Bắn đồng thời 16 luồng cùng lúc để ép bão hòa 686 GPU Blocks

print("=" * 60)
print(f"🔥 BẮT ĐẦU STRESS TEST ÉP BÃO HÒA KỊCH KHUNG GPU KV CACHE")
print(f"• Cấu hình vLLM Engine : 686 GPU Blocks | Max Context: 2048")
print(f"• Luồng bắn đồng thời  : {CONCURRENCY} luồng song song")
print(f"• Tổng số requests     : {TOTAL_REQUESTS} câu hỏi chi tiết")
print(f"👉 Mở Grafana Dashboard: http://localhost:3001")
print("=" * 60)

# Mẫu câu hỏi dài và chi tiết để tiêu hao nhiều GPU Blocks cho mỗi request
LONG_PROMPT_TEMPLATE = (
    "Tôi là nhà đầu tư bất động sản đang có tài chính khoảng 15 tỷ đồng. "
    "Tôi cần bạn tư vấn và phân tích thật chi tiết các căn nhà tại khu vực Quận 9 hoặc TP. Thủ Đức, "
    "yêu cầu diện tích từ 80m2 trở lên, đường trước nhà rộng thoáng cho ô tô, có sổ hồng riêng pháp lý rõ ràng. "
    "Hãy so sánh ưu nhược điểm về tiềm năng tăng giá và khả năng cho thuê của mã căn bất động sản số {idx}."
)

def send_chat(idx: int):
    t0 = time.perf_counter()
    payload = {
        "message": LONG_PROMPT_TEMPLATE.format(idx=idx),
        "session_id": f"saturation_test_{idx}"
    }
    req = urllib.request.Request(
        BACKEND_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=300)
        dur = time.perf_counter() - t0
        print(f"⚡ [Xong {idx+1:02d}/{TOTAL_REQUESTS:02d}] Phản hồi sau {dur:.2f}s")
        return {"success": True, "duration": dur}
    except Exception as e:
        dur = time.perf_counter() - t0
        print(f"❌ [Lỗi {idx+1:02d}/{TOTAL_REQUESTS:02d}]: {e}")
        return {"success": False, "duration": dur, "error": str(e)}

if __name__ == "__main__":
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        results = list(executor.map(send_chat, range(TOTAL_REQUESTS)))
    
    total_time = time.perf_counter() - start
    success_res = [r for r in results if r.get("success")]
    dur_list = [r["duration"] for r in success_res]
    
    print("\n" + "=" * 60)
    print("📊 KẾT QUẢ TEST BÃO HÒA GPU THỰC NGHIỆM")
    print("=" * 60)
    print(f"• Tỷ lệ thành công          : {len(success_res)}/{TOTAL_REQUESTS} ({len(success_res)/TOTAL_REQUESTS*100:.1f}%)")
    print(f"• Tổng thời gian đo         : {total_time:.2f} giây")
    print(f"• Request Throughput tổng   : {len(success_res)/total_time:.2f} reqs/giây")
    if dur_list:
        print(f"• Độ trễ trung bình (Mean)  : {statistics.mean(dur_list):.2f} giây")
        print(f"• Độ trễ trung vị (P50)     : {statistics.median(dur_list):.2f} giây")
    print("=" * 60)
    print("👉 Hãy quan sát Grafana: Đồng hồ GPU KV Cache và Throughput sẽ chạm đỉnh bão hòa!")