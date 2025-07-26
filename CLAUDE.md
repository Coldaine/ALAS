# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Session Learnings (2025-07-26)

### Architecture & Systems

1. **Dual Logging Systems**: ALAS has two separate logging systems:
   - Main logger (`/log/`) - The useful operational logs for debugging
   - Vision logger (`/logs/`) - For the LLM vision integration (less useful for debugging)

2. **Multiple Launch Methods**: 
   - Direct execution: `python alas.py`
   - Web GUI: `python gui.py` (PyWebIO-based on port 22267)
   - Tkinter GUI: `python run_gui.py` (new desktop interface with pause/resume buttons)

3. **Graceful Shutdown**: ALAS already had a `stop_event` mechanism for the web GUI, extended with signal handlers for Ctrl+C interrupts in main execution.

### OCR System Details

4. **OCR Backend Priority**: 
   - Primary: PaddleOCR (when available)
   - Fallback: EasyOCR with PaddleOCR compatibility wrapper
   - Final fallback: Minimal stub to prevent crashes
   - All use the same interface: `OCR_MODEL.ocr(images, cls=True)`

5. **Vision OCR**: Alternative LLM-based OCR using Google's Gemini Flash 2.5 (requires API key and connected device for cost protection)

### Recent Bug Fixes

6. **Log File Persistence**: The web GUI wasn't clearing logs on startup because it bypassed the `clear_on_start` parameter - fixed by modifying both `process_manager.py` and `alas.py`

7. **NoneType Error**: Fixed in `log_res.py` where it tried to access dictionary methods on None values

8. **Game Stuck Detection**: ALAS has built-in stuck detection - when it waits too long for UI elements (like `GET_ITEMS_1` appearing repeatedly), it automatically restarts the game

### Operational Insights

9. **Task Scheduling**: ALAS runs tasks sequentially based on their scheduled times, automatically delaying failed tasks

10. **Fleet Management**: The bot tracks available fleets (0/4 means all busy) and won't attempt commissions without available fleets

11. **Error Recovery**: ALAS has robust error handling:
    - Auto-restarts game when stuck
    - Saves error screenshots in `/log/error/`
    - Retries failed operations
    - Handles connection issues gracefully

12. **Commission Detection**: Uses LLM parsing to read commission timers and statuses, with fallback handling for parsing failures

### Action Screenshot Archiving

Screenshots are automatically archived before every bot action for debugging purposes:

1. **How it works**: Before each click, swipe, or drag action, the bot saves the current screen state
2. **Location**: Screenshots are saved to `log/action_archive/<date>/<action>/<timestamp>_<button>.png`
3. **Always enabled**: No configuration needed - runs automatically
4. **Performance**: Zero impact on bot speed - uses async background thread for saving
5. **Storage management**: Archives older than 7 days are automatically cleaned up on startup
6. **Error handling**: Robust filename sanitization and I/O error handling

Technical improvements:
- **Async I/O**: Screenshot saving happens in a background thread, never blocking bot actions
- **Auto-cleanup**: Old archives are removed to prevent unbounded disk usage
- **Robust sanitization**: All invalid Windows filename characters are handled

This helps understand:
- What the bot saw before taking an action
- Why certain decisions were made
- Debug issues when the bot gets stuck

### Logging System

Each ALAS session creates a unique log file:

1. **Format**: `log/YYYY-MM-DD_HHMMSS_<config_name>.txt`
2. **Example**: `log/2025-07-26_143052_alas.txt`
3. **No overwrites**: Each run gets its own timestamped log
4. **Clean separation**: Easy to find logs for specific sessions

## ⚠️ IMPORTANT: Always Use Poetry

**ALWAYS use Poetry for this project. Never use pip directly or system Python.**

Poetry manages dependencies in an isolated virtual environment and ensures consistent versions. The pyproject.toml has been carefully configured with exact dependency versions that work together.

```bash
# REQUIRED: Install Poetry if not available
curl -sSL https://install.python-poetry.org | python -

# REQUIRED: Install dependencies
poetry install

# REQUIRED: Always use 'poetry run' prefix for all Python commands
poetry run python alas.py
poetry run python gui.py
poetry run python -m deploy.installer
```

## Overview

ALAS (AzurLaneAutoScript) is an automation bot for the Azur Lane mobile game. It uses computer vision and OCR to read game state and automate gameplay tasks.

## Running ALAS

```bash
# Install dependencies with Poetry (REQUIRED)
poetry install

# Run CLI directly (RECOMMENDED)
poetry run python alas.py

# Run GUI (web interface on port 22267)
poetry run python gui.py

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

✅ **WORKING**: OCR system fully functional with dual-mode operation.

### Vision OCR (Default)
ALAS now uses direct LLM vision for text reading when a device is connected:

```python
# Vision OCR is automatic when:
# 1. GOOGLE_API_KEY is set as environment variable
# 2. Android device is connected (cost protection)
# 3. Google generativeai package is installed: pip install google-generativeai

