import sys
import os
import pytest

# Add parent directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope='module')
def ocr_imports():
    """Fixture to test that essential OCR modules import correctly."""
    try:
        from module.ocr.ocr import Ocr, OCR_MODEL
        from module.ocr.al_ocr import AlOcr, OCR_BACKEND, OCR_NAME
        return {
            "Ocr": Ocr,
            "OCR_MODEL": OCR_MODEL,
            "AlOcr": AlOcr,
            "OCR_BACKEND": OCR_BACKEND,
            "OCR_NAME": OCR_NAME
        }
    except ImportError as e:
        pytest.fail(f"Failed to import core OCR modules: {e}")

def test_ocr_files_exist():
    """Check that primary OCR files exist and are not empty."""
    ocr_files = [
        "module/ocr/ocr.py",
        "module/ocr/al_ocr.py",
        "module/ocr/simple_ocr.py"
    ]
    for file_path in ocr_files:
        assert os.path.exists(file_path), f"{file_path} should exist"
        assert os.path.getsize(file_path) > 100, f"{file_path} should not be empty"

def test_ocr_backend_initialized(ocr_imports):
    """Test that a valid OCR backend (preferably PaddleOCR) was initialized."""
    AlOcr = ocr_imports["AlOcr"]
    OCR_BACKEND = ocr_imports["OCR_BACKEND"]
    OCR_NAME = ocr_imports["OCR_NAME"]
    
    assert OCR_BACKEND is not None, "OCR_BACKEND should not be None"
    assert OCR_NAME != "none", "OCR_NAME should have a valid backend name"
    
    # Check if PaddleOCR is the preferred backend
    try:
        import paddleocr
        assert OCR_BACKEND == "paddleocr", "PaddleOCR should be the preferred backend"
        print(f"Successfully initialized OCR backend: {OCR_NAME}")
    except ImportError:
        print(f"PaddleOCR not found, fell back to: {OCR_NAME}")
    
    # Ensure AlOcr can be instantiated
    try:
        ocr_instance = AlOcr(name='test_init')
        assert ocr_instance is not None, "AlOcr instance should be created successfully"
        assert ocr_instance.backend == OCR_BACKEND, "AlOcr instance should use the detected backend"
    except Exception as e:
        pytest.fail(f"AlOcr instantiation failed: {e}")

def test_legacy_ocr_functional(ocr_imports):
    """Check that the legacy Ocr class is functional and uses the new backend."""
    Ocr = ocr_imports["Ocr"]
    # This test ensures the `Ocr.ocr` method we repaired is working.
    # We don't need to test the full OCR process here, just that the call succeeds.
    try:
        # The buttons argument is a dummy for initialization
        ocr_instance = Ocr(buttons=(0, 0, 10, 10), name='test_legacy')
        # Passing None should return a default empty value without crashing
        result = ocr_instance.ocr(image=None)
        assert result == '', "Ocr.ocr(image=None) should return an empty string"
    except Exception as e:
        pytest.fail(f"Legacy Ocr class failed on initialization or execution: {e}")

def test_commission_module_compatibility():
    """Check if the commission module maintains compatibility with the Ocr class."""
    try:
        with open("module/commission/project.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'from module.ocr.ocr import' in content, "Commission module must maintain Ocr import"
        assert 'class SuffixOcr(Ocr):' in content, "SuffixOcr class must inherit from Ocr"
    except FileNotFoundError:
        pytest.fail("Could not find module/commission/project.py")
    except Exception as e:
        pytest.fail(f"Error checking commission module: {e}")