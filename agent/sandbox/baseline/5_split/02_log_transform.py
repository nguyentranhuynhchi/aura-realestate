import numpy as np
import pandas as pd

def apply_log_transform(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Biến đổi Log1p cho giá nhà (price_raw -> price_log) và diện tích (area_raw -> area_log)."""
    dfs = [train_df.copy(), val_df.copy(), test_df.copy()]
    for d in dfs:
        if "price_raw" in d.columns:
            s_price = pd.to_numeric(d["price_raw"], errors="coerce").fillna(0.0).astype(float)
            d["price_log"] = np.log1p(s_price.values)
            d.drop(columns=["price_raw"], inplace=True)
        if "area_raw" in d.columns:
            s_area = pd.to_numeric(d["area_raw"], errors="coerce").fillna(0.0).astype(float)
            d["area_log"] = np.log1p(s_area.values)
            d.drop(columns=["area_raw"], inplace=True)
            
    meta = {
        "price_log_applied": True,
        "area_log_applied": True,
        "train_price_log_mean": round(float(dfs[0]["price_log"].mean()), 4) if "price_log" in dfs[0] else 0.0
    }
    return dfs[0], dfs[1], dfs[2], meta

if __name__ == "__main__":
    t = pd.DataFrame({"price_raw": [2.5, 5.0], "area_raw": [50.0, 100.0]})
    tr, v, te, m = apply_log_transform(t, t, t)
    print("Log transform columns:", tr.columns.tolist(), m)
