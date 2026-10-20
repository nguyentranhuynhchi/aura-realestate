import os
import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler

def scale_features(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, save_path: str = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Khởi tạo StandardScaler, fit trên tập Train và transform sang Val/Test."""
    feature_cols = [c for c in train_df.columns if c != "price_log"]
    X_tr = train_df[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    X_va = val_df[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    X_te = test_df[feature_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    scaler = StandardScaler()
    
    scaled_train = pd.DataFrame(scaler.fit_transform(X_tr), columns=feature_cols, index=train_df.index)
    scaled_val = pd.DataFrame(scaler.transform(X_va), columns=feature_cols, index=val_df.index)
    scaled_test = pd.DataFrame(scaler.transform(X_te), columns=feature_cols, index=test_df.index)
    
    # Giữ lại nhãn price_log
    scaled_train.insert(0, "price_log", train_df["price_log"].values)
    scaled_val.insert(0, "price_log", val_df["price_log"].values)
    scaled_test.insert(0, "price_log", test_df["price_log"].values)
    
    if save_path:
        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        joblib.dump(scaler, save_path)
        
    meta = {"num_scaled_features": len(feature_cols), "features_list": feature_cols, "scaler_saved": bool(save_path)}
    return scaled_train, scaled_val, scaled_test, meta

if __name__ == "__main__":
    t = pd.DataFrame({"price_log": [1.0, 2.0], "f1": [10.0, 20.0]})
    tr, v, te, m = scale_features(t, t, t)
    print("Scaled meta:", m)
