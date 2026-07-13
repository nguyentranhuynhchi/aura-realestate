import os

class Settings:
    # Tên của dự án và tiền tố phiên bản API
    PROJECT_NAME: str = "Dự đoán giá bất nhà"
    API_V1_STR: str = "/api/v1"
    
    # Định nghĩa đường dẫn tuyệt đối trỏ ra ngoài thư mục gốc để vào Registry `models/`
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    MODEL_REGISTRY_DIR = os.path.join(BASE_DIR, "..", "models")
    
    # Tên các file weight mô hình đã lưu
    SCALER_FILE_NAME: str = "standard_scaler.pkl"
    MODEL_FILE_NAME: str = "best_stacking_regressor.pkl"

settings = Settings()