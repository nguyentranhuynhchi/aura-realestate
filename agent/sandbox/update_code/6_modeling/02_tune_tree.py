import numpy as np
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import r2_score

def tune_decision_tree(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray) -> tuple[DecisionTreeRegressor, dict]:
    """Tối ưu siêu tham số max_depth và min_samples_split cho Decision Tree."""
    param_grid = [
        {"max_depth": 10, "min_samples_split": 10},
        {"max_depth": 15, "min_samples_split": 20},
        {"max_depth": 20, "min_samples_split": 30}
    ]
    best_model = None
    best_r2 = -float("inf")
    best_params = {}
    
    for params in param_grid:
        m = DecisionTreeRegressor(max_depth=params["max_depth"], min_samples_split=params["min_samples_split"], random_state=42)
        m.fit(X_train, y_train)
        score = r2_score(y_val, m.predict(X_val))
        if score > best_r2:
            best_r2 = score
            best_params = params
            best_model = m
            
    meta = {"best_params": best_params, "val_r2": round(float(best_r2), 4), "model_type": "DecisionTree"}
    return best_model, meta

if __name__ == "__main__":
    X = np.random.randn(50, 4)
    y = np.random.randn(50)
    m, meta = tune_decision_tree(X, y, X, y)
    print("Tree tuning:", meta)
