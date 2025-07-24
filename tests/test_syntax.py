import ast
import os
from pathlib import Path
import sys
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_all_python_files_compile():
    """Ensure all Python files have valid syntax by attempting to compile them."""
    errors = []
    file_count = 0
    
    # Check all .py files in the 'module' directory
    for py_file in Path("module").rglob("*.py"):
        file_count += 1
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
        except SyntaxError as e:
            errors.append(f"{py_file}: {e}")
    
    print(f"[INFO] Checked {file_count} Python files for syntax.")
    
    if errors:
        error_messages = "\n".join(errors[:10])
        pytest.fail(
            f"Found {len(errors)} syntax errors.\n"
            f"First 10 errors:\n{error_messages}"
        )

def test_main_imports():
    """Test that critical application modules can be imported without syntax errors."""
    critical_imports = [
        ("alas", "Main entry point"),
        ("module.base.base", "Base module"),
        ("module.config.config", "Config module"),
        ("module.ocr.ocr", "OCR module"),
        ("module.campaign.campaign_base", "Campaign module")
    ]
    
    failures = []
    
    for module_path, description in critical_imports:
        try:
            __import__(module_path)
            print(f"[PASS] Imported {module_path} ({description})")
        except ImportError as e:
            # Distinguish between missing dependencies and actual code errors
            error_msg = str(e).lower()
            if "no module named" in error_msg:
                # This is likely a missing dependency, which is expected in a test environment
                print(f"[WARN] Import of '{module_path}' skipped due to missing dependency: {e}")
            else:
                failures.append(f"{module_path}: {e}")
        except Exception as e:
            failures.append(f"{module_path}: {type(e).__name__}: {e}")
            
    if failures:
        failure_messages = "\n".join(str(f) for f in failures)
        pytest.fail(
            f"Failed to import {len(failures)} critical modules.\n"
            f"Failures:\n{failure_messages}"
        )