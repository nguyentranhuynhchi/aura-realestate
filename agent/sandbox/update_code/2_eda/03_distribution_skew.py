import pandas as pd
from scipy.stats import skew, kurtosis

def analyze_skewness(df: pd.DataFrame, target_col: str = "price_raw", area_col: str = "area_raw") -> dict:
    """Tính độ lệch phân phối (Skewness & Kurtosis) để quyết định áp dụng Log Transform."""
    results = {}
    for col in [target_col, area_col]:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(s) > 10:
                col_skew = float(skew(s))
                col_kurt = float(kurtosis(s))
                results[col] = {
                    "skewness": round(col_skew, 4),
                    "kurtosis": round(col_kurt, 4),
                    "needs_log_transform": bool(abs(col_skew) > 1.0)
                }

    # Update recommendation based on skewness
    if any(v["needs_log_transform"] for v in results.values()):
        results["recommendation"] = "apply_log1p"
    else:
        results["recommendation"] = "keep_linear"

    return results

if __name__ == "__main__":
    test_df = pd.DataFrame({"price_raw": [1, 2, 2.5, 3, 50, 100]})
    print(analyze_skewness(test_df))