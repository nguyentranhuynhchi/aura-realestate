import pandas as pd

def filter_property_segments(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Phân loại phân khúc bất động sản: chỉ giữ Nhà riêng & Căn hộ, loại bỏ Đất nền."""
    initial_len = len(df)
    if initial_len == 0:
        return df, {"dropped_rows": 0, "remaining_rows": 0}

    # Bỏ bài đăng rác không có cả giá lẫn diện tích
    clean_df = df.dropna(subset=["price_raw", "area_raw"]).copy()

    # Nhận diện phân khúc qua URL (0: Đất, 1: Nhà riêng, 2: Chung cư)
    if "url" in clean_df.columns:
        url_series = clean_df["url"].astype(str).str.lower()
        is_land = url_series.str.contains(r"ban-dat|ban-dat-nen", na=False)
        clean_df = clean_df[~is_land]

    dropped = initial_len - len(clean_df)
    return clean_df.reset_index(drop=True), {
        "initial_rows": initial_len,
        "dropped_rows": dropped,
        "remaining_rows": len(clean_df)
    }

if __name__ == "__main__":
    test_df = pd.DataFrame({"url": ["ban-dat-nen-quan-9", "ban-nha-rieng-q1"], "price_raw": [1, 2], "area_raw": [50, 60]})
    res_df, meta = filter_property_segments(test_df)
    print(meta)