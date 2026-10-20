# 🏡 Aura Real Estate — Nền Tảng AI Định Giá & Tư Vấn Bất Động Sản Tự Hành

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3.1-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.3.1-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose_v2-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Apache Airflow](https://img.shields.io/badge/Apache_Airflow-2.8.1-017CEE.svg?logo=apache-airflow&logoColor=white)](https://airflow.apache.org/)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB_0.4.24-FF6F00.svg)](https://www.trychroma.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_15-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![vLLM](https://img.shields.io/badge/Inference-vLLM_0.6.3-412991.svg)](https://github.com/vllm-project/vllm)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Aura Real Estate** là hệ thống AI toàn diện hỗ trợ định giá chuẩn xác và tìm kiếm thông minh cho phân khúc **Nhà riêng tại TP.HCM**, đồng thời tích hợp hệ thống **Multi-Agent MLOps** tự hành giám sát đường ống dữ liệu, phát hiện suy giảm chất lượng mô hình và tự động vá lỗi theo vòng lặp khép kín.

---

## 📌 1. Bài Toán & Giá Trị Thực Tiễn

Thị trường bất động sản nhà ở riêng lẻ tại TP.HCM đặc thù bởi tính phân mảnh, dữ liệu tin rao hỗn loạn, chênh lệch giá ảo và thiếu công cụ tra cứu ngữ cảnh trực quan. Người mua và nhà đầu tư thường gặp hai rào cản lớn:
1. **Thiếu căn cứ định giá khách quan:** Khó xác định mức giá người bán đưa ra có hợp lý so với mặt bằng thực tế hay không.
2. **Chi phí thời gian sàng lọc thông tin:** Mất hàng giờ tra cứu thủ công qua hàng ngàn tin đăng với từ khóa tản mạn, thiếu sự liên kết ngữ nghĩa giữa nhu cầu và đặc điểm nhà ở.

Aura Real Estate giải quyết trọn vẹn bài toán trên thông qua 2 dịch vụ cốt lõi:
- **Định giá nhà tự động (Automated Valuation Model - AVM):** Nhập các thông số cơ bản (diện tích, số tầng, số toilet, quận/huyện, pháp lý, hướng nhà, nội thất) để nhận giá trị ước tính tức thì từ mô hình Stacking Ensemble được tối ưu hóa liên tục trên dữ liệu thực tế.
- **Trợ lý ảo tư vấn thông minh (Hybrid RAG Chatbot):** Giao tiếp ngôn ngữ tự nhiên theo cơ chế hội thoại đa lượt, kết hợp lọc metadata thuộc tính cứng với tìm kiếm ngữ nghĩa sâu (Semantic Search) trên Vector Database để gợi ý chính xác những bất động sản phù hợp nhất.
- **Hệ thống Multi-Agent MLOps Tự hành:** Giám sát liên tục chất lượng pipeline, tự động phát hiện lỗi thực thi hoặc suy giảm chỉ số $R^2$, tự động sinh code vá lỗi qua AST Sandbox cô lập, và biên soạn báo cáo thẩm định doanh nghiệp kèm chỉ số MTTR & Pass@k gửi trực tiếp qua Email.

> ⚠️ **Tuyên bố miễn trừ trách nhiệm (Disclaimer):** Chatbot hỗ trợ sàng lọc thông tin mô tả căn nhà và không đưa ra kết luận pháp lý ràng buộc. Mọi giao dịch bất động sản cần được xác minh qua các cơ quan nhà nước có thẩm quyền.

---

## ✨ 2. Tính Năng Nổi Bật

- **Mô hình Định giá Đa tầng (Stacking Ensemble AVM):** Kết hợp Ridge Regression, Decision Tree và Random Forest qua meta-learner Linear Regression, đạt hiệu năng $R^2 \approx 0.73 - 0.78$ và xử lý triệt để hiện tượng đa cộng tuyến (VIF filtering).
- **Trợ lý RAG Hybrid & Streaming Thời gian thực:** Cơ chế tìm kiếm lai (Metadata Filtering + ChromaDB Vector Similarity với embedding `all-MiniLM-L6-v2`), truyền phát token thời gian thực bằng Server-Sent Events (SSE) `/api/v1/chat/stream`.
- **Bộ nhớ Hội thoại 2 Tầng (2-Tier Memory):** Quản lý trạng thái ngữ cảnh trên PostgreSQL với Sliding Window (5 tin gần nhất) và tác vụ nén tóm tắt chạy ngầm (`compress_memory_if_needed`) giúp giữ vững ngữ cảnh dài hạn mà không phình to prompt.
- **Cơ chế Dự phòng LLM Kép (Dual LLM Serving):** Ưu tiên máy chủ suy luận cục bộ GPU vLLM (`Qwen/Qwen2.5-3B-Instruct-AWQ` kernel AWQ Marlin) nhằm đảm bảo quyền riêng tư dữ liệu và độ trễ thấp; tự động fallback sang Google Gemini API khi vLLM bận hoặc ngoại tuyến.
- **Vòng lặp Multi-Agent MLOps Tự hành (Self-Healing Loop):** Đồ thị 5 agent chuyên biệt (`Airflow Runner` → `Supervisor` → `Coder` → `Validator` → `Human Gate`) phối hợp qua bảng đen Blackboard, tự động sửa lỗi và tinh chỉnh tham số pipeline.
- **Cơ chế An toàn Đa tầng (Dual-Sandbox & AST Guard):** Bộ lọc AST tĩnh kiểm tra cú pháp trước khi ghi tệp, chạy thử nghiệm trong Subprocess cô lập không gây ảnh hưởng tới mã nguồn sản xuất (`pipelines/` được gắn chế độ Read-Only).
- **Thu thập Dữ liệu Vượt Rào Cản (Anti-bot Web Scraper):** Kiến trúc kết hợp Playwright Cookie Harvesting và `curl_cffi` TLS/JA3 Fingerprint Impersonation (`chrome120`), vượt qua Cloudflare WAF một cách ổn định và tiết kiệm tài nguyên.
- **Giám sát & Khả năng Quan sát (Observability):** Tích hợp sẵn Prometheus và Grafana để thu thập chỉ số suy luận vLLM theo thời gian thực (throughput, KV cache, latency) và Langfuse tracing cho từng yêu cầu LLM.

---

## 🏛️ 3. Kiến Trúc Hệ Thống

### 3.1 Sơ đồ Kiến trúc Tổng quan (Microservices Architecture)

```mermaid
flowchart TD
    subgraph CLIENT["Lớp Giao Diện Người Dùng (Client Layer)"]
        UI["React 18 + Vite + TailwindCSS<br/>(SPA Nginx Container · Port 3000)"]
    end

    subgraph API_GATEWAY["Lớp Dịch Vụ Ứng Dụng (Application Layer)"]
        FASTAPI["FastAPI Serving Gateway<br/>(Uvicorn AsyncIO · Port 8000)"]
        PRED_SVC["Predict Service<br/>(Stacking Regressor .pkl)"]
        CHAT_SVC["Chatbot Service<br/>(LangChain Hybrid RAG)"]
        FASTAPI --> PRED_SVC
        FASTAPI --> CHAT_SVC
    end

    subgraph DATA_STORAGE["Lớp Dữ Liệu & Bộ Nhớ (Data & Memory Layer)"]
        PG[("PostgreSQL 15<br/>• 2-Tier Chat Memory<br/>• Airflow Metadata DB")]
        CHROMA[("ChromaDB 0.4.24<br/>• Persistent Vector Store<br/>• all-MiniLM-L6-v2 Embeddings")]
    end

    subgraph INFERENCE["Lớp Suy Luận LLM (Inference Layer)"]
        VLLM["vLLM Inference Engine (GPU)<br/>Qwen2.5-3B-Instruct-AWQ<br/>Port 8002:8000"]
        GEMINI["Google Gemini API<br/>(Cloud Fallback Provider)"]
    end

    subgraph MLOPS["Lớp Tự Hành MLOps & Giám Sát (MLOps & Governance)"]
        AIRFLOW["Apache Airflow 2.8.1<br/>• Webserver (:8080)<br/>• Scheduler (LocalExecutor)"]
        AGENT["Multi-Agent Daemon Worker<br/>(5 Chuyên gia tự hành MLOps)"]
        PROM["Prometheus (:9090)<br/>Scrape Metrics vLLM"]
        GRAF["Grafana (:3001)<br/>Dashboard Giám sát"]
    end

    UI -- "REST / Predict JSON" --> FASTAPI
    UI -- "SSE / Chat Stream" --> FASTAPI
    PRED_SVC -. "Load Weights" .-> REGISTRY[("Model Registry<br/>Artifacts .pkl")]
    CHAT_SVC -- "Truy vấn lịch sử & nén tóm tắt" --> PG
    CHAT_SVC -- "Vector Search + Metadata Filter" --> CHROMA
    CHAT_SVC -- "Prompting ưu tiên" --> VLLM
    CHAT_SVC -. "Fallback khi vLLM bận" .-> GEMINI
    
    AIRFLOW -- "Kích hoạt DAG cào dữ liệu & huấn luyện" --> REGISTRY
    AGENT -- "REST API Trigger & Giám sát XCom" --> AIRFLOW
    AGENT -- "Prompting chẩn đoán & sinh bản vá" --> VLLM
    PROM -- "Scrape :8000/metrics" --> VLLM
    GRAF -- "Trực quan hóa" --> PROM
```

---

### 3.2 Luồng Dữ Liệu MLOps & Vòng Lặp Multi-Agent Tự Vá Lỗi

```mermaid
flowchart TD
    START(["⏰ Lịch hẹn PIPELINE_RUN_TIME<br/>hoặc kích hoạt thủ công"]) --> AF_RUNNER["[Agent 1: Airflow Runner]<br/>Kích hoạt DAG aura_realestate_mlops_pipeline"]
    
    subgraph DAG_EXECUTION["Thực Thi Pipeline MLOps Trên Airflow"]
        T1["Task 1: init_mlops_logistics<br/>(Khởi tạo folder experiment)"]
        T2["Task 2: crawl_raw_data<br/>(curl_cffi + TLS Chrome120)"]
        T3["Task 3: run_modular_mlops_pipeline<br/>(24 micro-modules tiền xử lý & train)"]
        T4["Task 4: finalize_pipeline_summary<br/>(Đẩy JSON Summary vào XCom)"]
        T1 --> T2 --> T3 --> T4
    end

    AF_RUNNER --> DAG_EXECUTION
    DAG_EXECUTION --> SUPERVISOR["[Agent 2: Supervisor]<br/>Đọc kết quả trên Blackboard & Chẩn đoán"]

    SUPERVISOR -- "R2 >= 0.65 & Pipeline Thành công" --> GATE["[Agent 5: Human Gate]<br/>Xuất bản Báo cáo Thẩm định PDF"]
    
    SUPERVISOR -- "Có lỗi Code hoặc R2 < 0.65<br/>(Vòng lặp <= 3 lần)" --> CODER["[Agent 3: Coder]<br/>Phân tích nhật ký, định vị file mục tiêu<br/>Sinh bản vá code qua LLM vLLM"]
    
    CODER --> AST{"Bộ Kiểm Tra AST<br/>(validate_python_syntax)"}
    AST -- "Lỗi cú pháp" --> CODER
    AST -- "Cú pháp hợp lệ" --> SANDBOX["Ghi bản vá vào Sandbox cô lập<br/>(agent/sandbox/workspace)"]

    SANDBOX --> VALIDATOR["[Agent 4: Validator]<br/>Thẩm định trong Subprocess cô lập<br/>Kiểm tra Importability & Tương thích"]
    
    VALIDATOR -- "Thẩm định thất bại" --> CODER
    VALIDATOR -- "Bật đèn xanh (Passed)" --> AF_RETRY["Airflow Runner chạy lại<br/>với pipeline_dir trỏ về Sandbox"]
    AF_RETRY --> DAG_EXECUTION

    GATE --> REPORT[("Xuất bản latest_audit_report.md<br/>Gửi Email PDF kèm MTTR & Pass@k")]
    REPORT --> END(["🏁 Hoàn tất phiên vận hành"])
```

---

### 3.3 Quy Trình Phục Vụ Trực Tuyến & Hybrid RAG (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor User as Người dùng
    participant FE as Frontend (React SPA)
    participant BE as FastAPI Gateway
    participant PG as PostgreSQL (2-Tier Memory)
    participant VDB as ChromaDB (Vector Store)
    participant LLM as vLLM (Qwen2.5-AWQ)

    User->>FE: Nhập tin nhắn tìm kiếm BĐS
    FE->>BE: POST /api/v1/chat/stream {message, session_id}
    
    activate BE
    BE->>PG: Lấy 5 tin nhắn gần nhất & bản tóm tắt lịch sử
    PG-->>BE: Trả về Context Memory
    
    BE->>VDB: Query Hybrid (all-MiniLM-L6-v2 + Metadata Filters)
    VDB-->>BE: Trả về Top 3 căn nhà phù hợp nhất
    
    BE->>LLM: Gửi Prompt (System Prompt + RAG Context + 2-Tier Memory)
    activate LLM
    
    loop Truyền phát Token (SSE Stream)
        LLM-->>BE: Stream Token chunk
        BE-->>FE: data: {"token": "..."}
        FE-->>User: Hiển thị chữ chạy theo thời gian thực
    end
    deactivate LLM
    
    BE-->>FE: data: [DONE]
    
    par Tác vụ chạy ngầm (FastAPI Background Task)
        BE->>PG: Lưu 2 tin nhắn mới (User & Assistant)
        BE->>PG: Nén 2 tin cũ nhất vào chat_summaries nếu tổng tin >= 5
    end
    deactivate BE
```

---

### 3.4 Kiến Trúc Mạng & Hạ Tầng Container (Docker Compose Topology)

```mermaid
flowchart LR
    subgraph DOCKER_HOST["Máy Chủ Docker (Bridge Network: aura_network)"]
        direction TB
        
        subgraph PORTS_EXPOSED["Cổng Mạng Công Khai (Host Bindings)"]
            P3000["Host :3000"]
            P8000["Host :8000"]
            P8001["Host :8001"]
            P8080["Host :8080"]
            P8002["Host :8002"]
            P9090["Host :9090"]
            P3001["Host :3001"]
            P5432["Host :5432"]
        end

        subgraph CONTAINERS["Các Dịch Vụ Containerized"]
            FE_C["frontend<br/>(Nginx 80)"]
            BE_C["backend<br/>(FastAPI 8000)"]
            CHROMA_C["chromadb<br/>(Chroma 8000)"]
            PG_C["postgres<br/>(PostgreSQL 5432)"]
            AF_W_C["airflow-webserver<br/>(Airflow 8080)"]
            AF_S_C["airflow-scheduler<br/>(LocalExecutor)"]
            VLLM_C["vllm<br/>(NVIDIA Runtime)"]
            PROM_C["prometheus<br/>(Prometheus 9090)"]
            GRAF_C["grafana<br/>(Grafana 3000)"]
            AGENT_C["agent-service<br/>(Daemon Worker)"]
        end

        subgraph VOLUMES["Persistent Storage (Docker Volumes)"]
            V_PG[("./docker_data/postgres_data")]
            V_CHROMA[("./docker_data/chromadb_data")]
            V_REGISTRY[("./model_registry")]
            V_PIPELINES[("./pipelines (Read-Only)")]
            V_DATA[("./data")]
        end
    end

    P3000 --- FE_C
    P8000 --- BE_C
    P8001 --- CHROMA_C
    P5432 --- PG_C
    P8080 --- AF_W_C
    P8002 --- VLLM_C
    P9090 --- PROM_C
    P3001 --- GRAF_C

    PG_C --- V_PG
    CHROMA_C --- V_CHROMA
    BE_C --- V_REGISTRY
    AGENT_C --- V_PIPELINES
    AF_S_C --- V_DATA
```

---

## 📸 4. Giao Diện & Hình Ảnh Minh Họa

| Chức năng | Minh họa giao diện thực tế | Mô tả kỹ thuật |
| :--- | :---: | :--- |
| **Định giá Bất động sản** | *(Placeholder: Thư mục ảnh chụp màn hình UI Predict)* | Giao diện cho phép chọn 23 quận/huyện TP.HCM, diện tích, tầng, pháp lý; tính toán giá trị lập tức qua FastAPI Serving |
| **Chatbot Tư vấn RAG** | *(Placeholder: Thư mục ảnh chụp màn hình UI Chatbot Streaming)* | Hội thoại thời gian thực qua Server-Sent Events, hiển thị thẻ thông tin căn nhà kèm nguồn trích dẫn từ ChromaDB |
| **Airflow DAG MLOps** | *(Placeholder: Ảnh chụp Airflow Webserver DAG Graph)* | Quản lý quy trình cào dữ liệu, làm sạch, tách dữ liệu và tái huấn luyện mô hình theo kiến trúc vi mô |
| **Giám sát Inference vLLM** | *(Placeholder: Dashboard Grafana / Prometheus)* | Biểu đồ theo dõi GPU KV Cache Usage, Prompt Throughput, Time To First Token (TTFT) |
| **Báo cáo Thẩm định MLOps** | *(Placeholder: File PDF xuất bản tại `agent/metrics/`)* | Báo cáo kiểm định chỉ số kinh doanh ($R^2$, MAE, RMSE), đo lường thời gian khắc phục sự cố MTTR và tỷ lệ sửa thành công Pass@k |

---

## 💻 5. Yêu Cầu Hệ Thống

Dự án được đóng gói hoàn chỉnh bằng Docker Compose, tuy nhiên có thể vận hành từng phần trên môi trường cục bộ:

| Thành phần | Phiên bản tối thiểu | Ghi chú cấu hình |
| :--- | :--- | :--- |
| **Hệ điều hành** | Windows 10/11 (WSL2), Ubuntu 20.04+, macOS | Khuyến nghị môi trường Linux/WSL2 để hỗ trợ GPU Docker container |
| **Python** | `Python >= 3.10` (Khuyến nghị 3.10 hoặc 3.11) | Phiên bản cơ sở trong Docker: `python:3.10-slim` |
| **Node.js** | `Node.js >= 18.x` (Khuyến nghị 20-alpine) | Phục vụ biên dịch Frontend qua Vite (`package.json`) |
| **Docker Engine** | `Docker >= 24.0.0`, `Docker Compose v2` | Hỗ trợ cấu hình `docker-compose.yml` chuẩn hiện đại |
| **NVIDIA GPU** | Tối thiểu 6GB VRAM (Hỗ trợ CUDA 12.1+) | Dành cho container `vLLM` chạy Qwen2.5-3B-AWQ (Nếu không có GPU, hệ thống tự động chuyển sang Gemini API) |
| **Bộ nhớ RAM** | Khuyến nghị tối thiểu 16GB RAM | Đáp ứng đồng thời 10 microservices container |

---

## ⚙️ 6. Cấu Hình Biến Môi Trường

Hệ thống sử dụng tệp `.env` tại thư mục gốc cho toàn bộ cụm container và `backend/.env` cho Backend:

```bash
# Tạo tệp cấu hình từ mẫu
cp .env.example .env
cp .env.example backend/.env
```

### Bảng Chi Tiết Biến Môi Trường

| Tên biến | Mô tả chức năng | Bắt buộc? | Giá trị mặc định / Ví dụ |
| :--- | :--- | :---: | :--- |
| `AIRFLOW_FERNET_KEY` | Khóa mã hóa bảo mật kết nối và mật khẩu trong Airflow (32 bytes base64) | **Có** | `0tY0ZkJyMWRZ7rV4hWf_nCq_TqQ3n1oK6xHqYj8iV-k=` |
| `AIRFLOW_WEBSERVER_SECRET_KEY` | Khóa bí mật phục vụ phiên làm việc Flask Webserver Airflow | **Có** | `aura_super_secret_webserver_key_999` |
| `PIPELINE_RUN_TIME` | Giờ tự động kích hoạt MLOps mỗi ngày (`HH:MM`). Đặt `none` để tắt | Không | `13:50` (hoặc `none`) |
| `CRAWL_MAX_LIMIT` | Số lượng bài đăng tối đa thu thập mỗi lần cào để tránh rate limit | Không | `50` |
| `AIRFLOW_SMTP_USER` | Email Gmail dùng để gửi thông báo và báo cáo thẩm định | Không | `your_email@gmail.com` |
| `AIRFLOW_SMTP_PASSWORD` | Mật khẩu ứng dụng Google (App Password 16 ký tự) | Không | `cuvlozelxyatjops` |
| `ALERT_RECIPIENT` | Địa chỉ email người quản trị tiếp nhận báo cáo thẩm định PDF | Không | `admin_recipient@gmail.com` |
| `VLLM_BASE_URL` | URL dịch vụ OpenAI-compatible của vLLM nội bộ hoặc máy chủ ngoài | **Có** | `http://vllm:8000/v1` (Docker) hoặc `http://localhost:8002/v1` |
| `VLLM_MODEL_NAME` | Tên mô hình ngôn ngữ được nạp trong máy chủ suy luận vLLM | **Có** | `Qwen/Qwen2.5-3B-Instruct-AWQ` |
| `GEMINI_API_KEY` | API Key Google AI Studio phục vụ dự phòng (Fallback LLM) | Tùy chọn | `AIzaSy...` |
| `DATABASE_URL` | Chuỗi kết nối PostgreSQL lưu trữ bộ nhớ 2 tầng của Chatbot | **Có** | `postgresql://postgres:postgres@postgres:5432/aura_realestate_db` |
| `LANGFUSE_PUBLIC_KEY` | Khóa công khai Langfuse để theo dõi truy vấn LLM | Không | `pk-lf-...` |
| `LANGFUSE_SECRET_KEY` | Khóa bí mật Langfuse để theo dõi truy vấn LLM | Không | `sk-lf-...` |
| `HF_TOKEN` | Token Hugging Face để tải trọng số mô hình lượng tử hóa | Không | `hf_...` |

---

## 🚀 7. Cài Đặt & Khởi Chạy

### Kịch bản 1: Khởi chạy Trọn gói qua Docker Compose (Khuyến nghị)

Toàn bộ 10 dịch vụ được điều phối tự động:

```bash
# 1. Clone repository
git clone https://github.com/your-username/aura-realestate.git
cd aura-realestate

# 2. Khởi tạo cấu hình môi trường
cp .env.example .env
cp .env.example backend/.env

# 3. Khởi tạo và kích hoạt toàn bộ 10 container
docker compose up -d --build
```

#### Bảng Kiểm Tra Cổng Dịch Vụ Đang Chạy:

| Dịch vụ | URL Truy cập | Chức năng chính |
| :--- | :--- | :--- |
| **Frontend UI** | [http://localhost:3000](http://localhost:3000) | Giao diện React Định giá & Chatbot RAG |
| **FastAPI Swagger Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Tài liệu kiểm thử API định giá và chat trực tuyến |
| **Apache Airflow Webserver** | [http://localhost:8080](http://localhost:8080) | Giao diện quản lý DAGs (`admin` / `admin`) |
| **ChromaDB REST API** | [http://localhost:8001](http://localhost:8001) | Cổng truy vấn Vector Database |
| **vLLM Inference Server** | [http://localhost:8002/v1/models](http://localhost:8002/v1/models) | Điểm cuối OpenAI-compatible của Qwen2.5 |
| **Prometheus Server** | [http://localhost:9090](http://localhost:9090) | Cổng thu thập chỉ số hiệu năng vLLM |
| **Grafana Dashboard** | [http://localhost:3001](http://localhost:3001) | Dashboard quan sát trực quan (`admin` / `admin`) |
| **PostgreSQL Database** | `localhost:5432` | CSDL bộ nhớ chat và metadata Airflow |

---

### Kịch bản 2: Vận hành Từng Phần Cục Bộ (Local Development)

Nếu muốn phát triển hoặc gỡ lỗi từng phần mà không dùng Docker:

#### 1. Khởi chạy Pipeline Học Máy & Tiền Xử Lý:
```bash
# Cài đặt thư viện môi trường
pip install -r requirements.txt
playwright install chromium

# Chạy pipeline tiền xử lý, huấn luyện và đồng bộ ChromaDB
python run_pipeline.py
```

#### 2. Khởi chạy Backend API (FastAPI):
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. Khởi chạy Frontend (React + Vite):
```bash
cd frontend
npm install
npm run dev
# Mở trình duyệt tại http://localhost:5173
```

#### 4. Khởi chạy Multi-Agent MLOps Worker:
```bash
# Chạy 1 lần thẩm định và thoát
python -m agent.main --mode once

# Hoặc chạy ở chế độ giám sát ngầm theo lịch hẹn PIPELINE_RUN_TIME
python -m agent.main --mode daemon
```

---

## 📖 8. Hướng Dẫn Sử Dụng API & Mã Mẫu

### 8.1 API Dự Đoán Giá Nhà (`POST /api/v1/predict`)

**Yêu cầu qua cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "area_raw": 85.5,
       "floors": 3.0,
       "bathrooms": 2.0,
       "district_clean": "Quận Tân Phú",
       "legal_clean": "Có Sổ",
       "direction_clean": "Đông Nam",
       "interior_clean": "Nội thất cơ bản"
     }'
```

**Phản hồi thành công (HTTP 200):**
```json
{
  "success": true,
  "data": {
    "predicted_price": 10.459774416812296,
    "unit": "Tỷ VNĐ"
  }
}
```

---

### 8.2 API Chatbot RAG Truyền Phát Thời Gian Thực (`POST /api/v1/chat/stream`)

**Ví dụ gọi bằng JavaScript (Fetch API + EventStream Reader):**
```javascript
const response = await fetch("http://localhost:8000/api/v1/chat/stream", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message: "Tìm giúp tôi căn nhà ở Quận Bình Thạnh dưới 7 tỷ có sổ hồng",
    session_id: "user_session_123"
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder("utf-8");

while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value);
  const lines = chunk.split("\n");
  for (const line of lines) {
    if (line.startsWith("data: ")) {
      const dataStr = line.replace("data: ", "").trim();
      if (dataStr === "[DONE]") {
        console.log("Truyền phát hoàn tất!");
      } else {
        const payload = JSON.parse(dataStr);
        process.stdout.write(payload.token);
      }
    }
  }
}
```

---

## 🔬 9. Nghiên Cứu Mô Hình & Đánh Giá Thực Nghiệm

### 9.1 So Sánh Thu Thập Dữ Liệu (Crawler Approaches)

| Phương pháp | Công nghệ sử dụng | Kết quả | Đánh giá & Vấn đề kỹ thuật |
| :---: | :--- | :---: | :--- |
| **Hướng 1** | Requests + BeautifulSoup | ❌ Thất bại | Bị Cloudflare WAF chặn ngay lập tức (`403 Forbidden`); không thể tải trang SPA React/Vue |
| **Hướng 2** | Selenium + `undetected-chromedriver` | ❌ Bỏ dở | Vượt được JavaScript rendering nhưng tiêu tốn tài nguyên quá lớn (CPU/RAM); hay bị crash khi chạy cron định kỳ |
| **Hướng 3** | **Playwright + curl_cffi (`chrome120`)** | ✅ **Sản xuất** | **Hoạt động ổn định:** Thu thập cookie hợp lệ bằng Playwright rồi tái sử dụng qua `curl_cffi` mô phỏng TLS Fingerprint Chrome 120 |

---

### 9.2 Tiền Xử Lý Biến & Kiểm Soát Đa Cộng Tuyến (EDA & Feature Matrix)

Bộ dữ liệu thô gồm 18 thuộc tính thu thập từ thị trường được chuẩn hóa qua quy trình khắt khe:

| Thuộc tính gốc | Phân loại | Vấn đề phát hiện khi EDA | Quyết định xử lý | Phương pháp chuyển đổi |
| :--- | :--- | :--- | :---: | :--- |
| `price_raw` | **Target** | Skewness 7.94, Kurtosis 87.41, nhiều outlier | **Giữ** | Regex trích số về đơn vị Tỷ VNĐ; lọc dải $0 < x \le 400$ tỷ; biến đổi `log1p` |
| `area_raw` | Feature | Định dạng lẫn dấu chấm (`4.335.7`); lệch phải | **Giữ** | Lọc dải thực tế $10 - 600m^2$; kết hợp kiểm tra đơn giá; biến đổi `log1p` + `StandardScaler` |
| `address_raw` | Feature | Chuỗi địa chỉ quá dài và chi tiết gây nhiễu | **Rút gọn** | Regex bóc tách 23 đơn vị Quận/Huyện TP.HCM; áp dụng **Ordinal Encoding** theo giá trị đất trung bình |
| `bedrooms` | Feature | Đa cộng tuyến cực đại với `bathrooms` ($r = 0.97$) | **Loại bỏ** | Điền median tập huấn luyện rồi loại bỏ hoàn toàn để triệt tiêu chỉ số VIF |
| `bathrooms` | Feature | Xuất hiện giá trị bất thường (hơn 30 toilet do spam) | **Giữ** | Cắt ngưỡng $1 - 15$; điền median; chuẩn hóa qua `StandardScaler` |
| `floors` | Feature | Nhiều giá trị khuyết (NaN) | **Giữ** | Gán mặc định 1 tầng (nhà cấp 4/trệt); giới hạn $1 - 15$; chuẩn hóa qua `StandardScaler` |
| `house_direction`| Feature | Tỷ lệ khuyết cao (~80.25%) | **Giữ** | Chuẩn hóa về 8 hướng địa lý chính; One-Hot Encoding 8 cột; bỏ nhóm "Không rõ" làm baseline |
| `legal_status` | Feature | Văn bản tự do rườm rà | **Giữ** | Gom nhóm về 3 trạng thái (`Có Sổ`, `Chưa Sổ`, `Không rõ`); Ordinal Encoding |
| `interior` | Feature | Tình trạng nội thất mô tả chủ quan | **Giữ** | Phân loại về 6 cấp độ; Ordinal Encoding + `StandardScaler` |

---

### 9.3 Bảng Xếp Hạng Thuật Toán & Mô Hình Quán Quân

Sau khi tinh chỉnh siêu tham số qua 5-Fold Cross Validation trên tập Train, các mô hình tự viết (Scratch) và mô hình thư viện được xếp hạng hiệu năng trên tập kiểm thử độc lập:

| Hạng | Tên mô hình | $R^2$ Score | MAE (Log) | RMSE (Log) | Cơ chế kiến trúc & Đánh giá |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 🏆 **Champion** | **Stacking Regressor (Ensemble)** | **0.7311 - 0.7789** | **0.2646** | **0.3546** | Kết hợp Ridge + Decision Tree + Random Forest qua Meta-Learner Linear Regression; kiểm soát phương sai tối ưu |
| 🥈 2 | Voting Regressor | 0.7018 | 0.2784 | 0.3734 | Trung bình cộng dự đoán của mô hình tuyến tính và phi tuyến |
| 🥉 3 | Random Forest Regressor | 0.7005 | 0.2790 | 0.3742 | 50 cây quyết định, giới hạn độ sâu `max_depth=20`, chống overfitting |
| 4 | Decision Tree Regressor | 0.6729 | 0.2828 | 0.3911 | Phân chia nhánh dựa trên mức giảm phương sai (Variance Reduction) |
| 5 | Ridge Regression (L2) | 0.5688 | 0.3372 | 0.4490 | Tuyến tính có phạt hệ số $\alpha = 1.0$ kiểm soát co cụm trọng số |
| 6 | Linear Regression | 0.5687 | 0.3372 | 0.4491 | Tuyến tính thuần túy, nhạy cảm với tương quan giữa các thuộc tính |

---

## 📂 10. Cấu Trúc Thư Mục Dự Án

```text
aura-realestate/
├── agent/                       # Hệ thống Multi-Agent MLOps tự hành (Python thuần & LangGraph)
│   ├── agents/                  # 5 Chuyên gia: airflow_runner, supervisor, coder, validator, human_gate
│   ├── core/                    # Engine điều phối Native Workflow & Bảng đen Blackboard State
│   ├── metrics/                 # Bộ thu thập chỉ số doanh nghiệp MTTR, Pass@k & file báo cáo Markdown
│   ├── sandbox/                 # Môi trường cô lập Dual-Sandbox (baseline đối chiếu & workspace chỉnh sửa)
│   ├── tests/                   # Bộ kiểm thử đơn vị cho toàn bộ công cụ và luồng Agent
│   ├── tools/                   # Các công cụ: rào chắn AST, chạy subprocess, kết nối Airflow, ReportLab PDF
│   ├── config.py                # Cấu hình kết nối LLM (vLLM local & OpenAI format)
│   ├── main.py                  # Điểm khởi chạy Agent CLI (--mode once | daemon)
│   └── requirements.txt         # Phụ thuộc thư viện cho Agent Service
├── backend/                     # Backend API Gateway phát triển bằng FastAPI
│   ├── app/
│   │   ├── api/                 # Tuyến API Endpoints: predict.py, chatbot.py (Streaming SSE)
│   │   ├── core/                # Cấu hình hệ thống backend
│   │   ├── schemas.py           # Định nghĩa cấu trúc dữ liệu Pydantic (PredictRequest, ChatRequest)
│   │   ├── services/            # Logic nghiệp vụ: predict_service, chatbot_service (2-tier memory RAG)
│   │   └── main.py              # Điểm khởi chạy ứng dụng FastAPI (CORS, Routers, Health Check)
│   ├── models/                  # Lưu trữ artifact Stacking Regressor .pkl phục vụ suy luận
│   ├── Dockerfile               # Cấu hình container Python 3.10-slim cho Backend
│   └── requirements.txt         # Thư viện phụ thuộc Backend (FastAPI, LangChain, psycopg, ChromaDB)
├── crawler/                     # Hệ thống thu thập dữ liệu bất động sản
│   ├── scripts/run_crawler.py   # Lệnh thực thi cào dữ liệu tích hợp vào Airflow BashOperator
│   └── spiders/v3_api_hidden.py # Spider cào ngầm kết hợp Playwright + curl_cffi impersonate Chrome120
├── dags/                        # Thư mục chứa Apache Airflow DAGs
│   └── aura_mlops_dag.py        # DAG aura_realestate_mlops_pipeline điều phối cào, tiền xử lý & huấn luyện
├── data/                        # Dữ liệu phân tầng: raw (thô) và processed (đã làm sạch)
├── docker_data/                 # Thư mục lưu trữ volume bền vững (Postgres DB, ChromaDB vectors)
├── frontend/                    # Giao diện Single Page Application (React 18 + Vite + TailwindCSS)
│   ├── src/
│   │   ├── features/            # Mô-đun giao diện: predict (định giá) và chatbot (tư vấn trực tuyến)
│   │   ├── services/            # Gọi API Backend qua Axios và EventSource/Fetch Stream
│   │   ├── App.jsx              # Định tuyến trang chính
│   │   └── main.jsx             # Điểm nạp ứng dụng React
│   ├── Dockerfile               # Multi-stage build (Node.js 20 build -> Nginx Alpine phục vụ)
│   └── package.json             # Danh mục gói NPM và scripts (dev, build, preview)
├── ml_pipeline_experiments/     # Sổ tay Jupyter ghi lại 7 giai đoạn nghiên cứu thực nghiệm EDA & Modeling
├── model_registry/              # Kho lưu trữ các phiên bản mô hình kèm metadata & pipeline_summary.json
├── pipelines/                   # Bộ 24 vi mô-đun tiền xử lý dữ liệu và huấn luyện chuẩn hóa
├── .env.example                 # Bản mẫu biến môi trường chuẩn kèm hướng dẫn an toàn
├── docker-compose.yml           # Tệp phối hợp 10 container dịch vụ trọn gói
├── Dockerfile.worker            # Image phục vụ Airflow Webserver, Scheduler & Worker
├── pipeline_log.json            # Nhật ký lưu trữ mốc thời gian cào và huấn luyện gần nhất
├── requirements.txt             # Thư viện phục vụ bộ thu thập dữ liệu & lập lịch độc lập
└── run_pipeline.py              # Kịch bản chạy toàn diện Pipeline từ dòng lệnh
```

---

## 🧪 11. Kiểm Thử, Biên Dịch & Vận Hành

### Kiểm Thử Hệ Thống Multi-Agent (11 Test Cases Toàn Diện)

Chạy bộ kiểm thử tự động của Agent bên trong container `aura_agent_service`:

```bash
docker exec aura_agent_service python -m pytest agent/tests -v
```

*Kết quả thẩm định thực tế:*
```text
agent/tests/test_tools.py::test_ast_syntax_checker PASSED                     [  9%]
agent/tests/test_tools.py::test_safe_file_write_with_ast_guard PASSED         [ 18%]
agent/tests/test_tools.py::test_unified_diff_generator PASSED                 [ 27%]
agent/tests/test_tools.py::test_subprocess_importability_check PASSED         [ 36%]
agent/tests/test_tools.py::test_airflow_bridge_fallback PASSED                 [ 45%]
agent/tests/test_tools.py::test_enterprise_metrics_collector PASSED           [ 54%]
agent/tests/test_workflow.py::test_supervisor_catalog_resolution PASSED       [ 63%]
agent/tests/test_workflow.py::test_supervisor_routing_success PASSED          [ 72%]
agent/tests/test_workflow.py::test_coder_and_validator_safety_flow PASSED     [ 81%]
agent/tests/test_workflow.py::test_human_gate_and_metrics_report PASSED       [ 90%]
agent/tests/test_workflow.py::test_end_to_end_native_workflow PASSED          [100%]
============================== 11 passed in 96.79s ==============================
```

### Kiểm Tra Trạng Thái & Nhật Ký Container

```bash
# Xem trạng thái hoạt động của 10 container
docker compose ps

# Theo dõi nhật ký trực tiếp của Agent Service
docker logs -f aura_agent_service

# Theo dõi nhật ký trực tiếp của Backend FastAPI
docker logs -f aura-realestate-backend-1

# Theo dõi nhật ký suy luận của vLLM Server
docker logs -f aura_vllm_server
```

### Biên Dịch Giao Diện Frontend (Production Build)

```bash
cd frontend
npm run build
# Bản build tối ưu hóa sẽ được lưu tại thư mục frontend/dist/
```

---

## 🤝 12. Hướng Dẫn Đóng Góp (Contributing)

Chúng tôi hoan nghênh mọi đóng góp nhằm cải thiện độ chính xác của mô hình và tính ổn định của hệ thống!

1. **Fork** kho mã nguồn về tài khoản cá nhân.
2. Tạo nhánh tính năng mới theo quy chuẩn:
   ```bash
   git checkout -b feature/ten-tinh-nang-moi
   ```
3. Thực hiện thay đổi, tuân thủ phong cách lập trình (PEP 8 cho Python, ESLint cho React).
4. Đảm bảo toàn bộ bài kiểm thử đều vượt qua:
   ```bash
   docker exec aura_agent_service python -m pytest agent/tests
   ```
5. Commit thay đổi tuân theo [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   git commit -m "feat: bổ sung cơ chế lọc nhiễu diện tích mới trong preprocessing"
   ```
6. Đẩy nhánh lên repository và tạo **Pull Request** kèm mô tả chi tiết các thử nghiệm.

---

## 📄 13. Giấy Phép (License)

Dự án hiện được định hướng phát hành theo giấy phép **MIT License**. Chi tiết các quyền sử dụng, sao chép, sửa đổi và phân phối được quy định trong tệp [LICENSE](LICENSE).

*(TODO: Cần khởi tạo tệp `LICENSE` chính thức tại thư mục gốc của repository).*
