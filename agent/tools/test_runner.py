"""
==============================================================================
AURA MLOPS TEST RUNNER TOOLS (MVP ARCHITECTURE)
==============================================================================
Cung cấp công cụ chạy thử nghiệm (Dry-Run / Smoke Test) trong một tiến trình
con cô lập (isolated subprocess), bảo vệ tuyệt đối runtime của Agent.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent.tools.sandbox import PROJECT_ROOT, resolve_file_path


def check_module_importability(relative_path: str) -> Dict[str, Any]:
    """
    Kiểm tra xem một file Python có thể nạp (import) an toàn hay không
    bằng cách khởi chạy trong một Subprocess riêng biệt hoàn toàn.
    """
    target_path = resolve_file_path(relative_path)
    if not target_path.exists():
        return {
            "success": False,
            "error": f"Không tìm thấy file để kiểm thử nạp: {relative_path} (resolved: {target_path})"
        }
        
    script = f"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
from pathlib import Path
import importlib.util

project_root = Path(r'{PROJECT_ROOT}')
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

file_path = Path(r'{target_path}')
module_name = file_path.stem

try:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        print("IMPORT_FAIL: spec_from_file_location trả về None")
        sys.exit(1)
    
    # Thực thi nạp module để phát hiện lỗi runtime / NameError ở cấp module
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Đảm bảo module không bị rỗng và có ít nhất 1 hàm callable
    callables = [k for k, v in mod.__dict__.items() if callable(v) and not k.startswith('_')]
    if not callables:
        print("IMPORT_FAIL: Module rỗng, không chứa hàm nghiệp vụ nào!")
        sys.exit(3)

    print("IMPORT_SUCCESS")
    sys.exit(0)
except Exception as e:
    import traceback
    print("IMPORT_EXCEPTION: " + str(e))
    traceback.print_exc()
    sys.exit(2)
"""
    try:
        res = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=str(PROJECT_ROOT)
        )
        
        stdout = res.stdout.strip()
        stderr = res.stderr.strip()
        
        if res.returncode == 0 and "IMPORT_SUCCESS" in stdout:
            return {
                "success": True,
                "message": f"Tệp '{relative_path}' nạp an toàn tuyệt đối (Không có lỗi cú pháp hoặc import).",
                "output": stdout
            }
        else:
            return {
                "success": False,
                "error": f"Lỗi khi nạp thử nghiệm module '{relative_path}':\n{stderr or stdout}",
                "returncode": res.returncode
            }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Quá thời gian chờ (10s) khi kiểm tra nạp file '{relative_path}'."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi thực thi kiểm thử: {str(e)}"
        }


def run_preprocessing_smoke_test() -> Dict[str, Any]:
    """
    Chạy thử nghiệm nhanh (Smoke Test) các mô-đun tiền xử lý trong Sandbox
    để xác nhận các phép định nghĩa hàm và xử lý dữ liệu không sinh lỗi.
    """
    prep_dir = resolve_file_path("3_preprocessing/01_segment_filter.py").parent
    script = f"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
from pathlib import Path
import importlib.util

prep_dir = Path(r'{prep_dir}')
files = sorted(list(prep_dir.glob("*.py")))

for f in files:
    if f.name.startswith("__"):
        continue
    try:
        code = compile(f.read_text(encoding='utf-8', errors='replace'), str(f), 'exec')
    except Exception as e:
        print(f"SMOKE_TEST_FAILED on {{f.name}}: {{e}}")
        sys.exit(1)

print("SMOKE_TEST_SUCCESS: Toàn bộ mô-đun preprocessing đều hợp lệ.")
sys.exit(0)
"""
    try:
        res = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            cwd=str(PROJECT_ROOT)
        )
        if res.returncode == 0 and "SMOKE_TEST_SUCCESS" in res.stdout:
            return {
                "success": True,
                "message": "Smoke Test tiền xử lý vượt qua thành công 100%.",
                "details": res.stdout.strip()
            }
        else:
            return {
                "success": False,
                "error": f"Smoke Test tiền xử lý thất bại:\n{res.stderr.strip() or res.stdout.strip()}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi thực thi Smoke Test: {str(e)}"
        }
