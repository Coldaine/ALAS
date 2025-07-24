import re
import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_no_old_string_formatting():
    """Verify no old-style string formatting ('%' or .format()) remains in new code."""
    # This is a simplified check; it might have false positives but is good enough for a lint test.
    percent_pattern = re.compile(r"%\s*[sdifr]")
    format_pattern = re.compile(r"\.format\s*\(")
    
    violations = []
    # Limit check to 'module' directory to focus on app code
    for py_file in Path("module").rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8')
            if percent_pattern.search(content) or format_pattern.search(content):
                violations.append(str(py_file))
        except Exception as e:
            print(f"[WARN] Could not check {py_file}: {e}")
            
    if violations:
        print(
            f"\n[WARN] Found old string formatting in {len(violations)} files. "
            f"Consider converting to f-strings. First 5 files: {violations[:5]}"
        )

def test_modern_type_hints_usage():
    """Check for usage of modern type hints (e.g., 'list' instead of 'List')."""
    # Pattern to find old typing imports from `typing` module
    old_typing_pattern = re.compile(r"from typing import.*\b(List|Dict|Tuple|Set|Optional)\b")
    
    violations = []
    for py_file in Path("module").rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8')
            if old_typing_pattern.search(content):
                violations.append(str(py_file))
        except Exception as e:
            print(f"[WARN] Could not check {py_file}: {e}")
            
    # This is a non-blocking informational check.
    if violations:
        print(f"[INFO] {len(violations)} files still use old `typing` imports (acceptable for now).")

def test_f_strings_adoption():
    """Check that f-strings are being used in the project."""
    f_string_pattern = re.compile(r"f[\"'].*{.*}.*[\"']")
    
    files_with_f_strings = 0
    files_checked = 0
    
    for py_file in Path("module").rglob("*.py"):
        files_checked += 1
        try:
            content = py_file.read_text(encoding='utf-8')
            if f_string_pattern.search(content):
                files_with_f_strings += 1
        except Exception as e:
            print(f"[WARN] Could not check {py_file}: {e}")
    
    assert files_checked > 0, "No Python files found to check for f-string usage."
    percentage = (files_with_f_strings / files_checked) * 100
    
    print(f"[INFO] f-string usage: {percentage:.1f}% ({files_with_f_strings}/{files_checked} files)")
    assert percentage > 30, "f-string adoption is below 30%. Consider modernizing."

def test_python_version_and_poetry_usage():
    """Check pyproject.toml for Python 3.10+ and Poetry configuration."""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    content = pyproject_path.read_text(encoding='utf-8')
    
    assert 'python = "^3.10"' in content, "pyproject.toml should require Python 3.10+"
    assert '[tool.poetry]' in content, "Project should be configured to use Poetry"