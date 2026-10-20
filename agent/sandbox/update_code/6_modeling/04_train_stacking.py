import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.metrics import r2_score

def train_stacking_ensemble(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray, base_models: dict = None) -> tuple[StackingRegressor, dict]:
    """Huấn luyện StackingRegressor kết hợp Ridge, DecisionTree và RandomForest với Meta-Learner LinearRegression."""
    ridge = base_models.get("ridge") if base_models else Ridge(alpha=1.0, random_state=42)
    tree = base_models.get("tree") if base_models else DecisionTreeRegressor(max_depth=15, min_samples_split=20, random_state=42)
    rf = base_models.get("rf") if base_models else RandomForestRegressor(n_estimators=50, max_depth=20, min_samples_split=8, random_state=42, n_jobs=-1)
    
    stacking = StackingRegressor(
        estimators=[("ridge", ridge), ("tree", tree), ("rf", rf)],
        final_estimator=LinearRegression(),
        cv=5,
        n_jobs=-1
    )
    stacking.fit(X_train, y_train)
    val_r2 = r2_score(y_val, stacking.predict(X_val))
    
    meta = {
        "model_architecture": "StackingRegressor[Ridge,DecisionTree,RandomForest]->LinearRegression",
        "val_r2": round(float(val_r2), 4),
        "cv_folds": 5
    }
    return stacking, meta

if __name__ == "__main__":
    X = np.random.randn(60, 4)
    y = np.random.randn(60)
    m, meta = train_stacking_ensemble(X, y, X, y)
    print("Stacking meta:", meta)
