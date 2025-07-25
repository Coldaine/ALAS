# Method Trace: OCR Integration System

## **📍 Location**
- **File**: `module/ocr/ocr.py`
- **Class**: Various OCR classes
- **Lines**: 1-465

## **📖 Purpose & Functionality**
Provides OCR functionality with PaddleOCR v3 integration and EasyOCR fallback. Critical for text recognition in game UI.

## **🔄 Execution Path**

### Step 1: OCR Backend Detection
- **Code**: `try: _test_ocr = PaddleOCR(lang='en')`
- **Purpose**: Test if PaddleOCR is available and working
- **Inputs**: Language configuration
- **Outputs**: OCR instance or exception
- **Side Effects**: May initialize PaddleOCR backend

### Step 2: Fallback to EasyOCR
- **Code**: `except Exception: _test_ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False, use_gpu=False)`
- **Purpose**: Use EasyOCR with PaddleOCR compatibility wrapper
- **Inputs**: OCR configuration parameters
- **Outputs**: Compatible OCR instance
- **Side Effects**: Initializes EasyOCR backend

### Step 3: OCR Model Assignment
- **Code**: `OCR_MODEL = _test_ocr`
- **Purpose**: Set global OCR model for use throughout ALAS
- **Inputs**: Initialized OCR instance
- **Outputs**: Global OCR_MODEL variable
- **Side Effects**: Makes OCR available to all modules

## **🌿 Branch Analysis**

### Backend Selection Branch
- **If PaddleOCR available**: Use native PaddleOCR
- **If PaddleOCR fails**: Fall back to EasyOCR with compatibility wrapper
- **If both fail**: Use minimal stub (prevents crashes)

### Configuration Branch
- **GPU Usage**: Disabled for stability (use_gpu=False)
- **Angle Classification**: Enabled for better accuracy (use_angle_cls=True)
- **Logging**: Disabled for cleaner output (show_log=False)

## **⚠️ Exception Paths**

### PaddleOCR Initialization Failure
- **Source**: Missing paddle dependency or GPU issues
- **Handling**: Fall back to EasyOCR wrapper
- **Recovery**: Seamless fallback with same interface

### EasyOCR Initialization Failure
- **Source**: Missing EasyOCR or system issues
- **Handling**: Fall back to minimal stub
- **Recovery**: Prevents crashes, returns empty results

## **🔗 External Calls**

### PaddleOCR Operations
- **ocr(image_list, cls=True)**: Main OCR processing
- **Expected Behavior**: Return list of text detection results

### EasyOCR Operations
- **readtext()**: Text detection and recognition
- **Expected Behavior**: Return list of detection results (converted to PaddleOCR format)

## **🚨 Critical Analysis**

### Performance Impact
- **Initialization**: One-time cost during module import
- **Processing**: Varies by backend and image complexity
- **Memory**: OCR models require significant memory

### Reliability Concerns
- **Backend Availability**: Depends on external OCR libraries
- **Format Compatibility**: EasyOCR results must be converted to PaddleOCR format
- **Error Handling**: Must gracefully handle OCR failures

### Improvement Suggestions
- **Lazy Loading**: Initialize OCR only when needed
- **Backend Selection**: Allow runtime backend switching
- **Performance Monitoring**: Track OCR processing times
- **Result Caching**: Cache OCR results for identical images
