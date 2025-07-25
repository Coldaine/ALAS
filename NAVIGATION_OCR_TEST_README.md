# Navigation OCR Test Suite

This test suite provides closed-loop navigation testing for ALAS, specifically testing problematic screens like Research and Dorm with OCR verification.

## Test Scripts

### 1. `test_ocr_direct_navigation.py` (RECOMMENDED)
The most direct and reliable test script. Uses minimal ALAS components to navigate and test OCR.

**Features:**
- Direct device connection without full ALAS initialization
- Navigates to Research and Dorm screens
- Runs OCR on each screen and saves results
- Captures screenshots with text region highlights
- Generates detailed report with OCR results

**Usage:**
```bash
# Default (MEmu on 127.0.0.1:21503)
poetry run python test_ocr_direct_navigation.py

# Custom device
poetry run python test_ocr_direct_navigation.py 127.0.0.1:5555
```

### 2. `test_navigation_ocr_simple.py`
Uses ALAS instance for navigation with simplified initialization.

**Usage:**
```bash
poetry run python test_navigation_ocr_simple.py
```

### 3. `test_navigation_ocr_loop.py`
Full-featured test inheriting from UI class (may have initialization issues).

**Usage:**
```bash
poetry run python test_navigation_ocr_loop.py
```

## Prerequisites

1. **Game must be on MAIN MENU** before running tests
2. MEmu or emulator running with Azur Lane
3. ALAS configured (config/alas.json exists)
4. Poetry environment activated with dependencies installed

## Test Flow

1. **Initial State**: Captures main menu screenshot and runs OCR
2. **Research Test**:
   - Navigate to Research Menu
   - Navigate to Research Lab
   - Run OCR and capture screenshots
   - Return to main menu
3. **Dorm Test**:
   - Navigate to Dorm Menu
   - Navigate to Dorm Room
   - Run OCR and capture screenshots
   - Return to main menu
4. **Results**: Generates report with all OCR results

## Output

Each test run creates a timestamped directory containing:

```
test_nav_ocr_YYYYMMDD_HHMMSS/
├── results.json          # Raw test data
├── report.md            # Human-readable report
├── initial_state.png    # Starting screenshot
├── research_menu.png    # Research menu screenshot
├── research_full.png    # Research lab screenshot
├── research_text_0_*.png # Cropped text regions
├── dorm_menu.png        # Dorm menu screenshot
├── dorm_full.png        # Dorm room screenshot
├── dorm_text_0_*.png    # Cropped text regions
└── ...
```

## Report Format

The markdown report includes:

1. **Test Summary**: Navigation success, OCR success, text count
2. **OCR Details**: For each screen:
   - Success/failure status
   - Processing time
   - Number of texts found
   - Sample texts with confidence scores
3. **Errors**: Any errors encountered

## Example Report Output

```markdown
# Navigation OCR Test Report

**Date**: 2025-07-25T10:30:00
**Device**: 127.0.0.1:21503

## Test Summary

| Screen | Navigation | OCR | Texts Found |
|--------|------------|-----|-------------|
| main_menu | ✅ | ✅ | 25 |
| research | ✅ | ✅ | 18 |
| dorm | ✅ | ✅ | 22 |

## OCR Details

### research

- **Status**: Success
- **Time**: 450.3ms
- **Texts**: 18

**Sample texts**:
1. `Research Lab` (conf: 0.998)
2. `Duration` (conf: 0.995)
3. `Start Research` (conf: 0.987)
...
```

## Troubleshooting

### Device Connection Failed
- Ensure emulator is running
- Check ADB connection: `adb devices`
- Verify serial number matches your emulator

### Navigation Failed
- Ensure game is on main menu before starting
- Check if UI has changed (buttons may need updating)
- Verify screen resolution is 1280x720

### OCR Returns Empty
- Check if OCR backend is installed: `poetry add paddleocr` or `poetry add easyocr`
- Verify screenshots are being captured correctly
- Check console for OCR initialization errors

### Test Hangs
- Game may be showing unexpected popup
- Network lag causing slow screen transitions
- Kill test with Ctrl+C and check last screenshot

## Interpreting Results

1. **High confidence texts** (>0.9) are reliable detections
2. **Low text count** may indicate OCR issues or wrong screen
3. **Navigation failures** suggest UI changes or popups
4. **OCR timeouts** indicate performance issues

## Next Steps

After running tests:
1. Review the markdown report for OCR accuracy
2. Check screenshots to verify correct navigation
3. Compare OCR results with expected UI texts
4. Use results to debug OCR issues in production ALAS