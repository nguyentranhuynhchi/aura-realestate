"""
==============================================================================
AURA MLOPS MODEL DEPLOYMENT TOOL (HUMAN-IN-THE-LOOP GOVERNANCE)
==============================================================================
Công cụ cho phép Developer chính thức phê duyệt và thăng cấp (Promote)
mô hình ứng viên từ Model Registry lên Production Backend.

Tuân thủ nghiêm ngặt nguyên tắc Quản trị MLOps:
1. KHÔNG tự động đè mô hình lên môi trường Production.
2. Tự động sao lưu (Backup) mô hình hiện tại trước khi triển khai (Hỗ trợ Rollback).
3. Ghi vết kiểm toán (Audit Trail) rõ ràng trong Model Registry.
==============================================================================
"""

import os
import sys
import json
import shutil
import argparse
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_DIR = PROJECT_ROOT / "model_registry"
BACKEND_MODELS_DIR = PROJECT_ROOT / "backend" / "models"


def list_candidate_models():
    """Liệt kê danh sách tất cả các mô hình ứng viên trong Model Registry."""
    if not REGISTRY_DIR.exists():
        print(" [THÔNG BÁO]: Thư mục Model Registry chưa tồn tại.")
        return []

    candidates = []
    for exp_dir in sorted(REGISTRY_DIR.iterdir(), reverse=True):
        if not exp_dir.is_dir():
            continue
        m_file = exp_dir / "metrics.json"
        if m_file.exists():
            try:
                with open(m_file, "r", encoding="utf-8") as f:
                    metrics = json.load(f)
                    candidates.append({
                        "version": exp_dir.name,
                        "path": str(exp_dir),
                        "r2": metrics.get("R2_score", "N/A"),
                        "mae": metrics.get("MAE", "N/A"),
                        "rmse": metrics.get("RMSE", "N/A"),
                        "status": metrics.get("status", "N/A"),
                        "deployment_status": metrics.get("deployment_status", "N/A"),
                        "model_exists": (exp_dir / "model.pkl").exists()
                    })
            except Exception:
                pass
    return candidates


def print_candidates_table(candidates):
    """In bảng danh sách mô hình ứng viên."""
    print("\n" + "=" * 95)
    print(f" {'PHIÊN BẢN (TIMESTAMP)':<22} | {'R2 SCORE':<10} | {'MAE':<10} | {'STATUS':<20} | {'DEPLOYMENT STATUS'}")
    print("=" * 95)
    for c in candidates:
        print(f" {c['version']:<22} | {str(c['r2']):<10} | {str(c['mae']):<10} | {c['status']:<20} | {c['deployment_status']}")
    print("=" * 95)


def deploy_model(version: str = "latest", auto_confirm: bool = False):
    """Triển khai phiên bản mô hình được chỉ định lên Production Backend."""
    candidates = list_candidate_models()
    if not candidates:
        print(" [LỖI]: Không tìm thấy mô hình nào trong Model Registry.")
        return False

    target = None
    if version.lower() == "latest":
        target = candidates[0]
    else:
        for c in candidates:
            if c["version"] == version:
                target = c
                break

    if not target:
        print(f" [LỖI]: Không tìm thấy phiên bản '{version}' trong Model Registry.")
        return False

    exp_dir = Path(target["path"])
    model_src = exp_dir / "model.pkl"
    scaler_src = exp_dir / "scaler.pkl"

    if not model_src.exists():
        print(f" [LỖI]: File 'model.pkl' không tồn tại tại {model_src}")
        return False

    print("\n" + "=" * 70)
    print(" [XÁC NHẬN DEPLOY MÔ HÌNH LÊN PRODUCTION BACKEND]")
    print("=" * 70)
    print(f" - Phiên bản lựa chọn: {target['version']}")
    print(f" - Điểm số R2 Test:    {target['r2']}")
    print(f" - Điểm số MAE:        {target['mae']}")
    print(f" - Trạng thái hiện tại:{target['status']} ({target['deployment_status']})")
    print(f" - Đích đến:           {BACKEND_MODELS_DIR}")
    print("=" * 70)

    if not auto_confirm:
        confirm = input("\n>> Bạn có chắc chắn muốn DEPLOY mô hình này lên Production Backend? (y/N): ").strip().lower()
        if confirm not in ["y", "yes"]:
            print(" [HỦY BỎ]: Developer đã hủy thao tác triển khai.")
            return False

    BACKEND_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. SAO LƯU MÔ HÌNH CŨ (AN TOÀN ROLLBACK)
    current_model = BACKEND_MODELS_DIR / "best_stacking_regressor.pkl"
    current_scaler = BACKEND_MODELS_DIR / "standard_scaler.pkl"
    if current_model.exists():
        backup_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = BACKEND_MODELS_DIR / f"backup_{backup_ts}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(current_model, backup_dir / "best_stacking_regressor.pkl")
        if current_scaler.exists():
            shutil.copy2(current_scaler, backup_dir / "standard_scaler.pkl")
        print(f" [SAO LƯU]: Đã sao lưu mô hình cũ sang: {backup_dir}")

    # 2. CẬP NHẬT MÔ HÌNH MỚI
    shutil.copy2(model_src, current_model)
    print(f" [DEPLOY]: Đã cập nhật '{current_model.name}' thành công!")

    if scaler_src.exists():
        shutil.copy2(scaler_src, current_scaler)
        print(f" [DEPLOY]: Đã cập nhật '{current_scaler.name}' thành công!")

    # 3. GHI NHẬN VẾT KIỂM TOÁN (AUDIT TRAIL)
    m_file = exp_dir / "metrics.json"
    if m_file.exists():
        try:
            with open(m_file, "r", encoding="utf-8") as f:
                metrics = json.load(f)
            metrics["deployment_status"] = "DEPLOYED_TO_PRODUCTION"
            metrics["deployed_at"] = datetime.now().isoformat()
            metrics["deployed_by"] = "developer"
            with open(m_file, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=4)
        except Exception as e:
            print(f" [CẢNH BÁO]: Không thể cập nhật metrics.json ({e})")

    print("\n" + "=" * 70)
    print(f" [HOÀN TẤT]: Mô hình phiên bản '{target['version']}' (R2={target['r2']}) đã chính thức ACTIVE trên Backend!")
    print("=" * 70 + "\n")
    return True


