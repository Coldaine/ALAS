import sys
import os
import time
import pytest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_config_structure():
    """Test configuration files are intact and accessible."""
    config_files = [
        "config/template.json",
        "pyproject.toml"
    ]
    
    for config_file in config_files:
        assert os.path.exists(config_file), f"{config_file} not found"
        assert os.path.getsize(config_file) > 0, f"{config_file} should not be empty"

def test_import_performance():
    """Test that key modules import without excessive delay."""
    modules_to_time = [
        ("module.exception", "Exception module"),
        ("module.logger", "Logger module"),
        ("module.base.decorator", "Decorator module"),
    ]
    
    total_time = 0
    max_import_time = 1.0  # seconds
    
    for module_name, description in modules_to_time:
        try:
            start = time.time()
            __import__(module_name)
            elapsed = time.time() - start
            total_time += elapsed
            assert elapsed < max_import_time, f"{description} import was too slow: {elapsed:.3f}s"
        except ImportError:
            # This is expected for modules with heavy dependencies not installed in test env
            print(f"[INFO] Skipping performance check for {description} due to missing dependencies.")
        except Exception as e:
            pytest.fail(f"Failed to import {description}: {e}")
    
    print(f"[INFO] Total import time for checked modules: {total_time:.3f}s")

def test_core_module_structure():
    """Test that core module directories exist."""
    core_dirs = [
        "module/base",
        "module/config", 
        "module/ocr",
        "module/campaign",
        "module/device",
        "module/combat"
    ]
    
    for dir_path in core_dirs:
        assert os.path.isdir(dir_path), f"{dir_path} directory not found"
        # Check for at least one Python file, indicating it's a module
        py_files = list(Path(dir_path).glob("*.py"))
        assert len(py_files) > 0, f"{dir_path} should contain Python module files"

def test_no_syntax_errors_in_edited_files():
    """Verify that recently edited files have valid Python syntax."""
    # Focus on files changed during recent OCR work
    edited_files = [
        "module/ocr/ocr.py",
        "module/ocr/al_ocr.py",
        "pyproject.toml" # Not python, but check existence
    ]
    
    for file_path in edited_files:
        assert os.path.exists(file_path), f"{file_path} not found"
        if not file_path.endswith('.py'):
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            compile(content, file_path, 'exec')
        except SyntaxError as e:
            pytest.fail(f"{file_path} has a syntax error: {e}")
        except Exception as e:
            pytest.fail(f"Failed to check syntax of {file_path}: {e}")

def test_poetry_config():
    """Test that pyproject.toml is valid and contains key sections."""
    pyproject_path = "pyproject.toml"
    assert os.path.exists(pyproject_path), "pyproject.toml not found"
    
    try:
        # Use tomllib for Python 3.11+
        import tomllib
    except ImportError:
        # Fallback to tomli for older Python versions
        import tomli as tomllib
            
    with open(pyproject_path, 'rb') as f:
        data = tomllib.load(f)
        
    # Check for essential tool configurations
    assert 'tool' in data, "pyproject.toml missing [tool] section"
    tool_data = data['tool']
    
    assert 'poetry' in tool_data, "pyproject.toml missing [tool.poetry]"
    assert 'dependencies' in tool_data['poetry'], "[tool.poetry] missing dependencies"
    assert 'python' in tool_data['poetry'], "[tool.poetry] missing python version specification"
    
    # Check for code quality tools
    assert 'black' in tool_data, "pyproject.toml missing [tool.black] configuration"
    assert 'ruff' in tool_data, "pyproject.toml missing [tool.ruff] configuration"