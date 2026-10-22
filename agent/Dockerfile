FROM python:3.11-slim

WORKDIR /app

# Cài các công cụ biên dịch cơ bản
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy và cài đặt thư viện riêng của Agent
COPY agent/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy toàn bộ mã nguồn vào container
COPY . /app

ENV PYTHONPATH=/app

# Mặc định khởi chạy main.py của Agent
CMD ["python", "-m", "agent.main"]