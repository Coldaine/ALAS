#!/usr/bin/env python3
"""
Test runner script for ALAS OCR system.
Provides convenient test execution with different options.
"""
import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add ALAS root to path
ALAS_ROOT = Path(__file__).parent
sys.path.insert(0, str(ALAS_ROOT))


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n=== {description} ===")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=ALAS_ROOT, capture_output=True, text=True)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"FAIL: Command failed with return code {result.returncode}")
            return False
        else:
            print("PASS: Command completed successfully")
            return True
            
    except FileNotFoundError:
        print(f"FAIL: Command not found: {cmd[0]}")
        return False
    except Exception as e:
        print(f"FAIL: Error running command: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are available."""
    print("=== Checking Dependencies ===")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 10):
        print(f"FAIL: Python 3.10+ required, found {python_version.major}.{python_version.minor}")
        return False
    else:
        print(f"PASS: Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check pytest
    try:
        import pytest
        print(f"PASS: pytest {pytest.__version__}")
    except ImportError:
        print("FAIL: pytest not installed. Run: pip install pytest")
        return False
    
    # Check core ALAS modules
    try:
        from module.ocr.ocr import OCR_MODEL
        print(f"PASS: OCR system: {type(OCR_MODEL).__name__}")
    except ImportError as e:
        print(f"FAIL: Cannot import OCR system: {e}")
        return False
    
    try:
        from module.ocr.al_ocr import AlOcr
        print("PASS: AlOcr import successful")
    except ImportError as e:
        print(f"FAIL: Cannot import AlOcr: {e}")
        return False
    
    return True


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description='ALAS OCR System Test Runner')
    parser.add_argument('--quick', action='store_true', 
                       help='Run only quick unit tests')
    parser.add_argument('--integration', action='store_true',
                       help='Run integration tests')
    parser.add_argument('--performance', action='store_true',
                       help='Run performance tests')
    parser.add_argument('--all', action='store_true',
                       help='Run all tests')
    parser.add_argument('--check-deps', action='store_true',
                       help='Only check dependencies')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--file', '-f', type=str,
                       help='Run specific test file')
    
    args = parser.parse_args()
    
    # Check dependencies first
    if not check_dependencies():
        print("\nFAIL: Dependency check failed. Please install missing dependencies.")
        return 1
    
    if args.check_deps:
        print("\nPASS: All dependencies satisfied.")
        return 0
    
    # Build pytest command
    cmd = [sys.executable, '-m', 'pytest']
    
    if args.verbose:
        cmd.extend(['-v', '-s'])
    
    # Select tests to run
    if args.file:
        cmd.append(f"tests/{args.file}")
    elif args.quick:
        cmd.extend(['-m', 'not slow', 'tests/test_ocr_system.py::TestOCRBackendDetection'])
        cmd.extend(['tests/test_ocr_system.py::TestPaddleOCRInterface'])
    elif args.integration:
        cmd.extend(['-m', 'integration', 'tests/test_ocr_system.py::TestALASIntegration'])
    elif args.performance:
        cmd.extend(['-m', 'performance', 'tests/test_ocr_system.py::TestPerformance'])
    elif args.all:
        cmd.append('tests/')
    else:
        # Default: run main OCR tests
        cmd.append('tests/test_ocr_system.py')
    
    # Run tests
    success = run_command(cmd, "Running OCR System Tests")
    
    if success:
        print("\nSUCCESS: All tests completed successfully!")
        return 0
    else:
        print("\nFAIL: Some tests failed. Check output above for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())