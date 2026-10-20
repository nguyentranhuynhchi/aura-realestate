import pandas as pd

INTERIOR_MAPPING = {
    'Khác / Thỏa thuận': 0, 'Nội thất cơ bản': 1, 'Không nội thất': 2,
    'Không rõ (NaN)': 3, 'Đầy đủ nội thất': 4, 'Bàn giao thô': 5,
}

LEGAL_MAPPING = {
    'Không rõ': 0, 'Chưa Sổ / HDMB': 1, 'Có Sổ': 2,
}

VALID_DIRECTIONS = ['Bắc', 'Nam', 'Tây', 'Tây Bắc', 'Tây Nam', 'Đông', 'Đông Bắc', 'Đông Nam']

def standardize_interior(val) -> str:
    s = str(val).lower() if not pd.isna(val) else ""
    if any(k in s for k in ["đầy đủ", "full", "cao cấp"]): return "Đầy đủ nội thất"
    if "cơ bản" in s: return "Nội thất cơ bản"
    if "thô" in s: return "Bàn giao thô"
    if "không nội thất" in s: return "Không nội thất"
    if "thỏa thuận" in s or "khác" in s: return "Khác / Thỏa thuận"
    return "Không rõ (NaN)"

def standardize_legal(val) -> str:
    s = str(val).lower() if not pd.isna(val) else ""
    if any(k in s for k in ["sổ đỏ", "sổ hồng", "có sổ", "đã có sổ"]): return "Có Sổ"
    if any(k in s for k in ["chưa sổ", "hdmb", "hợp đồng mua bán"]): return "Chưa Sổ / HDMB"
    return "Không rõ"

def encode_categorical_features(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Mã hóa Ordinal cho Nội thất, Pháp lý và One-Hot cho 8 hướng nhà (Cell 6, 6.4 Notebook 03)."""
    df_out = df.copy()

    # 1. Nội thất & Pháp lý
    clean_interior = df_out["interior"].apply(standardize_interior)
    clean_legal = df_out["legal_status"].apply(standardize_legal)
    df_out["interior_encoded"] = clean_interior.map(INTERIOR_MAPPING).fillna(3).astype(int)
    df_out["legal_encoded"] = clean_legal.map(LEGAL_MAPPING).fillna(0).astype(int)

    # 2. One-hot hướng nhà
    for d in VALID_DIRECTIONS:
        df_out[f"dir_{d}"] = (df_out["house_direction"].astype(str).str.strip() == d).astype(int)

    return df_out, {
        "interior_stats": clean_interior.value_counts().to_dict(),
        "legal_stats": clean_legal.value_counts().to_dict(),
        "direction_dummies_created": len(VALID_DIRECTIONS)
    }

if __name__ == "__main__":
    test_df = pd.DataFrame({"interior": ["Full nội thất"], "legal_status": ["Sổ hồng riêng"], "house_direction": ["Đông Nam"]})
    print(encode_categorical_features(test_df)[1])
