import pandas as pd

def impute_missing_data(df: pd.DataFrame, fill_stats: dict = None) -> tuple[pd.DataFrame, dict]:
    """Điền khuyết: Median cho số phòng ngủ/tắm, Mode (1 tầng) cho số tầng (Cell 6 Notebook 04)."""
    df_out = df.copy()

    if fill_stats is None:
        fill_stats = {
            "bedrooms_median": float(df_out["bedrooms"].median()) if "bedrooms" in df_out.columns and not df_out["bedrooms"].dropna().empty else 2.0,
            "bathrooms_median": float(df_out["bathrooms"].median()) if "bathrooms" in df_out.columns and not df_out["bathrooms"].dropna().empty else 2.0,
            "floors_mode": float(df_out["floors"].mode()[0]) if "floors" in df_out.columns and not df_out["floors"].dropna().empty else 1.0,
        }

    if "bedrooms" in df_out.columns:
        df_out["bedrooms"] = df_out["bedrooms"].fillna(fill_stats["bedrooms_median"])
    if "bathrooms" in df_out.columns:
        df_out["bathrooms"] = df_out["bathrooms"].fillna(fill_stats["bathrooms_median"])
    if "floors" in df_out.columns:
        df_out["floors"] = df_out["floors"].fillna(fill_stats["floors_mode"])

    return df_out, fill_stats

if __name__ == "__main__":
    test_df = pd.DataFrame({"bedrooms": [1, None, 3], "bathrooms": [1, 2, None], "floors": [None, 2, 2]})
    res_df, stats = impute_missing_data(test_df)
    print("Imputation stats:", stats)
