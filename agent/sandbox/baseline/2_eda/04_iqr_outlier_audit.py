import pandas as pd
import numpy as np

def audit_iqr_outliers(df: pd.DataFrame, price_col: str = "price_raw", area_col: str = "area_raw") -> dict:
    """Khám phá Outlier đơn giá (Tỷ/m2) bằng phương pháp biên IQR (Cell 7 Notebook 03)."""
    p = pd.to_numeric(df[price_col], errors="coerce")
    a = pd.to_numeric(df[area_col], errors="coerce")
    valid_mask = (p > 0) & (a > 0)

    if valid_mask.sum() < 10:
        return {"status": "insufficient_data", "outlier_count": 0}

    unit_price = p[valid_mask] / a[valid_mask]
    q1 = float(unit_price.quantile(0.25))
    q3 = float(unit_price.quantile(0.75))
    iqr = q3 - q1
    upper_bound = round(q3 + 1.5 * iqr, 4)  # ~0.364 Tỷ/m2
    lower_bound = max(0.005, round(q1 - 1.5 * iqr, 4))

    outlier_count = int(((unit_price > upper_bound) | (unit_price < lower_bound)).sum())

    return {
        "unit_price_q1": round(q1, 4),
        "unit_price_q3": round(q3, 4),
        "upper_bound_billion_per_m2": upper_bound,
        "lower_bound_billion_per_m2": lower_bound,
        "outliers_detected": outlier_count,
        "status": "warning" if outlier_count > 0 else "healthy"
    }

if __name__ == "__main__":
    test_df = pd.DataFrame({"price_raw": [2.0, 3.5, 5.0, 50.0], "area_raw": [50, 60, 70, 10]})
    print(audit_iqr_outliers(test_df))
