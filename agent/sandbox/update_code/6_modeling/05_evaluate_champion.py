import os
import json
import joblib
import shutil
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error, root_mean_squared_error

def evaluate_and_promote(model, X_test: np.ndarray, y_test: np.ndarray, exp_dir: str, registry_dir: str, backend_dir: str = None) -> dict:
    """Đánh giá mô hình trên tập Test, so găng Champion vs Challenger và tự động thăng cấp nếu vượt trội."""
    preds = model.predict(X_test)
    r2 = float(r2_score(y_test, preds))
    mae = float(mean_absolute_error(y_test, preds))
    rmse = float(root_mean_squared_error(y_test, preds))
    
    os.makedirs(exp_dir, exist_ok=True)
    challenger_model_path = os.path.join(exp_dir, "model.pkl")
    joblib.dump(model, challenger_model_path)
    
    # Tìm Champion tốt nhất trước đó
    r2_champion = -999.0
    best_champ_dir = None
    if os.path.exists(registry_dir):
        folders = [f for f in os.listdir(registry_dir) if os.path.isdir(os.path.join(registry_dir, f)) and f != os.path.basename(exp_dir)]
        folders.sort(reverse=True)
        if folders:
            best_champ_dir = os.path.join(registry_dir, folders[0])
            m_path = os.path.join(best_champ_dir, "metrics.json")
            if os.path.exists(m_path):
                with open(m_path, "r", encoding="utf-8") as f:
                    r2_champion = json.load(f).get("R2_score", -999.0)

    is_promoted = r2 > r2_champion
    status = "Champion" if is_promoted else "Challenger"
    
    metrics = {"R2_score": round(r2, 4), "MAE": round(mae, 4), "RMSE": round(rmse, 4), "status": status, "previous_champion_r2": round(r2_champion, 4)}
    with open(os.path.join(exp_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)
        
    if backend_dir and is_promoted:
        os.makedirs(backend_dir, exist_ok=True)
        shutil.copy(challenger_model_path, os.path.join(backend_dir, "best_stacking_regressor.pkl"))
        scaler_src = os.path.join(exp_dir, "scaler.pkl")
        if os.path.exists(scaler_src):
            shutil.copy(scaler_src, os.path.join(backend_dir, "standard_scaler.pkl"))
        
    return metrics

if __name__ == "__main__":
    from sklearn.linear_model import LinearRegression
    dummy = LinearRegression().fit([[1], [2]], [1, 2])
    print(evaluate_and_promote(dummy, np.array([[1], [2]]), np.array([1, 2]), "./tmp_exp", "./tmp_reg"))
