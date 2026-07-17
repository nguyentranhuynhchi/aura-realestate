import os
import sys
import joblib
import json
import shutil
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_error, root_mean_squared_error
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, StackingRegressor

# Đọc tham số folder lịch sử truyền từ run_pipeline sang (nếu không có thì báo lỗi)
if len(sys.argv) < 2:
    print("[ERROR] Thiếu tham số timestamp của folder lịch sử! Vui lòng chạy qua file run_pipeline.py.")
    sys.exit(1)

CURRENT_TIMESTAMP = sys.argv[1]

# Định nghĩa các đường dẫn
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "data", "processed"))
MODEL_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "backend", "models"))
REGISTRY_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "model_registry"))

TRAIN_PATH = os.path.join(DATA_DIR, "train.csv")
VAL_PATH = os.path.join(DATA_DIR, "val.csv")
TEST_PATH = os.path.join(DATA_DIR, "test.csv")
MODEL_VOLUME_PATH = os.path.join(MODEL_DIR, "best_stacking_regressor.pkl")
SCALER_VOLUME_PATH = os.path.join(MODEL_DIR, "scaler.pkl")

CURRENT_EXP_DIR = os.path.join(REGISTRY_DIR, CURRENT_TIMESTAMP)

print("\n--- BẮT ĐẦU LUỒNG HUẤN LUYỆN MÔ HÌNH STACKING ENSEMBLE ---")

# 1. Đọc dữ liệu đã qua xử lý
if not (os.path.exists(TRAIN_PATH) and os.path.exists(VAL_PATH) and os.path.exists(TEST_PATH)):
    print("[ERROR] Thiếu các file train.csv, val.csv hoặc test.csv tại thư mục processed.")
    sys.exit(1)

train_df = pd.read_csv(TRAIN_PATH)
val_df = pd.read_csv(VAL_PATH)
test_df = pd.read_csv(TEST_PATH)

X_train = train_df.drop(columns=['price_log']).values
y_train = train_df['price_log'].values
X_val = val_df.drop(columns=['price_log']).values
y_val = val_df['price_log'].values
X_test = test_df.drop(columns=['price_log']).values
y_test = test_df['price_log'].values

# 2. Khởi tạo các Base Models
best_ridge = Ridge(alpha=1.0, random_state=42)
best_tree = DecisionTreeRegressor(max_depth=15, min_samples_split=20, max_features=None, random_state=42)
best_rf = RandomForestRegressor(n_estimators=50, max_depth=20, min_samples_split=8, max_features=None, random_state=42, n_jobs=-1)

# 3. Khởi tạo Stacking Regressor
stacking_model = StackingRegressor(
    estimators=[('ridge', best_ridge), ('tree', best_tree), ('rf', best_rf)], 
    final_estimator=LinearRegression(), cv=5, n_jobs=-1
)

# 4. Huấn luyện mô hình thách thức (Challenger)
print("[TRAIN] Đang huấn luyện mô hình Stacking Regressor ứng viên mới...")
stacking_model.fit(X_train, y_train)

# 5. Đánh giá chỉ số thực tế trên tập Test
preds_test = stacking_model.predict(X_test)
r2_challenger = r2_score(y_test, preds_test)
mae_challenger = mean_absolute_error(y_test, preds_test)
rmse_challenger = root_mean_squared_error(y_test, preds_test)

print(f"\n [CHALLENGER METRICS] Mô hình ứng viên mới đạt R2 trên tập Test = {r2_challenger:.4f}")

# =================================================================
#  MỤC 6: LƯU SẢN PHẨM MỚI VÀO REGISTRY TRƯỚC (CHƯA ĐỘNG VÀO VOLUME)
# =================================================================
# Tạo folder lịch sử hiện tại nếu chưa có
os.makedirs(CURRENT_EXP_DIR, exist_ok=True)

# Ghi file model mới train vào đúng folder registry của ngày hôm nay
CHALLENGER_MODEL_REGISTRY = os.path.join(CURRENT_EXP_DIR, "model.pkl")
joblib.dump(stacking_model, CHALLENGER_MODEL_REGISTRY)

