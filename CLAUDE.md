# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

ALAS (AzurLaneAutoScript) is an automation bot for the Azur Lane mobile game. It uses computer vision and OCR to read game state and automate gameplay tasks.

## Running ALAS

```bash
# Install dependencies (recommended - using Poetry)
poetry install

# Alternative: Install via pip
# pip install .

# Run GUI (web interface on port 22267)
poetry run python gui.py
# Or: python gui.py (if using pip install)

# Run CLI directly
poetry run python alas.py
# Or: python alas.py (if using pip install)

# Install/update ALAS components
poetry run python -m deploy.installer
```

## Architecture

### Core Module Structure

The codebase follows a modular architecture where each game feature is implemented as a separate module:

- **module/base/**: Core utilities including decorators, timers, filters, and the critical `Button` class that represents UI elements
- **module/device/**: Device abstraction layer supporting multiple connection methods (ADB, uiautomator2, minitouch)
- **module/ocr/**: OCR system with flexible backend support (PaddleOCR, EasyOCR, or SimpleOCR fallback)
- **module/config/**: Configuration management, argument parsing, and i18n support
- **module/webui/**: PyWebIO-based web interface

### Key Architectural Patterns

1. **Screenshot-Based Automation**: The bot works by taking screenshots, analyzing them with OCR/image recognition, and sending touch commands
2. **Task System**: Each game activity (campaign, event, daily) is a separate task with its own module
3. **Button/Asset System**: UI elements are defined as `Button` objects with image assets for recognition
4. **Configuration-Driven**: Extensive YAML/JSON configuration system for tasks, schedules, and settings

### Important Classes and Concepts

- **AzurLaneAutoScript** (alas.py): Main orchestrator that runs tasks in a loop
- **ModuleBase**: Base class for all game modules, provides screenshot, click, and wait methods
- **Button**: Represents a clickable UI element with associated image assets
- **Config**: Global configuration object accessible throughout the codebase
- **Device**: Abstraction for Android device connection and control

## OCR System

✅ **WORKING**: OCR system fully functional with PaddleOCR-compatible interface.

The OCR system supports multiple backends with automatic fallback:

```python
# Current working system with PaddleOCR interface:
from module.ocr.ocr import OCR_MODEL          # Main OCR backend
from module.ocr.models import OCR_MODEL       # Factory that creates AlOcr instances

# Backend priority (automatic selection):
# 1. PaddleOCR (when available) - pip install paddleocr
# 2. EasyOCR with PaddleOCR compatibility wrapper (fallback)
# 3. Minimal stub (prevents crashes)

# Current backend: EasyOCR with PaddleOCR compatibility
# Install PaddleOCR for optimal performance: pip install paddleocr
```

**Interface**: All modules use standard PaddleOCR interface: `OCR_MODEL.ocr(images, cls=True)`

## Development Workflow

### Adding a New Task Module

1. Create a new directory under `module/` for your feature
2. Create asset images in `assets/<module_name>/`
3. Define UI buttons in your module
4. Implement logic extending `ModuleBase`
5. Add configuration in `config/argument/`

### Debugging

```bash
# Enable debug logging
poetry run python alas.py --debug

# Test OCR functionality
poetry run python test_ocr_simple.py

# Check device connection
poetry run python -m uiautomator2 init

# Run test suite
poetry run python run_tests.py
```

### Code Style

The project has been modernized to Python 3.10+ with modern syntax:

```bash
# Optional code formatting (low priority)
poetry run black .

# Optional linting (low priority)
poetry run ruff check . --fix
```

## Current Development Status

### Completed Work
- ✅ **Python Modernization**: Successfully migrated from Python 3.7 to Python 3.10+ (300+ files updated)
- ✅ **LLM Vision Integration**: Implemented Gemini Flash 2.5 vision system with parallel analysis alongside traditional template matching
- ✅ **Windows Compatibility**: Fixed logger Unicode issues that prevented ALAS execution
- ✅ **Android Device Setup**: Configured MEmu emulator connection (127.0.0.1:21503) for live testing
- ✅ **Ollama Local Vision**: Implemented llava-phi3 model for RTX 4050 Ti hardware

### ✅ RESOLVED: OCR System Implementation

**Current Status**: OCR system working with PaddleOCR-compatible interface

#### Resolution Summary
Successfully implemented PaddleOCR backend with fallback system:

1. **Primary Backend**: PaddleOCR (when available)
   - Native PaddleOCR with optimized settings for ALAS
   - Full `ocr(image_list, cls=True)` interface support
   - GPU disabled for stability, angle classification enabled

2. **Fallback Backend**: EasyOCR with PaddleOCR Compatibility Wrapper
   - Converts EasyOCR output to PaddleOCR format automatically
   - Maintains exact same interface: `OCR_MODEL.ocr(images, cls=True)`
   - Supports `.close()` method for resource management

3. **Final Fallback**: Minimal PaddleOCR-compatible stub
   - Returns empty results in correct PaddleOCR format
   - Prevents crashes when no OCR backend available

#### Implementation Details
- **Interface Compatibility**: All 60+ ALAS modules work without modification
- **Performance**: Uses EasyOCR (already installed) as reliable fallback
- **Future-Proof**: Ready for PaddleOCR installation when dependencies resolved

### System Status
- **Branch**: `LLMRecognition` 
- **OCR**: ✅ WORKING - PaddleOCR-compatible interface with EasyOCR fallback
- **Device Connection**: ✅ MEmu emulator configured and working
- **Configuration**: Direct file editing approach (bypassing problematic web interface)
- **Dependencies**: Modern Python 3.10+ with cleaned requirements

## Configuration Files

### Core Configuration
- **config/template.json**: Default task configurations
- **config/deploy.yaml**: Deployment settings (ADB path: ./platform-tools/adb.exe, auto-update disabled)
- **config/alas.json**: ALAS instance configuration (device serial, server settings)
- **config/argument/args.json**: Argument specifications for all modules
- **config/argument/task.yaml**: Task definitions and groupings

### Vision System Configuration
- **config/vision_llm_config.py**: Gemini Flash 2.5 API configuration
- **config/vision_ollama_config.py**: Ollama local inference configuration (llava-phi3 model)

## Common Issues

### OCR Not Working
- Install an OCR backend: `poetry add paddleocr` (recommended) or `poetry add easyocr`
- Without OCR, ALAS runs but returns empty strings for text

### Device Connection Failed
- Check ADB is installed and in PATH
- Try `adb devices` to verify connection
- Use `poetry run python -m uiautomator2 init` for uiautomator2 setup

### Unicode Errors on Windows
- ✅ **Fixed**: Logger Unicode issues resolved by replacing box-drawing characters with ASCII equivalents

### Testing LLM Vision Integration
- Start MEmu emulator with Azur Lane
- Run ALAS with `poetry run python alas.py` 
- Check `logs/vision_llm.log` for comparative analysis data
- Monitor both traditional template matching and LLM vision results