import pandas as pd

def check_multicollinearity(df: pd.DataFrame, threshold: float = 0.85) -> dict:
    """Tính toán ma trận tương quan Pearson để phát hiện các cặp biến đa cộng tuyến."""
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if len(num_cols) < 2:
        return {"status": "insufficient_numeric_cols", "collinear_pairs": []}

    corr_matrix = df[num_cols].corr(method="pearson")
    collinear_pairs = []

    for i in range(len(num_cols)):
        for j in range(i + 1, len(num_cols)):
            col1, col2 = num_cols[i], num_cols[j]
            corr_val = float(corr_matrix.loc[col1, col2])
            if abs(corr_val) >= threshold:
                collinear_pairs.append({
                    "feature_1": col1,
                    "feature_2": col2,
                    "correlation": round(corr_val, 4)
                })

    return {
        "collinear_pairs": collinear_pairs,
        "action_required": "drop_or_combine" if collinear_pairs else "none",
        "status": "warning" if collinear_pairs else "healthy"
    }

if __name__ == "__main__":
    test_df = pd.DataFrame({"bed": [1, 2, 3], "bath": [1.1, 2.05, 2.95]})
    print(check_multicollinearity(test_df))
