"""
==============================================================================
AURA MLOPS SANDBOX & SYNTAX GUARD TOOLS (MVP ARCHITECTURE)
==============================================================================
Cung cấp các công cụ thao tác tệp an toàn trong kiến trúc Dual-Sandbox:
- baseline/: Kho mã nguồn chuẩn mốc (Golden Baseline, không bao giờ sửa trực tiếp).
- update_code/: Nơi Coder Agent đề xuất, thử nghiệm và ghi bản vá an toàn.
Bảo vệ bằng rào chắn AST (Abstract Syntax Tree) và sinh bản so sánh Git Unified Diff.
"""

import os
import sys
import ast
import difflib
from pathlib import Path
from typing import Tuple, Dict, Any, List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thư mục gốc của toàn bộ dự án Aura Real Estate
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SANDBOX_DIR = PROJECT_ROOT / "agent" / "sandbox"
BASELINE_DIR = SANDBOX_DIR / "baseline"
UPDATE_CODE_DIR = SANDBOX_DIR / "update_code"

# Danh mục chính xác 24 micro-modules cốt lõi của dự án Aura Real Estate
CATALOG_MODULES = [
    "1_crawler/01_session_cookie.py",
    "1_crawler/02_api_spider.py",
    "1_crawler/03_raw_extractor.py",
    "2_eda/01_missing_audit.py",
    "2_eda/02_collinearity_check.py",
    "2_eda/03_distribution_skew.py",
    "2_eda/04_iqr_outlier_audit.py",
    "3_preprocessing/01_segment_filter.py",
    "3_preprocessing/02_numeric_parser.py",
    "3_preprocessing/03_physical_bounds.py",
    "3_preprocessing/04_district_encoder.py",
    "3_preprocessing/05_category_encoder.py",
    "3_preprocessing/06_missing_imputer.py",
    "3_preprocessing/07_deduplicator.py",
    "4_rag/01_chunk_builder.py",
    "4_rag/02_chroma_syncer.py",
    "5_split/01_data_splitter.py",
    "5_split/02_log_transform.py",
    "5_split/03_feature_scaler.py",
    "6_modeling/01_tune_ridge.py",
    "6_modeling/02_tune_tree.py",
    "6_modeling/03_tune_rf.py",
    "6_modeling/04_train_stacking.py",
    "6_modeling/05_evaluate_champion.py"
]


def resolve_file_path(relative_path: str, prefer_update: bool = True) -> Path:
    """
    Chuẩn hóa đường dẫn tương đối thành đường dẫn tuyệt đối an toàn trong Dual Sandbox.
    Nếu prefer_update=True: ưu tiên tìm trong update_code, sau đó tới baseline, rồi tới project root.
    """
    norm = relative_path.replace("\\", "/").lstrip("/")
    
    # Loại bỏ tiền tố 'pipelines/' nếu người dùng truyền vào
    stripped = norm
    if stripped.startswith("pipelines/"):
        stripped = stripped[len("pipelines/"):]
    elif stripped.startswith("agent/sandbox/baseline/"):
        stripped = stripped[len("agent/sandbox/baseline/"):]
    elif stripped.startswith("agent/sandbox/update_code/"):
        stripped = stripped[len("agent/sandbox/update_code/"):]

    # Thứ tự tìm kiếm
    candidates = []
    if prefer_update:
        candidates.append(UPDATE_CODE_DIR / stripped)
        candidates.append(BASELINE_DIR / stripped)
    else:
        candidates.append(BASELINE_DIR / stripped)
        candidates.append(UPDATE_CODE_DIR / stripped)
        
    candidates.append(SANDBOX_DIR / stripped)
    candidates.append(PROJECT_ROOT / norm)
    candidates.append(PROJECT_ROOT / stripped)

    for p in candidates:
        if p.exists():
            return p

    # Mặc định trả về đường dẫn trong update_code
    return UPDATE_CODE_DIR / stripped