# Ghi file thông số metrics tạm thời của Challenger vào folder registry
metrics_data = {
    "R2_score": r2_challenger,
    "MAE": mae_challenger,
    "RMSE": rmse_challenger,
    "status": "Challenger"
}
with open(os.path.join(CURRENT_EXP_DIR, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics_data, f, indent=4)

print(f"\n[REGISTRY] Đã đóng băng mô hình ứng viên mới tại: model_registry/{CURRENT_TIMESTAMP}/model.pkl")


# =================================================================
#  MỤC 7:  ĐỐI SÁNH THẬT & PHÂN PHỐI RA VOLUME BACKEND
# =================================================================
# Định nghĩa đường dẫn đích đến của Volume Backend thực tế
VOLUME_MODEL_PATH = os.path.join(MODEL_DIR, "best_stacking_regressor.pkl")
VOLUME_SCALER_PATH = os.path.join(MODEL_DIR, "standard_scaler.pkl")

# Quét tìm con Champion cũ tốt nhất từ các folder lịch sử trước đó
all_folders = [f for f in os.listdir(REGISTRY_DIR) if os.path.isdir(os.path.join(REGISTRY_DIR, f)) and f != CURRENT_TIMESTAMP and f != ".git"]

r2_champion = -999.0
best_champion_dir = None

if all_folders:
    all_folders.sort(reverse=True)
    best_champion_dir = os.path.join(REGISTRY_DIR, all_folders[0])
    champion_json_path = os.path.join(best_champion_dir, "metrics.json")
    
    if os.path.exists(champion_json_path):
        with open(champion_json_path, "r", encoding="utf-8") as f:
            r2_champion = json.load(f).get("R2_score", -999.0)
        print(f"  [CHAMPION FOUND] Tìm thấy phiên bản cũ tốt nhất tại ({all_folders[0]}) | R2 = {r2_champion:.4f}")
else:
    print(" [MLOPS] Đây là lần chạy đầu tiên, chưa có folder lịch sử cũ.")
    # Nếu lần đầu chạy mà volume đang có sẵn file, nạp lên lấy điểm làm mốc
    if os.path.exists(VOLUME_MODEL_PATH):
        try:
            old_model = joblib.load(VOLUME_MODEL_PATH)
            old_preds = old_model.predict(X_test)
            r2_champion = r2_score(y_test, old_preds)
            print(f"  [VOLUME BASELINE] Lấy điểm model hiện tại ở Volume làm mốc | R2 = {r2_champion:.4f}")
        except Exception:
            print("  Không đọc được file Volume gốc. Mặc định đưa mô hình mới lên luôn.")

# --- ĐỐI SÁNH XÁC ĐỊNH FOLDER XUẤT SẮC NHẤT ---
print(f"\n[SO TÀI] Champion R2: {r2_champion:.4f} vs Challenger R2: {r2_challenger:.4f}")

if r2_challenger > r2_champion:
    print(f" [ PHẢN HỒI]: MÔ HÌNH MỚI CHIẾN THẮNG!")
    print(f"   -> Cập nhật trạng thái folder {CURRENT_TIMESTAMP} thành Champion.")
    print(f"   -> Đẩy cặp file (model + scaler) của folder MỚI ra Volume Backend.")
    
    # Cập nhật trạng thái trong Registry của chính nó
    metrics_data["status"] = "Champion"
    with open(os.path.join(CURRENT_EXP_DIR, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=4)
        
    # BỐC TỪ FOLDER MỚI RA VOLUME
    shutil.copy(CHALLENGER_MODEL_REGISTRY, VOLUME_MODEL_PATH)
    if os.path.exists(os.path.join(CURRENT_EXP_DIR, "scaler.pkl")):
        shutil.copy(os.path.join(CURRENT_EXP_DIR, "scaler.pkl"), VOLUME_SCALER_PATH)
        
else:
    print(f" [ PHẢN HỒI]: MÔ HÌNH CŨ GIỮ VỮNG PHONG ĐỘ!")
    if best_champion_dir:
        print(f"   -> Bốc cặp file (model + scaler) từ folder CŨ ({os.path.basename(best_champion_dir)}) ra đè lại Volume Backend.")
        
        # BỐC TỪ FOLDER CŨ RA ĐÈ LẠI VOLUME ĐỂ BẢO VỆ HỆ THỐNG
        if os.path.exists(os.path.join(best_champion_dir, "model.pkl")):
            shutil.copy(os.path.join(best_champion_dir, "model.pkl"), VOLUME_MODEL_PATH)
        if os.path.exists(os.path.join(best_champion_dir, "scaler.pkl")):
            shutil.copy(os.path.join(best_champion_dir, "scaler.pkl"), VOLUME_SCALER_PATH)
    else:
        # Lần chạy đầu tiên nhưng con mới tệ hơn con có sẵn ở volume
        print("   -> Giữ nguyên trạng thái cặp file gốc đang nằm ở Volume Backend.")

print("\n--- LUỒNG HUẤN LUYỆN VÀ PHÂN PHỐI MÔ HÌNH HOÀN THÀNH ---\n")