# The system automatically falls back to traditional OCR if:
# - No device connected
# - No API key available  
# - Vision API fails
```

### Traditional OCR (Fallback)
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

### Testing

```bash
# Run full test suite
poetry run python run_tests.py

# Run quick unit tests only
poetry run python run_tests.py --quick

# Run integration tests
poetry run python run_tests.py --integration

# Run specific test file
poetry run python run_tests.py --file test_ocr_system.py

# Check dependencies only
poetry run python run_tests.py --check-deps

# Run pytest directly (advanced)
poetry run python -m pytest tests/ -v
```

### Debugging

```bash
# Enable debug logging
poetry run python alas.py --debug

# Check device connection
poetry run python -m uiautomator2 init

# Test OCR with actual screenshots
poetry run python test_ocr_with_screenshots.py

# Live OCR testing
poetry run python test_ocr_live.py
```

### Code Quality

The project uses Python 3.10+ with modern syntax and comprehensive tooling:

```bash
# Code formatting
poetry run black .

# Linting and code analysis
poetry run ruff check . --fix

# Type checking
poetry run mypy module/

# Import sorting
poetry run isort .

# Run all quality checks
poetry run black . && poetry run ruff check . --fix && poetry run isort .
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

## Using Gemini for Code Analysis

### When to Use Gemini

Gemini is available on this system and should be used for:
1. **Large file summaries** - When you need to understand big configuration files or complex modules
2. **Huge file edits** - When making extensive changes across large files
3. **Code analysis** - Understanding file structure and purpose
4. **Configuration reviews** - Analyzing JSON/YAML configuration files

### How to Call Gemini

**Best Practice**: Write your prompts in .md files for complex analysis tasks. This allows for:
- Multi-line prompts with proper formatting
- Reusable analysis templates
- Clear documentation of what was analyzed

#### Method 1: Using .md Prompt Files (RECOMMENDED)

**Step 1: Write the prompt to a .md file**
```bash
# Use the Write tool to create a prompt file
# Example: analyzing a configuration file
```

**analyze_config.md**:
```markdown
Analyze the configuration file and explain:
1. The overall structure
2. Key settings for each module
3. How tasks are scheduled
4. Important configuration patterns
```

**Step 2: Call gemini with both the prompt file and target file**
```bash
# Use the Bash tool to execute gemini
gemini -p "@analyze_config.md @config/template.json"
```

The gemini command will:
1. Read the prompt from `analyze_config.md`
2. Read the target file `config/template.json`
3. Apply the prompt to analyze the target file
4. Return the analysis results

#### Method 2: Inline Prompts (for simple queries)
```bash
# Quick one-line analysis
gemini -p "@src/main.py Explain this file's purpose"
```

#### Example Prompt Files

Create reusable prompt templates:

**code_review.md**:
```markdown
Review this code file and provide:
1. Summary of purpose and functionality
2. Key classes and methods
3. Important algorithms or logic flows
4. Potential issues or improvements
5. Dependencies and external calls
```

**config_analysis.md**:
```markdown
Analyze this configuration file:
1. Document all available options
2. Explain the purpose of each section
3. Identify default values and their implications
4. Suggest optimization opportunities
5. Note any unclear or potentially problematic settings
```

### Complete Workflow Example

Here's how Claude should use Gemini for analysis:

```python
# 1. First, use the Write tool to create your prompt file
Write(
    file_path="analyze_exercise.md",
    content="""Analyze the Exercise module and explain:
1. How opponent selection works
2. The admiral trial timing strategies
3. How it calculates exercise priorities
4. Key configuration options and their effects"""
)

# 2. Then, use the Bash tool to call gemini
Bash(
    command='gemini -p "@analyze_exercise.md @module/exercise/exercise.py"',
    description="Analyze exercise module with Gemini"
)

# 3. Gemini will return the analysis, which you can then use
# to understand the code without consuming your context window
```

### Quick Reference
```bash
# For configuration files
gemini -p "@config_analysis.md @config/template.json"

# For code modules
gemini -p "@code_review.md @module/exercise/exercise.py"

# For understanding complex logic
gemini -p "@logic_analysis.md @module/config/config.py"
```

### Benefits of Using Gemini

1. **Context efficiency** - Gemini can analyze large files without consuming your context window
2. **Speed** - Faster analysis of big files compared to reading line-by-line
3. **Accuracy** - Direct file analysis without truncation or sampling
4. **API availability** - Both GOOGLE_API_KEY and GEMINI_API_KEY are configured on this system

### Important Notes

- Gemini has both API keys set (GOOGLE_API_KEY takes precedence)
- Use Gemini for analysis and understanding, but implement changes yourself
- Particularly useful for this large ALAS codebase with 300+ files
- Helps preserve context for actual coding work