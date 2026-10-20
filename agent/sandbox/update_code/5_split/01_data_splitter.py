import pandas as pd
from sklearn.model_selection import train_test_split

def split_dataset(df: pd.DataFrame, test_size: float = 0.30, val_size: float = 0.50, random_state: int = 42) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Chia tập dữ liệu theo tỷ lệ 70% Train, 15% Val, 15% Test chuẩn xác."""
    clean = df.drop(columns=["id", "url"], errors="ignore")
    train_df, temp_df = train_test_split(clean, test_size=test_size, random_state=random_state, shuffle=True)
    val_df, test_df = train_test_split(temp_df, test_size=val_size, random_state=random_state, shuffle=True)
    
    meta = {
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "test_rows": len(test_df),
        "total_rows": len(clean)
    }
    return train_df, val_df, test_df, meta

if __name__ == "__main__":
    dummy_df = pd.DataFrame({"price_raw": range(100), "area_raw": range(100)})
    tr, v, te, m = split_dataset(dummy_df)
    print("Split metadata:", m)
