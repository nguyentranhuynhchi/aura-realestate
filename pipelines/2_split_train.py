import os
import sys
import pandas as pd
import numpy as np
import joblib
import shutil # ◄ Bổ sung để sao lưu
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

#  NHẬN THAM SỐ TIMESTAMP ĐƯỢC TRUYỀN TỪ RUN_PIPELINE
if len(sys.argv) < 2:
    print("[ERROR] Thiếu tham số timestamp của folder lịch sử! Vui lòng chạy qua file run_pipeline.py.")
    sys.exit(1)

CURRENT_TIMESTAMP = sys.argv[1]

# Xác định đường dẫn dựa trên cấu trúc dự án của em
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_DATA_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "data", "processed", "clean_data.csv"))
PROCESSED_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "data", "processed"))
MODEL_ARTIFACTS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "backend", "models"))
REGISTRY_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "model_registry"))

CURRENT_EXP_DIR = os.path.join(REGISTRY_DIR, CURRENT_TIMESTAMP)

print("\n--- BẮT ĐẦU LUỒNG SHUFFLE, SPLIT VÀ CHUẨN HÓA ĐẶC TRƯNG ---")

# 1. Đọc dữ liệu sạch thô tổng hợp
if not os.path.exists(CLEAN_DATA_PATH):
    print(f"[ERROR] Không tìm thấy file clean_data.csv tại: {CLEAN_DATA_PATH}")
    sys.exit(1)

df = pd.read_csv(CLEAN_DATA_PATH)
if df.empty:
    print("[ERROR] File clean_data.csv trống. Không có dữ liệu để huấn luyện.")
    sys.exit(1)

print(f"[INFO] Đã nạp thành công kho dữ liệu tổng gồm {len(df)} dòng.")

# Drop cột 'id' hoặc 'url' nếu còn sót lại để tránh đưa vào model huấn luyện
df = df.drop(columns=['id', 'url'], errors='ignore')

# 2. Thực hiện Shuffle và Split dữ liệu thành Train (70%), Val (15%), Test (15%)
train_df, temp_df = train_test_split(df, test_size=0.30, random_state=42, shuffle=True)
val_df, test_df = train_test_split(temp_df, test_size=0.50, random_state=42, shuffle=True)

print(f"[INFO] Tỷ lệ phân chia tập dữ liệu:")
print(f"       - Tập Train     : {len(train_df)} dòng")
print(f"       - Tập Validation: {len(val_df)} dòng")
print(f"       - Tập Test      : {len(test_df)} dòng")

# Tách riêng nhãn (Target) và Đặc trưng (Features)
y_train = train_df['price_raw'].values
y_val = val_df['price_raw'].values
y_test = test_df['price_raw'].values

X_train = train_df.drop(columns=['price_raw'])
X_val = val_df.drop(columns=['price_raw'])
X_test = test_df.drop(columns=['price_raw'])

feature_columns = X_train.columns.tolist()

# 3. Biến đổi Log1p cho mục tiêu (Giá nhà)
y_train_log = np.log1p(y_train)
y_val_log = np.log1p(y_val)
y_test_log = np.log1p(y_test)

# 4. Biến đổi Log1p cho đặc trưng Diện tích (area_raw)
if 'area_raw' in X_train.columns:
    X_train['area_raw'] = np.log1p(X_train['area_raw'])
    X_val['area_raw'] = np.log1p(X_val['area_raw'])
    X_test['area_raw'] = np.log1p(X_test['area_raw'])
    
    X_train = X_train.rename(columns={'area_raw': 'area_log'})
    X_val = X_val.rename(columns={'area_raw': 'area_log'})
    X_test = X_test.rename(columns={'area_raw': 'area_log'})
    
    feature_columns = X_train.columns.tolist()

# 5. Khởi tạo và áp dụng StandardScaler
scaler = StandardScaler()

print("[PROCESS] Khởi tạo Scaler, fit thống kê và áp dụng trên tập Train...")
X_train_scaled = scaler.fit_transform(X_train)

print("[PROCESS] Áp dụng cấu hình chuẩn hóa cũ sang tập Validation và tập Test...")
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

X_train_final = pd.DataFrame(X_train_scaled, columns=feature_columns, index=X_train.index)
X_val_final = pd.DataFrame(X_val_scaled, columns=feature_columns, index=X_val.index)
X_test_final = pd.DataFrame(X_test_scaled, columns=feature_columns, index=X_test.index)

# 6. Gom nhãn và đặc trưng
train_out = X_train_final.copy()
train_out.insert(0, 'price_log', y_train_log)

val_out = X_val_final.copy()
val_out.insert(0, 'price_log', y_val_log)

test_out = X_test_final.copy()
test_out.insert(0, 'price_log', y_test_log)

# 7. Xuất các file dữ liệu chuẩn hóa phục vụ huấn luyện mô hình
try:
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    train_out.to_csv(os.path.join(PROCESSED_DIR, "train.csv"), index=False, encoding='utf-8-sig')
    val_out.to_csv(os.path.join(PROCESSED_DIR, "val.csv"), index=False, encoding='utf-8-sig')
    test_out.to_csv(os.path.join(PROCESSED_DIR, "test.csv"), index=False, encoding='utf-8-sig')
    print("[SUCCESS] Đã lưu thành công các file dữ liệu chuẩn hóa: train.csv, val.csv, test.csv")
except Exception as e:
    print(f"[ERROR] Không thể lưu các file dữ liệu sau chia tách: {e}")
    sys.exit(1)

# 8. Lưu file cấu hình chuẩn hóa (standard_scaler.pkl) xuống đĩa phục vụ API của Backend
try:
    os.makedirs(MODEL_ARTIFACTS_DIR, exist_ok=True)
    scaler_save_path = os.path.join(MODEL_ARTIFACTS_DIR, "standard_scaler.pkl")
    joblib.dump(scaler, scaler_save_path)
    print(f"[SUCCESS] Đã lưu và cập nhật cấu hình Scaler mới tại Volume Backend: {scaler_save_path}")
    
    # LOGIC TỰ ĐỘNG CHỈ ĐỊNH LƯU VÀO FOLDER LỊCH SỬ CỦA NÍ
    os.makedirs(CURRENT_EXP_DIR, exist_ok=True)
    registry_scaler_path = os.path.join(CURRENT_EXP_DIR, "scaler.pkl")
    joblib.dump(scaler, registry_scaler_path)
    print(f"[MLOPS SUCCESS] Đã tự động nhân bản scaler.pkl vào folder lịch sử: model_registry/{CURRENT_TIMESTAMP}/scaler.pkl")
    
except Exception as e:
    print(f"[ERROR] Không thể lưu tệp cấu hình standard_scaler.pkl: {e}")
    sys.exit(1)

print("--- LUỒNG CHIA TÁCH VÀ CHUẨN HÓA HOÀN THÀNH XUẤT SẮC ---\n")