# Tài nguyên Đa phương tiện Dự án Aura Real Estate

Thư mục này chứa toàn bộ hình ảnh, ảnh động GIF preview và video minh họa hoạt động của hệ thống Aura Real Estate.

## 1. Cấu trúc Thư mục

```text
docs/assets/
├── gifs/                   # Ảnh động GIF preview (<= 2MB, 800px width, 10-12 fps)
│   ├── chatbot-rag-preview.gif
│   ├── grafana-vllm-preview.gif
│   └── predict-valuation-preview.gif
├── images/                 # Ảnh chụp màn hình và poster thumbnail (đã tối ưu hóa, < 300KB)
│   ├── chatbot-rag-poster.png
│   ├── chatbot-rag-ui.png
│   ├── grafana-vllm-dashboard.png
│   ├── grafana-vllm-poster.png
│   ├── mlops-audit-email-report.png
│   ├── multiagent-langgraph-studio.png
│   ├── predict-valuation-poster.png
│   └── predict-valuation-ui.png
└── videos/                 # Video MP4 gốc chất lượng cao
    ├── chatbot-rag-demo.mp4
    ├── grafana-vllm-demo.mp4
    └── predict-valuation-demo.mp4
```

## 2. Quy trình Xử lý & Tái lập (Reproducibility)

Tất cả asset được trích xuất và tối ưu hóa trực tiếp từ thư mục `source/` thông qua OpenCV và Pillow (Python):

### Lệnh Tối ưu hóa Ảnh (Pillow Lanczos Resampling & PNG Optimize)
```python
from PIL import Image

def optimize_image(src, dst, max_w=1600):
    img = Image.open(src)
    if img.width > max_w:
        ratio = max_w / img.width
        img = img.resize((max_w, int(img.height * ratio)), Image.Resampling.LANCZOS)
    img.save(dst, optimize=True)
```

### Lệnh Sinh GIF Tối ưu hóa (Adaptive Palette Quantization)
```python
import cv2
from PIL import Image

def generate_gif(video_path, out_gif_path, max_duration=12.0, target_width=800, target_fps=10):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    step = max(1, int(round(fps / target_fps)))
    frame_duration_ms = int(1000 / (fps / step))
    
    frames = []
    idx = 0
    while cap.isOpened() and len(frames) < int(max_duration * (fps / step)):
        ret, frame = cap.read()
        if not ret: break
        if idx % step == 0:
            h, w = frame.shape[:2]
            target_h = int(round(h * (target_width / w)))
            resized = cv2.resize(frame, (target_width, target_h), interpolation=cv2.INTER_AREA)
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            frames.append(Image.fromarray(rgb).quantize(colors=128, method=Image.Quantize.MEDIANCUT))
        idx += 1
    cap.release()
    
    frames[0].save(out_gif_path, save_all=True, append_images=frames[1:], duration=frame_duration_ms, loop=0, optimize=True)
```

### Lệnh Tương đương với FFmpeg CLI
```bash
# Tạo GIF preview ngắn từ video MP4
ffmpeg -i in.mp4 -vf "fps=12,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -t 12 out.gif
```
