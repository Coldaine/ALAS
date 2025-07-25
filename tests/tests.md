# ALAS Test Suite Documentation

This document provides an overview of the test suite organization and the purpose of each test file.

## Test Directory Structure

```
tests/
├── unit/                 # Unit tests
│   ├── ocr/             # OCR-related unit tests
│   └── core/             # Core functionality tests
├── integration/         # Integration tests
├── e2e/                 # End-to-end tests
├── deployment/          # Deployment-related tests
└── utils/               # Test utilities and helpers
```

## Unit Tests

### OCR Tests (`tests/unit/ocr/`)

- `test_ocr.py`: Basic OCR functionality tests, including model loading and text recognition
- `test_ocr_performance.py`: Performance testing for OCR components
- `test_ocr_simple.py`: Simplified OCR tests for quick verification
- `test_ocr_system.py`: Comprehensive tests for the OCR system

### Core Tests (`tests/unit/core/`)

- `test_syntax.py`: Syntax checking for Python files
- `test_integration.py`: Basic integration tests for core functionality
- `test_modernization.py`: Tests for modern Python features and compatibility

## Integration Tests (`tests/integration/`)

- `test_config.py`: Configuration file validation and loading tests
- `test_module_interaction.py`: Tests for module interactions

## End-to-End Tests (`tests/e2e/`)

- `test_game_flow.py`: Full game flow testing
- `test_screenshots.py`: Screenshot-based testing

## Deployment Tests (`tests/deployment/`)

- `test_installer.py`: Installer and deployment verification

## Test Utilities (`tests/utils/`)

- `test_helpers.py`: Common test utilities and helper functions

## Running Tests

To run all tests:

```bash
python -m pytest tests/
```

To run a specific test category:

```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Run end-to-end tests
python -m pytest tests/e2e/
```

## Adding New Tests

When adding new tests, please follow these guidelines:

1. Place unit tests in the appropriate subdirectory under `tests/unit/`
2. Group related tests in the same file
3. Use descriptive test function names
4. Include docstrings explaining what each test verifies
5. Update this documentation when adding new test categories or files
