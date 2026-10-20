import re
import pandas as pd

DISTRICT_MAPPING = {
    'Huyện Cần Giờ': 0, 'Huyện Củ Chi': 1, 'Huyện Hóc Môn': 2, 'Huyện Nhà Bè': 3, 'Huyện Bình Chánh': 4,
    'Quận 6': 5, 'Quận 4': 6, 'Quận 11': 7, 'Quận 5': 8, 'Quận 8': 9, 'Quận 9': 10, 'Quận 3': 11,
    'Quận 10': 12, 'Quận 2': 13, 'Quận Tân Phú': 14, 'Quận Tân Bình': 15, 'Quận Phú Nhuận': 16,
    'Quận Gò Vấp': 17, 'Quận Bình Thạnh': 18, 'Quận 12': 19, 'Quận 7': 20, 'TP. Thủ Đức': 21, 'Quận 1': 22,
}

def extract_district(addr: str) -> str:
    if pd.isna(addr): return "Không rõ"
    s = str(addr).lower()
    if "thủ đức" in s or "tp. thủ đức" in s: return "TP. Thủ Đức"
    if "bình chánh" in s: return "Huyện Bình Chánh"
    if "cần giờ" in s: return "Huyện Cần Giờ"
    if "củ chi" in s: return "Huyện Củ Chi"
    if "hóc môn" in s: return "Huyện Hóc Môn"
    if "nhà bè" in s: return "Huyện Nhà Bè"
    if "bình thạnh" in s: return "Quận Bình Thạnh"
    if "bình tân" in s: return "Quận Bình Tân"
    if "gò vấp" in s: return "Quận Gò Vấp"
    if "phú nhuận" in s: return "Quận Phú Nhuận"
    if "tân bình" in s: return "Quận Tân Bình"
    if "tân phú" in s: return "Quận Tân Phú"
    for q in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
        if re.search(rf"\bq(\.|\s*)?{q}\b|quận\s*{q}\b", s):
            return f"Quận {q}"
    return "Không rõ"

def encode_districts(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Bóc tách 22 quận huyện TP.HCM và mã hóa Ordinal theo trung vị giá (Cell 6.2 Notebook 03)."""
    df_out = df.copy()
    raw_districts = df_out["address_raw"].apply(extract_district)
    df_out["address_encoded"] = raw_districts.map(DISTRICT_MAPPING).fillna(10).astype(int)

    unmapped = int((raw_districts == "Không rõ").sum())
    return df_out, {
        "unmapped_districts": unmapped,
        "district_distribution": df_out["address_encoded"].value_counts().to_dict()
    }

if __name__ == "__main__":
    test_df = pd.DataFrame({"address_raw": ["Đường D2, Bình Thạnh", "Nguyễn Huệ, Q.1"]})
    print(encode_districts(test_df)[1])