def rollback_previous_backup():
    """Phục hồi (Rollback) mô hình từ bản sao lưu gần nhất."""
    if not BACKEND_MODELS_DIR.exists():
        print(" [LỖI]: Thư mục backend/models/ chưa tồn tại.")
        return False

    backup_dirs = sorted([d for d in BACKEND_MODELS_DIR.iterdir() if d.is_dir() and d.name.startswith("backup_")], reverse=True)
    if not backup_dirs:
        print(" [LỖI]: Không tìm thấy bản backup nào trong backend/models/ để phục hồi.")
        return False

    latest_backup = backup_dirs[0]
    print(f" [ROLLBACK]: Đang phục hồi từ bản sao lưu: {latest_backup.name}...")

    b_model = latest_backup / "best_stacking_regressor.pkl"
    b_scaler = latest_backup / "standard_scaler.pkl"

    if b_model.exists():
        shutil.copy2(b_model, BACKEND_MODELS_DIR / "best_stacking_regressor.pkl")
    if b_scaler.exists():
        shutil.copy2(b_scaler, BACKEND_MODELS_DIR / "standard_scaler.pkl")

    print(f" [ROLLBACK THÀNH CÔNG]: Đã khôi phục mô hình từ '{latest_backup.name}' lên Production Backend.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aura MLOps Model Deployment & Approval Tool")
    parser.add_argument("--list", action="store_true", help="Liệt kê tất cả các mô hình ứng viên trong Registry")
    parser.add_argument("--version", type=str, default=None, help="Phiên bản mô hình cần deploy (timestamp hoặc 'latest')")
    parser.add_argument("--latest", action="store_true", help="Deploy phiên bản mới nhất")
    parser.add_argument("--rollback", action="store_true", help="Phục hồi lại bản backup gần nhất của Production")
    parser.add_argument("-y", "--yes", action="store_true", help="Tự động đồng ý xác nhận không cần hỏi lại")

    args = parser.parse_args()

    if args.list:
        candidates = list_candidate_models()
        print_candidates_table(candidates)
    elif args.rollback:
        rollback_previous_backup()
    elif args.latest or args.version:
        v = "latest" if args.latest else args.version
        deploy_model(version=v, auto_confirm=args.yes)
    else:
        candidates = list_candidate_models()
        print_candidates_table(candidates)
        print("\nHướng dẫn sử dụng:")
        print("  - Xem danh sách:      python -m agent.tools.deploy_model --list")
        print("  - Deploy bản mới nhất: python -m agent.tools.deploy_model --latest")
        print("  - Deploy phiên bản:   python -m agent.tools.deploy_model --version <timestamp>")
        print("  - Phục hồi (Rollback): python -m agent.tools.deploy_model --rollback")
