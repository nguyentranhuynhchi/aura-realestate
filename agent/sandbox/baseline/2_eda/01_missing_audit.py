import pandas as pd

def audit_missing_values(df: pd.DataFrame) -> dict:
    """Quét và tính toán tỷ lệ khuyết thiếu (Null / NaN / N/A) của tất cả các cột."""
    total_rows = len(df)
    if total_rows == 0:
        return {"status": "empty_dataframe", "missing_rates": {}}

    missing_info = {}
    high_missing = []
    for col in df.columns:
        null_count = df[col].isna().sum() + (df[col].astype(str).str.strip().isin(["N/A", "nan", "", "None"])).sum()
        rate = round(float(null_count / total_rows), 4)
        missing_info[col] = rate
        if rate > 0.40:
            high_missing.append(col)

    return {
        "total_samples": total_rows,
        "missing_rates": missing_info,
        "high_missing_features": high_missing,
        "status": "warning" if high_missing else "healthy"
    }

if __name__ == "__main__":
    test_df = pd.DataFrame({"a": [1, None, "N/A"], "b": ["x", "y", "z"]})
    print(audit_missing_values(test_df))