def validate_python_syntax(code: str, filename: str = "snippet.py") -> Tuple[bool, str, int, int]:
    """
    Rào chắn cú pháp AST (Abstract Syntax Tree Guardrail).
    Phân tích cây cú pháp của mã Python trước khi cho phép ghi vào đĩa.
    
    Returns:
        (is_valid, message, line_number, column_offset)
    """
    try:
        ast.parse(code, filename=filename)
        return True, f"Cú pháp tệp '{filename}' hoàn toàn hợp lệ (AST Clean).", 0, 0
    except SyntaxError as e:
        err_msg = (
            f"[LỖI CÚ PHÁP AST] Tại dòng {e.lineno}, cột {e.offset}: {e.msg}\n"
            f"-> Đoạn mã lỗi: {e.text.strip() if e.text else 'N/A'}"
        )
        return False, err_msg, e.lineno or 0, e.offset or 0
    except Exception as e:
        return False, f"[LỖI PARSE AST] Không thể phân tích mã: {str(e)}", 0, 0


def read_sandbox_file(relative_path: str, prefer_update: bool = True) -> Dict[str, Any]:
    """Đọc nội dung tệp mã nguồn từ Sandbox (update_code hoặc baseline)."""
    full_path = resolve_file_path(relative_path, prefer_update=prefer_update)
    if not full_path.exists():
        return {
            "success": False,
            "error": f"Không tìm thấy tệp tại đường dẫn: {relative_path} (resolved: {full_path})",
            "content": ""
        }
    
    try:
        content = full_path.read_text(encoding="utf-8", errors="replace")
        return {
            "success": True,
            "path": str(full_path),
            "relative_path": relative_path,
            "content": content,
            "line_count": len(content.splitlines())
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi đọc tệp '{relative_path}': {str(e)}",
            "content": ""
        }


def write_sandbox_file(relative_path: str, code: str) -> Dict[str, Any]:
    """
    Ghi mã nguồn vào Sandbox (luôn ghi vào update_code, không bao giờ ghi đè baseline).
    Bắt buộc phải vượt qua rào chắn AST Syntax Checker.
    """
    is_valid, msg, line, col = validate_python_syntax(code, filename=relative_path)
    if not is_valid:
        return {
            "success": False,
            "error": f"Từ chối ghi tệp do lỗi cú pháp AST:\n{msg}",
            "line": line,
            "col": col
        }
    
    norm = relative_path.replace("\\", "/").lstrip("/")
    stripped = norm
    if stripped.startswith("pipelines/"):
        stripped = stripped[len("pipelines/"):]
    elif stripped.startswith("agent/sandbox/update_code/"):
        stripped = stripped[len("agent/sandbox/update_code/"):]
    elif stripped.startswith("agent/sandbox/baseline/"):
        stripped = stripped[len("agent/sandbox/baseline/"):]

    sandbox_target = UPDATE_CODE_DIR / stripped
    sandbox_target.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        sandbox_target.write_text(code, encoding="utf-8")
        return {
            "success": True,
            "path": str(sandbox_target),
            "message": f"Đã ghi an toàn vào Sandbox update_code: {stripped} ({len(code.splitlines())} dòng)"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi hệ thống khi ghi file '{relative_path}': {str(e)}"
        }


def generate_code_diff(old_code: str, new_code: str, filename: str = "patch.py") -> str:
    """Sinh chuỗi so sánh Git Unified Diff chuẩn để Human Gate kiểm duyệt."""
    old_lines = old_code.splitlines(keepends=True)
    new_lines = new_code.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{filename} (baseline)",
        tofile=f"b/{filename} (proposed)",
        lineterm=""
    )
    return "".join(diff)


def list_catalog_modules() -> List[str]:
    """Trả về danh mục chính xác 24 micro-modules cốt lõi của toàn bộ dự án."""
    return CATALOG_MODULES.copy()
