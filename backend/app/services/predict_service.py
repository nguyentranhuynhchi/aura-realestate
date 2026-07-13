# backend/app/services/predict_service.py
import os
import joblib
import numpy as np
import pandas as pd
from pipelines.utils import DISTRICT_MAPPING, INTERIOR_MAPPING, LEGAL_MAPPING

class PredictService:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        model_dir = os.path.join(base_dir, "models")
        
        model_path = os.path.join(model_dir, "best_stacking_regressor.pkl")
        scaler_path = os.path.join(model_dir, "standard_scaler.pkl")
        
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            print("=== Models loaded successfully! ===")
        else:
            raise FileNotFoundError(f"Không tìm thấy file mô hình tại {model_dir}.")

        self.district_mapping = DISTRICT_MAPPING
        self.interior_mapping = INTERIOR_MAPPING
        self.legal_mapping = LEGAL_MAPPING

    def predict_price(self, data) -> float:
        # 1. Thực hiện kéo phân phối diện tích bằng Log-transform: log(x + 1)
        area_log = np.log1p(data.area_raw)
        
        # 2. Khởi tạo cấu trúc dữ liệu nền chứa đủ 14 biến (Giá trị mặc định ban đầu là 0.0)
        features = {col: 0.0 for col in self.scaler.feature_names_in_}
        
        # 3. Điền các giá trị số học và giá trị đã ánh xạ Ordinal vào cấu trúc dữ liệu
        features['area_log'] = area_log
        features['bathrooms'] = data.bathrooms
        features['floors'] = data.floors
        
        # Ánh xạ an toàn, nếu không khớp nhãn thì mặc định lấy giá trị trung vị hoặc trung bình
        features['address_encoded'] = self.district_mapping.get(data.district_clean, 15)
        features['interior_encoded'] = self.interior_mapping.get(data.interior_clean, 3)
        features['legal_encoded'] = self.legal_mapping.get(data.legal_clean, 0)
        
        # 4. Xử lý One-Hot Encoding cho Hướng nhà (Nếu chọn "Không rõ" thì tất cả giữ nguyên bằng 0)
        target_direction_col = f"dir_{data.direction_clean}"
        if target_direction_col in features:
            features[target_direction_col] = 1.0
            
        # 5. Chuyển đổi thành DataFrame và ép đúng thứ tự 14 cột mà bộ Scaler yêu cầu
        input_data = pd.DataFrame([features])[self.scaler.feature_names_in_]
        
        # 6. Chuẩn hóa ma trận đầu vào qua StandardScaler (Mean = 0, Std = 1)
        scaled_data = self.scaler.transform(input_data)
        
        # 7. Dự đoán giá trị Log từ mô hình học máy Stacking
        log_prediction = self.model.predict(scaled_data)[0]
        
        # 8. Giải mã ngược từ Log sang giá trị Tỷ VNĐ thực tế bằng hàm mũ: exp(x) - 1
        actual_price = np.expm1(log_prediction)
        
        return float(actual_price)

predict_service = PredictService()