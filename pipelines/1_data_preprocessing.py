import os
import re
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


# =========================================================================
# CÁC MAPPING / ENCODING CỐ ĐỊNH — LẤY NGUYÊN VĂN TỪ FILE 04 (Cell mã hóa)
# =========================================================================

DISTRICT_MAPPING = {
    'Huyện Cần Giờ': 0, 'Huyện Củ Chi': 1, 'Huyện Hóc Môn': 2, 'Huyện Nhà Bè': 3, 'Huyện Bình Chánh': 4,
    'Quận 6': 5, 'Quận 4': 6, 'Quận 11': 7, 'Quận 5': 8, 'Quận 8': 9, 'Quận 9': 10, 'Quận 3': 11,
    'Quận 10': 12, 'Quận 2': 13, 'Quận Tân Phú': 14, 'Quận Tân Bình': 15, 'Quận Phú Nhuận': 16,
    'Quận Gò Vấp': 17, 'Quận Bình Thạnh': 18, 'Quận 12': 19, 'Quận 7': 20, 'TP. Thủ Đức': 21, 'Quận 1': 22,
}

INTERIOR_MAPPING = {
    'Khác / Thỏa thuận': 0, 'Nội thất cơ bản': 1, 'Không nội thất': 2,
    'Không rõ (NaN)': 3, 'Đầy đủ nội thất': 4, 'Bàn giao thô': 5,
}

LEGAL_MAPPING = {
    'Không rõ': 0, 'Chưa Sổ / HDMB': 1, 'Có Sổ': 2,
}

# 8 hướng nhà hợp lệ dùng để One-Hot (đã loại 'Không rõ' làm baseline, đúng
# như file 04 đã drop cột 'dir_Không rõ' để tránh bẫy Dummy Variable)
VALID_DIRECTIONS = ['Bắc', 'Nam', 'Tây', 'Tây Bắc', 'Tây Nam', 'Đông', 'Đông Bắc', 'Đông Nam']
DIRECTION_DUMMY_COLUMNS = [f'dir_{d}' for d in VALID_DIRECTIONS]

# Các cột rác bị loại bỏ ngay từ file 01
REDUNDANT_COLUMNS = ['seller_name', 'phone_number', 'price_trend', 'ownership_type', 'description', 'surrounding_area']


