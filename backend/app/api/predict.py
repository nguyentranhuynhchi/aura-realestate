# backend/app/api/predict.py
from fastapi import APIRouter, HTTPException
from app.schemas import PredictRequest
from app.services.predict_service import predict_service

router = APIRouter()

@router.post("/predict", summary="Dự đoán giá dựa trên thông tin nhập vào")
async def predict(payload: PredictRequest):
    try:
        # Gọi service xử lý logic dự đoán
        predicted_price = predict_service.predict_price(payload)
        
        return {
            "success": True,
            "data": {
                "predicted_price": predicted_price,
                "unit": "Tỷ VNĐ" # hoặc đơn vị phù hợp với bài toán của bạn
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi dự đoán: {str(e)}")