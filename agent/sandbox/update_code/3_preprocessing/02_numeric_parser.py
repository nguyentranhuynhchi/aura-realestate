import re
import pandas as pd

def parse_price(val) -> float:
    if pd.isna(val) or "thỏa thuận" in str(val).lower():
        return 0.0
    try:
        s = str(val).strip().lower().replace(",", ".")
        m = re.search(r"([\d.]+)\s*tỷ", s)
        if m: return float(m.group(1))
        m = re.search(r"([\d.]+)\s*triệu", s)
        if m: return float(m.group(1)) / 1000.0
        m = re.search(r"([\d.]+)", s)
        return float(m.group(1)) if m else 0.0
    except Exception:
        return 0.0

def parse_area(val) -> float:
    if pd.isna(val): return 0.0
    try:
        s = str(val).strip().lower().replace(",", ".")
        m = re.search(r"([\d.]+)", s)
        return float(m.group(1)) if m else 0.0
    except Exception:
        return 0.0

def parse_numeric_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Chuyển đổi các cột chuỗi dạng văn bản sang số thực chuẩn hóa."""
    df_out = df.copy()
    df_out["price_raw"] = df_out["price_raw"].apply(parse_price)
    df_out["area_raw"] = df_out["area_raw"].apply(parse_area)

    for col in ["bedrooms", "bathrooms", "floors"]:
        if col in df_out.columns:
            df_out[col] = df_out[col].astype(str).str.extract(r"(\d+)")[0]
            df_out[col] = pd.to_numeric(df_out[col], errors="coerce")

    # Loại bỏ những dòng có giá hoặc diện tích = 0
    df_out = df_out[(df_out["price_raw"] > 0) & (df_out["area_raw"] > 0)].reset_index(drop=True)

    return df_out, {
        "valid_numeric_rows": len(df_out),
        "mean_price": round(float(df_out["price_raw"].mean()), 2),
        "mean_area": round(float(df_out["area_raw"].mean()), 2)
    }

if __name__ == "__main__":
    test_df = pd.DataFrame({"price_raw": ["3.5 tỷ", "850 triệu"], "area_raw": ["65 m2", "120.5m2"]})
    print(parse_numeric_columns(test_df)[1])
