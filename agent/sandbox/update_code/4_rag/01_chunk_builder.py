import pandas as pd

def build_property_chunks(df: pd.DataFrame) -> tuple[list[dict], dict]:
    """Tạo văn bản tóm tắt ngữ nghĩa phong phú cho từng bất động sản phục vụ RAG."""
    chunks = []
    for _, row in df.iterrows():
        prop_id = str(row.get("id", abs(hash(str(row.values)))))
        price = row.get("price_raw", "N/A")
        area = row.get("area_raw", "N/A")
        addr = row.get("address_raw", "Không rõ địa chỉ")
        beds = row.get("bedrooms", "N/A")
        baths = row.get("bathrooms", "N/A")
        legal = row.get("legal_status", "Không rõ")
        interior = row.get("interior", "Không rõ")

        text = (
            f"Bất động sản tại {addr}. "
            f"Diện tích: {area} m2, Giá bán: {price} tỷ. "
            f"Thiết kế: {beds} phòng ngủ, {baths} phòng tắm. "
            f"Pháp lý: {legal}, Nội thất: {interior}."
        )

        chunks.append({
            "id": prop_id,
            "text": text,
            "metadata": {"price": float(price) if isinstance(price, (int, float)) else 0.0, "address": str(addr)}
        })

    return chunks, {"total_chunks_created": len(chunks)}

if __name__ == "__main__":
    test_df = pd.DataFrame([{"id": "1", "price_raw": 3.2, "area_raw": 65, "address_raw": "Quận 7"}])
    c, m = build_property_chunks(test_df)
    print(m, c[0]["text"])
