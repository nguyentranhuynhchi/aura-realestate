# D:\DA\aura-realestate\test_streaming_benchmark.py
import urllib.request
import json
import time
import sys

# Đảm bảo in tiếng Việt chuẩn trên Windows Terminal
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

STREAM_URL = "http://127.0.0.1:8000/api/v1/chat/stream"

print("=" * 65)
print("🚀 BẮT ĐẦU KIỂM THỬ VÀ ĐO ĐẠC ĐỘ TRỄ STREAMING (SSE)")
print(f"• Endpoint: {STREAM_URL}")
print("=" * 65)

def run_streaming_test(question: str):
    print(f"\n👤 [USER]: {question}\n")
    print("🤖 [AURA BOT]: ", end="", flush=True)

    payload = {
        "message": question,
        "session_id": "test_streaming_session"
    }

    req = urllib.request.Request(
        STREAM_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    t_start = time.perf_counter()
    t_first_token = None
    token_timestamps = []
    received_text = []

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            for line in response:
                line_str = line.decode("utf-8").strip()
                if not line_str or not line_str.startswith("data:"):
                    continue
                
                data_content = line_str[5:].strip()
                if data_content == "[DONE]":
                    break

                try:
                    data_json = json.loads(data_content)
                    token = data_json.get("token", "")
                    
                    # Bắt mốc thời gian của Chữ Đầu Tiên (TTFT)
                    t_now = time.perf_counter()
                    if t_first_token is None:
                        t_first_token = t_now
                    
                    token_timestamps.append(t_now)
                    received_text.append(token)
                    
                    # In trực tiếp token ra màn hình theo thời gian thực
                    print(token, end="", flush=True)
                except Exception:
                    pass

        t_end = time.perf_counter()
        
        # TÍNH TOÁN CÁC CHỈ SỐ ĐO
        ttft_s = (t_first_token - t_start) if t_first_token else 0
        total_time_s = t_end - t_start
        total_tokens = len(received_text)
        
        # Tính TPOT (Thời gian trung bình giữa 2 token liên tiếp)
        if len(token_timestamps) > 1:
            diffs = [token_timestamps[i] - token_timestamps[i-1] for i in range(1, len(token_timestamps))]
            avg_tpot_ms = (sum(diffs) / len(diffs)) * 1000
        else:
            avg_tpot_ms = 0

        generation_speed = total_tokens / (t_end - t_first_token) if (t_first_token and (t_end > t_first_token)) else 0

        print("\n\n" + "-" * 65)
        print("📊 KẾT QUẢ ĐO LƯỜNG ĐỘ TRỄ STREAMING:")
        print("-" * 65)
        print(f"• TTFT (Thời gian chờ chữ đầu tiên)  : {ttft_s:.3f} giây ({ttft_s*1000:.1f} ms)")
        print(f"• TPOT (Thời gian sinh mỗi token)   : {avg_tpot_ms:.1f} ms/token")
        print(f"• Tốc độ sinh từ thực tế (Speed)    : {generation_speed:.1f} tokens/giây")
        print(f"• Tổng số token đã sinh ra          : {total_tokens} tokens")
        print(f"• Tổng thời gian hoàn thành cả câu  : {total_time_s:.2f} giây")
        print("-" * 65)

    except Exception as e:
        print(f"\n❌ Lỗi trong quá trình stream: {e}")

if __name__ == "__main__":
    test_question = "Tôi muốn tìm nhà ở Quận 9 tầm 15 tỷ diện tích rộng có sổ hồng riêng"
    run_streaming_test(test_question)