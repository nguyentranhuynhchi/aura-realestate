import numpy as np
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

def tune_ridge(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray, alphas: list = [0.01, 0.1, 1.0, 10.0]) -> tuple[Ridge, dict]:
    """Tối ưu siêu tham số alpha cho Ridge Regressor trên tập Validation."""
    best_model = None
    best_r2 = -float("inf")
    best_alpha = 1.0
    
    for a in alphas:
        m = Ridge(alpha=a, random_state=42)
        m.fit(X_train, y_train)
        score = r2_score(y_val, m.predict(X_val))
        if score > best_r2:
            best_r2 = score
            best_alpha = a
            best_model = m
            
    meta = {"best_alpha": best_alpha, "val_r2": round(best_r2, 4), "model_type": "Ridge"}
    return best_model, meta

if __name__ == "__main__":
    X = np.random.randn(50, 4)
    y = np.random.randn(50)
    m, meta = tune_ridge(X, y, X, y)
    print("Ridge tuning:", meta)