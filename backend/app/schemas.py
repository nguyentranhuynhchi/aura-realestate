# backend/app/schemas.py
from pydantic import BaseModel, Field
from typing import Optional

class PredictRequest(BaseModel):
    area_raw: float = Field(..., description="Diện tích thực tế (m²)", example=85.5)
    floors: float = Field(1.0, description="Số tầng của căn nhà", example=3.0)
    bathrooms: float = Field(..., description="Số phòng tắm / vệ sinh", example=2.0)
    district_clean: str = Field(..., description="Tên Quận/Huyện tại TP.HCM", example="Quận Tân Phú")
    legal_clean: str = Field("Không rõ", description="Trạng thái pháp lý của căn nhà", example="Có Sổ")
    direction_clean: str = Field("Không rõ", description="Hướng nhà", example="Đông Nam")
    interior_clean: str = Field("Không rõ (NaN)", description="Tình trạng nội thất", example="Nội thất cơ bản")

class ChatRequest(BaseModel):
    message: str = Field(..., description="Câu hỏi hoặc lời nhắn của người dùng", example="cho tôi biết giá bán của căn nhà ở Địa chỉ: Số 142 đường Lê Văn Việt, Tăng Nhơn Phú A, TP. Thủ Đức!")