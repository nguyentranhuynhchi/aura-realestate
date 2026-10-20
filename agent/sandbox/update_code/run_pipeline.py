try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import os
import sys
import json
import importlib.util
from datetime import datetime
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..","..", ".."))
RAW_DATA_PATH = os.path.join(ROOT_DIR, "data", "raw", "new_data.csv")
CLEAN_DATA_PATH = os.path.join(ROOT_DIR, "data", "processed", "clean_data.csv")
DATA_PROCESSED_DIR = os.path.join(ROOT_DIR, "data", "processed")
BACKEND_MODELS_DIR = os.path.join(ROOT_DIR, "backend", "models")
REGISTRY_DIR = os.path.join(ROOT_DIR, "model_registry")

def dynamic_import(rel_path, module_name):
    full_path = os.path.join(BASE_DIR, rel_path)
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def run_mlops_pipeline(timestamp: str = None) -> dict:
    timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_dir = os.path.join(REGISTRY_DIR, timestamp)
    os.makedirs(exp_dir, exist_ok=True)
    summary = {"timestamp": timestamp, "steps": {}}

    print(f"=== [START] RUNNING MODULAR MLOPS PIPELINE: {timestamp} ===")

    # --- 1. CRAWLER / DATA INGESTION ---
    if os.path.exists(RAW_DATA_PATH):
        raw_df = pd.read_csv(RAW_DATA_PATH)
        summary["steps"]["1_crawler"] = {"status": "success", "raw_records": len(raw_df)}
    else:
        summary["steps"]["1_crawler"] = {"status": "skipped_or_missing", "raw_records": 0}
        return summary

        # --- 2. EDA AUDITING ---
    eda_missing = dynamic_import("2_eda/01_missing_audit.py", "eda_missing")
    eda_skew = dynamic_import("2_eda/03_distribution_skew.py", "eda_skew")
    summary["steps"]["2_eda"] = {
        "missing_audit": eda_missing.audit_missing_values(raw_df),      # ◄ SỬA TÊN HÀM
        "skew_analysis": eda_skew.analyze_skewness(raw_df)             # ◄ SỬA TÊN HÀM
    }

    # --- 3. PREPROCESSING PIPELINE ---
    p1 = dynamic_import("3_preprocessing/01_segment_filter.py", "p1")
    p2 = dynamic_import("3_preprocessing/02_numeric_parser.py", "p2")
    p3 = dynamic_import("3_preprocessing/03_physical_bounds.py", "p3")
    p4 = dynamic_import("3_preprocessing/04_district_encoder.py", "p4")
    p5 = dynamic_import("3_preprocessing/05_category_encoder.py", "p5")
    p6 = dynamic_import("3_preprocessing/06_missing_imputer.py", "p6")
    p7 = dynamic_import("3_preprocessing/07_deduplicator.py", "p7")

    df_step, m1 = p1.filter_property_segments(raw_df)      # ◄ SỬA TÊN HÀM
    df_step, m2 = p2.parse_numeric_columns(df_step)         # ◄ SỬA TÊN HÀM
    df_step, m3 = p3.filter_physical_bounds(df_step)        # (Khớp chuẩn)
    df_step, m4 = p4.encode_districts(df_step)              # (Khớp chuẩn)
    df_step, m5 = p5.encode_categorical_features(df_step)   # (Khớp chuẩn)
    df_step, m6 = p6.impute_missing_data(df_step)           # ◄ SỬA TÊN HÀM
    clean_df, m7 = p7.deduplicate_and_merge(df_step, CLEAN_DATA_PATH) # (Khớp chuẩn)

    summary["steps"]["3_preprocessing"] = {
        "segment_filter": m1, "numeric_parser": m2, "physical_bounds": m3,
        "district_encoder": m4, "category_encoder": m5, "missing_imputer": m6, "deduplicator": m7
    }

    # --- 4. RAG CHUNKING & SYNC ---
    rag1 = dynamic_import("4_rag/01_chunk_builder.py", "rag1")
    rag2 = dynamic_import("4_rag/02_chroma_syncer.py", "rag2")
    chunks, m_chunks = rag1.build_property_chunks(raw_df if not raw_df.empty else clean_df)
    m_sync = rag2.sync_to_chroma(chunks)
    summary["steps"]["4_rag"] = {"chunk_builder": m_chunks, "chroma_syncer": m_sync}

    # --- 5. SPLIT & FEATURE SCALING ---
    s1 = dynamic_import("5_split/01_data_splitter.py", "s1")
    s2 = dynamic_import("5_split/02_log_transform.py", "s2")
    s3 = dynamic_import("5_split/03_feature_scaler.py", "s3")

    tr, val, te, m_split = s1.split_dataset(clean_df)
    tr, val, te, m_log = s2.apply_log_transform(tr, val, te)
    scaler_save_path = os.path.join(exp_dir, "scaler.pkl")
    tr, val, te, m_scale = s3.scale_features(tr, val, te, save_path=scaler_save_path)

    # Lưu train/val/test ra data/processed/
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    tr.to_csv(os.path.join(DATA_PROCESSED_DIR, "train.csv"), index=False)
    val.to_csv(os.path.join(DATA_PROCESSED_DIR, "val.csv"), index=False)
    te.to_csv(os.path.join(DATA_PROCESSED_DIR, "test.csv"), index=False)

    summary["steps"]["5_split"] = {"splitter": m_split, "log_transform": m_log, "scaler": m_scale}

    # --- 6. MODELING & EVALUATION ---
    m_ridge = dynamic_import("6_modeling/01_tune_ridge.py", "m_ridge")
    m_tree = dynamic_import("6_modeling/02_tune_tree.py", "m_tree")
    m_rf = dynamic_import("6_modeling/03_tune_rf.py", "m_rf")
    m_stack = dynamic_import("6_modeling/04_train_stacking.py", "m_stack")
    m_eval = dynamic_import("6_modeling/05_evaluate_champion.py", "m_eval")

    X_tr = tr.drop(columns=["price_log"]).values
    y_tr = tr["price_log"].values
    X_v = val.drop(columns=["price_log"]).values
    y_v = val["price_log"].values
    X_te = te.drop(columns=["price_log"]).values
    y_te = te["price_log"].values

    ridge_model, meta_ridge = m_ridge.tune_ridge(X_tr, y_tr, X_v, y_v)
    tree_model, meta_tree = m_tree.tune_decision_tree(X_tr, y_tr, X_v, y_v)
    rf_model, meta_rf = m_rf.tune_random_forest(X_tr, y_tr, X_v, y_v)

    base_models = {"ridge": ridge_model, "tree": tree_model, "rf": rf_model}
    stacking_model, meta_stack = m_stack.train_stacking_ensemble(X_tr, y_tr, X_v, y_v, base_models=base_models)

    eval_result = m_eval.evaluate_and_promote(stacking_model, X_te, y_te, exp_dir, REGISTRY_DIR, BACKEND_MODELS_DIR)

    summary["steps"]["6_modeling"] = {
        "ridge": meta_ridge, "tree": meta_tree, "rf": meta_rf, "stacking": meta_stack, "final_evaluation": eval_result
    }

    # Ghi file summary ra registry và output
    summary_path = os.path.join(exp_dir, "pipeline_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"=== [COMPLETE] Pipeline Summary saved to {summary_path} ===")
    return summary

if __name__ == "__main__":
    ts = sys.argv[1] if len(sys.argv) > 1 else None
    res = run_mlops_pipeline(timestamp=ts)
    if "6_modeling" in res.get("steps", {}):
        print(json.dumps(res["steps"]["6_modeling"]["final_evaluation"], indent=2))
    else:
        print(json.dumps(res, indent=2))