class HousingDataPipeline:
    """
    Pipeline end-to-end: raw scraped data (dạng houses_raw.csv, đã có đủ 18
    cột như 01_text_parsing_and_feature_enhancement.ipynb) -> ma trận số
    sạch sẵn sàng đưa vào huấn luyện / dự đoán mô hình giá Nhà riêng.
    """

    def __init__(self, artifacts_dir: str = '../models'):
        self.artifacts_dir = artifacts_dir
        self.scaler_path = os.path.join(artifacts_dir, 'standard_scaler.pkl')
        self.stats_path = os.path.join(artifacts_dir, 'fill_stats.json')

        self.scaler = StandardScaler()
        self.fill_stats = {}  # {'bedrooms_median': .., 'bathrooms_median': ..}

    # =====================================================================
    # FILE 01 — TEXT PARSING & FEATURE ENHANCEMENT
    # =====================================================================
    @staticmethod
    def _classify_url_segment(url_str):
        """0: Đất, 1: Nhà riêng, 2: Chung cư — y hệt file 01."""
        if pd.isna(url_str):
            return 1
        u = str(url_str).lower()
        if 'ban-dat' in u:
            return 0
        elif 'chung-cu' in u or 'can-ho' in u:
            return 2
        return 1

    @staticmethod
    def _extract_property_type(url_segment):
        """Suy ra property type (title) chỉ dựa trên phân khúc URL — y hệt file 01."""
        if url_segment == 0:
            return 'Đất nền / Đất thổ cư'
        if url_segment == 2:
            return 'Chung cư / Căn hộ'
        return 'Nhà riêng'

    @staticmethod
    def _clean_price(price_str):
        """Trích giá trị số (đơn vị Tỷ VNĐ), phân biệt 'tỷ' và 'triệu' — y hệt file 01."""
        if pd.isna(price_str) or 'thỏa thuận' in str(price_str).lower():
            return np.nan
        try:
            s = str(price_str).strip().lower().replace(',', '.')
            m = re.search(r'([\d.]+)\s*tỷ', s)
            if m:
                return float(m.group(1))
            m = re.search(r'([\d.]+)\s*triệu', s)
            if m:
                return float(m.group(1)) / 1000.0
            m = re.search(r'([\d.]+)', s)
            return float(m.group(1)) if m else np.nan
        except ValueError:
            # Bọc lỗi cho các chuỗi dị dạng không ép kiểu float được
            return np.nan

    @staticmethod
    def _clean_area(area_str):
        """Trích diện tích (đơn vị m2) — y hệt file 01."""
        if pd.isna(area_str):
            return np.nan
        try:
            s = str(area_str).strip().lower().replace(',', '.')
            m = re.search(r'([\d.]+)', s)
            return float(m.group(1)) if m else np.nan
        except ValueError:
            # Bọc lỗi an toàn cho các chuỗi lỗi nhập liệu kiểu '4.335.7'
            return np.nan
        
    @staticmethod
    def _clean_to_integer(val):
        """Dùng cho bedrooms/bathrooms/floors — y hệt file 01."""
        if pd.isna(val):
            return np.nan
        m = re.search(r'(\d+)', str(val))
        return int(m.group(1)) if m else np.nan

    def _stage_01_text_parsing(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df = df.drop(columns=['id'], errors='ignore')

        # Loại các dòng lỗi định dạng số đã phát hiện trong quá trình EDA file 01
        if 'price_raw' in df.columns:
            df = df[~df['price_raw'].astype(str).str.contains(r'\d+\.\d+,', regex=True)].reset_index(drop=True)
        if 'area_raw' in df.columns:
            df = df[~df['area_raw'].astype(str).str.contains(r'\d+\.\d+,', regex=True)].reset_index(drop=True)

        df['url'] = df['url'].apply(self._classify_url_segment)
        df['title'] = df['url'].apply(self._extract_property_type)

        df['price_raw'] = df['price_raw'].apply(self._clean_price)
        df['area_raw'] = df['area_raw'].apply(self._clean_area)

        for col in ['bedrooms', 'bathrooms', 'floors']:
            df[col] = df[col].apply(self._clean_to_integer)

        if 'legal_status' in df.columns:
            df['legal_status'] = (
                df['legal_status'].astype(str).str.strip().str.rstrip('.').replace('nan', np.nan)
            )

        df = df.drop(columns=REDUNDANT_COLUMNS, errors='ignore')
        return df

    # =====================================================================
    # FILE 02 — LỌC RIÊNG PHÂN KHÚC "NHÀ RIÊNG"
    # =====================================================================
    @staticmethod
    def _stage_02_filter_house_segment(df: pd.DataFrame) -> pd.DataFrame:
        return df[df['title'] == 'Nhà riêng'].reset_index(drop=True)

    # =====================================================================
    # FILE 04 — ADVANCED PREPROCESSING
    # =====================================================================
    @staticmethod
    def _extract_district(address):
        if pd.isna(address):
            return 'Không rõ'
        addr = str(address).lower().strip()

        if 'thủ đức' in addr:
            return 'TP. Thủ Đức'
        if 'bình chánh' in addr:
            return 'Huyện Bình Chánh'
        if 'cần giờ' in addr:
            return 'Huyện Cần Giờ'
        if 'củ chi' in addr:
            return 'Huyện Củ Chi'
        if 'hóc môn' in addr:
            return 'Huyện Hóc Môn'
        if 'nhà bè' in addr:
            return 'Huyện Nhà Bè'

        if 'bình thạnh' in addr or 'q. bình' in addr:
            return 'Quận Bình Thạnh'
        if 'bình tân' in addr:
            return 'Quận Bình Tân'
        if 'gò vấp' in addr or 'q. gò' in addr:
            return 'Quận Gò Vấp'
        if 'phú nhuận' in addr or 'q. phú' in addr:
            return 'Quận Phú Nhuận'
        if 'tân bình' in addr:
            return 'Quận Tân Bình'
        if 'tân phú' in addr:
            return 'Quận Tân Phú'

        match_num = re.search(r'(?:quận|q\.?)\s*([0-9]+)', addr)
        if match_num:
            num = int(match_num.group(1))
            if 1 <= num <= 12:
                return f"Quận {num}"

        return 'Khác / Ngoại tỉnh'

    @staticmethod
    def _clean_legal(legal):
        if pd.isna(legal):
            return 'Không rõ'
        legal = str(legal).lower().strip()
        if any(k in legal for k in ['sổ hồng', 'sổ đỏ', 'đã có sổ', 'sổ riêng', 'chính chủ', 'hoàn công']):
            return 'Có Sổ'
        elif any(k in legal for k in ['hợp đồng mua bán', 'hdmb', 'chờ sổ', 'giấy tay', 'đang chờ']):
            return 'Chưa Sổ / HDMB'
        return 'Không rõ'

    @staticmethod
    def _extract_interior_clean(interior_text):
        if pd.isna(interior_text):
            return 'Không rõ (NaN)'
        s = str(interior_text).lower().strip()
        if any(k in s for k in ['đầy đủ', 'full', 'cao cấp', 'sang xịn', 'để lại nội thất']):
            return 'Đầy đủ nội thất'
        if 'cơ bản' in s:
            return 'Nội thất cơ bản'
        if 'không nội thất' in s or 'nhà trống' in s:
            return 'Không nội thất'
        if 'thô' in s:
            return 'Bàn giao thô'
        return 'Khác / Thỏa thuận'

    @staticmethod
    def _clean_direction(direction):
        if pd.isna(direction):
            return 'Không rõ'
        d = str(direction).lower().replace('-', ' ').strip()
        for v in ['đông nam', 'đông bắc', 'tây nam', 'tây bắc', 'đông', 'tây', 'nam', 'bắc']:
            if v in " ".join(d.split()):
                return v.title()
        return 'Không rõ'

    def _stage_04_advanced_preprocessing(self, df: pd.DataFrame, is_training: bool) -> pd.DataFrame:
        df = df.copy()
        df = df.drop(columns=['url', 'title'], errors='ignore')

        # --- Địa chỉ: gom nhóm quận/huyện + xóa nhiễu địa lý ---
        df['district_clean'] = df['address_raw'].apply(self._extract_district)
        df = df[~df['district_clean'].isin(['Khác / Ngoại tỉnh', 'Không rõ'])].reset_index(drop=True)
        df = df.drop(columns=['address_raw'], errors='ignore')

        # --- Pháp lý: gom nhóm 3 nhãn bản chất ---
        df['legal_clean'] = df['legal_status'].apply(self._clean_legal)
        df = df.drop(columns=['legal_status'], errors='ignore')

        # --- Nội thất: gom nhóm ---
        df['interior_clean'] = df['interior'].apply(self._extract_interior_clean)
        df = df.drop(columns=['interior'], errors='ignore')

        # --- Hướng nhà: chuẩn hóa nhãn ---
        df['direction_clean'] = df['house_direction'].apply(self._clean_direction)
        df = df.drop(columns=['house_direction'], errors='ignore')

        # --- Điền khuyết: median cho bedrooms/bathrooms (HỌC 1 LẦN LÚC TRAIN, LƯU LẠI),
        #     hằng số 1 cho floors (nhà trệt/cấp 4) ---
        if is_training:
            self.fill_stats['bedrooms_median'] = float(df['bedrooms'].median())
            self.fill_stats['bathrooms_median'] = float(df['bathrooms'].median())
        df['bedrooms'] = df['bedrooms'].fillna(self.fill_stats['bedrooms_median'])
        df['bathrooms'] = df['bathrooms'].fillna(self.fill_stats['bathrooms_median'])
        df['floors'] = df['floors'].fillna(1)

        # --- Lọc vật lý số phòng/tầng (1 đến 15) ---
        df = df[(df['bedrooms'] >= 1) & (df['bedrooms'] <= 15)]
        df = df[(df['bathrooms'] >= 1) & (df['bathrooms'] <= 15)]
        df = df[(df['floors'] >= 1) & (df['floors'] <= 15)]
        df = df.reset_index(drop=True)

        # --- Lọc outlier giá/diện tích bằng ngưỡng cứng (Hard Thresholding) ---
        df['price_per_m2'] = df['price_raw'] / df['area_raw']
        df = df[(df['area_raw'] >= 10) & (df['area_raw'] <= 600)]
        df = df[(df['price_per_m2'] <= 1.0) & (df['price_raw'] <= 400.0) & (df['price_raw'] > 0)]
        df = df.drop(columns=['price_per_m2'])
        df = df.reset_index(drop=True)

        # --- Chỉ giữ tập biến số đã được vòng lặp VIF chọn lọc ở file 04:
        #     area_raw, floors, bathrooms (bedrooms và total_rooms đã bị loại
        #     do đa cộng tuyến — không tính total_rooms nữa vì không dùng) ---
        df = df.drop(columns=['bedrooms'], errors='ignore')

        # --- Encoding ---
        df['address_encoded'] = df['district_clean'].map(DISTRICT_MAPPING)
        df['interior_encoded'] = df['interior_clean'].map(INTERIOR_MAPPING)
        df['legal_encoded'] = df['legal_clean'].map(LEGAL_MAPPING)

        # One-Hot hướng nhà — ép cố định đủ 8 cột dir_* đúng thứ tự như file 04,
        # kể cả khi batch dữ liệu hiện tại thiếu một vài hướng (đảm bảo khớp
        # cột đặc trưng với scaler đã fit lúc train).
        df_dir = pd.get_dummies(df['direction_clean'], prefix='dir', dtype=int)
        df_dir = df_dir.drop(columns=['dir_Không rõ'], errors='ignore')
        for col in DIRECTION_DUMMY_COLUMNS:
            if col not in df_dir.columns:
                df_dir[col] = 0
        df_dir = df_dir[DIRECTION_DUMMY_COLUMNS]

        df = pd.concat([df, df_dir], axis=1)
        df = df.drop(columns=['district_clean', 'interior_clean', 'legal_clean', 'direction_clean'], errors='ignore')

        return df

    # =====================================================================
    # PUBLIC API
    # =====================================================================
    def fit_transform(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Chạy toàn bộ pipeline TRÊN TẬP TRAIN.
        Sẽ HỌC (median bedrooms/bathrooms, StandardScaler) và LƯU artifacts
        xuống đĩa (standard_scaler.pkl, fill_stats.json) để tái sử dụng khi
        transform() cho validation/test/serving.
        """
        df = self._stage_01_text_parsing(raw_df)
        df = self._stage_02_filter_house_segment(df)
        df = self._stage_04_advanced_preprocessing(df, is_training=True)
        df = self._stage_05_transform_and_scale(df, is_training=True)
        self._save_artifacts()
        return df

    def transform(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """
        Chạy toàn bộ pipeline cho dữ liệu MỚI (validation / test / serving).
        NẠP LẠI đúng median + scaler đã lưu ở fit_transform() — không học lại,
        tránh rò rỉ dữ liệu (data leakage) và đảm bảo nhất quán train/serving.
        """
        self._load_artifacts()
        df = self._stage_01_text_parsing(raw_df)
        df = self._stage_02_filter_house_segment(df)
        df = self._stage_04_advanced_preprocessing(df, is_training=False)
        df = self._stage_05_transform_and_scale(df, is_training=False)
        return df

    def _save_artifacts(self):
        os.makedirs(self.artifacts_dir, exist_ok=True)
        joblib.dump(self.scaler, self.scaler_path)
        with open(self.stats_path, 'w', encoding='utf-8') as f:
            json.dump(self.fill_stats, f, ensure_ascii=False, indent=2)

    def _load_artifacts(self):
        if not os.path.exists(self.scaler_path):
            raise FileNotFoundError(
                f"Không tìm thấy scaler tại {self.scaler_path}. "
                f"Hãy chạy fit_transform() trên tập train trước."
            )
        if not os.path.exists(self.stats_path):
            raise FileNotFoundError(
                f"Không tìm thấy fill_stats tại {self.stats_path}. "
                f"Hãy chạy fit_transform() trên tập train trước."
            )
        self.scaler = joblib.load(self.scaler_path)
        with open(self.stats_path, 'r', encoding='utf-8') as f:
            self.fill_stats = json.load(f)


# =========================================================================
# LUỒNG XỬ LÝ VÀ GỘP DỮ LIỆU HÀNG NGÀY CHỈ LÀM SẠCH THÔ (MLOPS APPLIED)
# =========================================================================
if __name__ == '__main__':
    import sys
    
    # Xác định các đường dẫn dựa trên cấu trúc thư mục thực tế của em
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    RAW_DATA_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "data", "raw", "new_data.csv"))
    CLEAN_DATA_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "data", "processed", "clean_data.csv"))
    
    print("\n--- BẮT ĐẦU QUY TRÌNH LÀM SẠCH VÀ GỘP DỮ LIỆU HÀNG NGÀY ---")
    
    # 1. Kiểm tra file dữ liệu thô mới cào về từ vùng đệm new_data.csv
    if not os.path.exists(RAW_DATA_PATH):
        print(f"[WARNING] Không tìm thấy file new_data.csv tại: {RAW_DATA_PATH}. Dừng xử lý.")
        sys.exit(0)
        
    try:
        new_df = pd.read_csv(RAW_DATA_PATH)
        if new_df.empty:
            print("[INFO] File new_data.csv không có dữ liệu mới. Dừng xử lý.")
            sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Lỗi không đọc được file new_data.csv: {e}")
        sys.exit(1)
        
    print(f"[INFO] Đã nạp thành công {len(new_df)} bản ghi mới cào về.")
    
    # 2. Khởi tạo Pipeline và chỉ chạy các Stage làm sạch text, xử lý thuộc tính và outlier cứng
    # (Tuyệt đối KHÔNG chạy Stage 05 chuẩn hóa/scale)
    pipeline = HousingDataPipeline(artifacts_dir=os.path.abspath(os.path.join(CURRENT_DIR, "..", "backend", "models")))
    
    print("[PROCESS] Đang chạy bóc tách văn bản (Stage 01)...")
    df_clean = pipeline._stage_01_text_parsing(new_df)
    
    print("[PROCESS] Đang lọc riêng phân khúc Nhà riêng (Stage 02)...")
    df_clean = pipeline._stage_02_filter_house_segment(df_clean)
    
    print("[PROCESS] Đang xử lý gom nhóm thuộc tính và lọc outlier cứng (Stage 04)...")
    # Sử dụng stats cũ để điền khuyết an toàn cho batch dữ liệu mới hàng ngày
    try:
        pipeline._load_artifacts()
    except Exception:
        # Dự phòng trường hợp chạy lần đầu chưa có file stats học từ notebook
        pipeline.fill_stats = {'bedrooms_median': 3.0, 'bathrooms_median': 2.0}
        
    df_clean = pipeline._stage_04_advanced_preprocessing(df_clean, is_training=False)
    
    if df_clean.empty:
        print("[INFO] Không có dữ liệu mới nào vượt qua được các bộ lọc làm sạch thô. Dừng xử lý.")
        sys.exit(0)
        
    print(f"[SUCCESS] Đã làm sạch xong dữ liệu mới. Còn lại {len(df_clean)} dòng hợp lệ.")
    
    # 3. Đọc file clean_data.csv cũ lên (nếu có) để tiến hành gộp và lọc trùng theo ID bài đăng
    print("[PROCESS] Tiến hành gộp dữ liệu và lọc trùng...")
    
    if os.path.exists(CLEAN_DATA_PATH):
        try:
            old_clean_df = pd.read_csv(CLEAN_DATA_PATH)
            print(f"[INFO] File clean_data.csv hiện tại đang có {len(old_clean_df)} dòng.")
            # Nối đuôi dữ liệu mới vào dữ liệu cũ
            combined_df = pd.concat([old_clean_df, df_clean], axis=0, ignore_index=True)
        except Exception as e:
            print(f"[ERROR] Không đọc được file clean_data.csv cũ ({e}). Tiến hành ghi mới.")
            combined_df = df_clean
    else:
        print("[INFO] File clean_data.csv chưa tồn tại. Sẽ tạo file mới.")
        combined_df = df_clean
        
    if 'df_clean' in locals() or 'df_clean' in globals():
        if not df_clean.empty:
            print("\n=== [PREVIEW] DÒNG DỮ LIỆU MỚI XUẤT SẮC VƯỢT QUA BỘ LỌC ===")
            # .to_markdown() giúp in ra dạng bảng cực kỳ đẹp và dễ nhìn trong Terminal
            print(df_clean.to_markdown(index=False))
            print("============================================================\n")
                
    # Lọc trùng lặp dựa trên cột 'id', giữ lại bản ghi xuất hiện sau cùng (keep='last')
    # để cập nhật thông tin/giá mới nhất nếu bài đăng đó bị trùng lặp.
    total_before = len(combined_df)
    duplicate_subsets = [
        'price_raw', 'area_raw', 'bathrooms', 'floors', 
        'address_encoded', 'interior_encoded', 'legal_encoded',
        'dir_Bắc', 'dir_Nam', 'dir_Tây', 'dir_Tây Bắc', 'dir_Tây Nam', 
        'dir_Đông', 'dir_Đông Bắc', 'dir_Đông Nam'
    ]

    # Kiểm tra xem các cột này có thực sự tồn tại trong combined_df trước khi lọc để tránh lỗi ngầm
    existing_subsets = [col for col in duplicate_subsets if col in combined_df.columns]

    # Tiến hành lọc trùng và giữ lại bản ghi cuối cùng (bản ghi mới nhất)
    combined_df = combined_df.drop_duplicates(subset=existing_subsets, keep='last').reset_index(drop=True)
    num_duplicates = total_before - len(combined_df)
    
    print(f"[DEDUPLICATE] Đã phát hiện và xử lý {num_duplicates} dòng bị trùng lặp ID.")
    
    # 4. Ghi đè lại toàn bộ dữ liệu sạch tổng hợp vào clean_data.csv
    try:
        os.makedirs(os.path.dirname(CLEAN_DATA_PATH), exist_ok=True)
        combined_df.to_csv(CLEAN_DATA_PATH, index=False, encoding='utf-8-sig')
        print(f"[SUCCESS] Đã cập nhật thành công file: {CLEAN_DATA_PATH}")
        print(f"[STATUS] Tổng số lượng dữ liệu sạch thô hiện tại: {len(combined_df)} dòng.")
    except Exception as e:
        print(f"[ERROR] Không thể ghi dữ liệu vào file clean_data.csv: {e}")
        sys.exit(1)
        
    print("--- QUY TRÌNH TIỀN XỬ LÝ HÀNG NGÀY HOÀN THÀNH ---\n")