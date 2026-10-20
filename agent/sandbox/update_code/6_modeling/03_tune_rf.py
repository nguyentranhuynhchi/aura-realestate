import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score

def tune_random_forest(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray) -> tuple[RandomForestRegressor, dict]:
    """Tối ưu tham số cơ bản cho Random Forest Regressor trên tập Validation."""
    param_grid = [
        {"n_estimators": 30, "max_depth": 15, "min_samples_split": 8},
        {"n_estimators": 50, "max_depth": 20, "min_samples_split": 8}
    ]
    best_model = None
    best_r2 = -float("inf")
    best_params = {}
    
    for params in param_grid:
        m = RandomForestRegressor(
            n_estimators=params["n_estimators"], max_depth=params["max_depth"], 
            min_samples_split=params["min_samples_split"], random_state=42, n_jobs=-1
        )
        m.fit(X_train, y_train)
        score = r2_score(y_val, m.predict(X_val))
        if score > best_r2:
            best_r2 = score
            best_params = params
            best_model = m
            
    meta = {"best_params": best_params, "val_r2": round(float(best_r2), 4), "model_type": "RandomForest"}
    return best_model, meta

if __name__ == "__main__":
    X = np.random.randn(50, 4)
    y = np.random.randn(50)
    m, meta = tune_random_forest(X, y, X, y)
    print("RF tuning:", meta)
