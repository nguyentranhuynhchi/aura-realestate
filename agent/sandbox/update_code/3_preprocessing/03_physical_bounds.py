import pandas as pd

def filter_physical_bounds(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Ép bộ lọc vật lý giới hạn diện tích (10-600m2), giá (<50 tỷ) và đơn giá IQR (Cell 8 Notebook 04)."""
    initial_len = len(df)
    unit_price = df["price_raw"] / df["area_raw"]

    mask = (
        (df["area_raw"] >= 10.0) & (df["area_raw"] <= 600.0) &
        (df["price_raw"] > 0.1) & (df["price_raw"] <= 50.0) &
        (unit_price <= 0.364)
    )

    # Giới hạn số phòng từ 1 đến 15 nếu có
    if "bedrooms" in df.columns:
        bed_mask = df["bedrooms"].isna() | ((df["bedrooms"] >= 1) & (df["bedrooms"] <= 15))
        mask = mask & bed_mask

    clean_df = df[mask].reset_index(drop=True)
    outliers_filtered = initial_len - len(clean_df)

    return clean_df, {
        "initial_rows": initial_len,
        "outliers_removed": outliers_filtered,
        "retained_rows": len(clean_df)
    }

if __name__ == "__main__":
    test_df = pd.DataFrame({"price_raw": [5.0, 100.0], "area_raw": [60.0, 1000.0], "bedrooms": [3, 20]})
    print(filter_physical_bounds(test_df)[1])
