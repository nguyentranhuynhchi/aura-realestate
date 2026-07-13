# pipelines/utils.py

# Bộ ánh xạ dùng chung cho cả Train và Predict
DISTRICT_MAPPING = {
    'Huyện Cần Giờ': 0, 'Huyện Củ Chi': 1, 'Huyện Hóc Môn': 2, 'Huyện Nhà Bè': 3, 'Huyện Bình Chánh': 4,
    'Quận 6': 5, 'Quận 4': 6, 'Quận 11': 7, 'Quận 5': 8, 'Quận 9': 10, 'Quận 3': 11,
    'Quận 10': 12, 'Quận 2': 13, 'Quận Tân Phú': 14, 'Quận Tân Bình': 15, 'Quận Phú Nhuận': 16,
    'Quận Gò Vấp': 17, 'Quận Bình Thạnh': 18, 'Quận 12': 19, 'Quận 7': 20, 'TP. Thủ Đức': 21, 'Quận 1': 22
}

INTERIOR_MAPPING = {
    'Khác / Thỏa thuận': 0, 'Nội thất cơ bản': 1, 'Không nội thất': 2, 
    'Không rõ (NaN)': 3, 'Đầy đủ nội thất': 4, 'Bàn giao thô': 5
}

LEGAL_MAPPING = {
    'Không rõ': 0, 'Chưa Sổ / HDMB': 1, 'Có Sổ': 2
}

def get_encoded_value(mapping, key, default=0):
    """Hàm tiện ích để lấy giá trị mapping an toàn"""
    return mapping.get(key, default)