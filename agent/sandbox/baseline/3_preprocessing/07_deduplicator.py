import os
import pandas as pd

DEDUPLICATE_SUBSETS = [
    'price_raw', 'area_raw', 'bathrooms', 'floors', 
    'address_encoded', 'interior_encoded', 'legal_encoded',
    'dir_Bắc', 'dir_Nam', 'dir_Tây', 'dir_Tây Bắc', 'dir_Tây Nam', 
    'dir_Đông', 'dir_Đông Bắc', 'dir_Đông Nam'
]

def deduplicate_and_merge(new_df: pd.DataFrame, clean_csv_path: str) -> tuple[pd.DataFrame, dict]:
    """Lọc trùng lặp bài đăng và hợp nhất dữ liệu mới vào kho tổng clean_data.csv."""
    os.makedirs(os.path.dirname(clean_csv_path), exist_ok=True)

    if os.path.exists(clean_csv_path) and os.path.getsize(clean_csv_path) > 0:
        try:
            old_df = pd.read_csv(clean_csv_path)
            if not old_df.empty and not new_df.empty:
                combined_df = pd.concat([old_df, new_df], axis=0, ignore_index=True)
            else:
                combined_df = old_df.copy() if not old_df.empty else new_df.copy()
        except Exception:
            combined_df = new_df.copy()
    else:
        combined_df = new_df.copy()

    total_before = len(combined_df)
    existing_subsets = [c for c in DEDUPLICATE_SUBSETS if c in combined_df.columns]

    # Giữ lại bản ghi xuất hiện sau cùng (keep='last') để cập nhật giá mới nhất
    combined_df = combined_df.drop_duplicates(subset=existing_subsets, keep="last").reset_index(drop=True)
    duplicates_removed = total_before - len(combined_df)

    # Chỉ giữ lại đúng các cột đặc trưng số đã chuẩn hóa phục vụ huấn luyện
    combined_df = combined_df[existing_subsets]
    combined_df.to_csv(clean_csv_path, index=False, encoding="utf-8-sig")

    return combined_df, {
        "duplicates_removed": duplicates_removed,
        "total_clean_records": len(combined_df),
        "clean_csv_path": clean_csv_path
    }

if __name__ == "__main__":
    print("Deduplicator initialized.")
