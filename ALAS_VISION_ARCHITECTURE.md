# ALAS Vision Architecture: Direct LLM Vision for Text Reading

## Executive Summary

**Goal**: Replace traditional OCR (PaddleOCR/EasyOCR) with direct LLM vision to eliminate OCR errors entirely.

**Current State**: Screenshot → OCR → Garbled Text → LLM Text Fixing → Clean Text  
**Target State**: Screenshot → LLM Vision → Clean Text

**Key Requirement**: No API calls when emulator/device is disconnected (cost protection).

## The Problem

1. **Current System Wastes Resources**:
   - OCR produces garbled text (e.g., "D--457-—UL" instead of "D-457-UL")
   - LLM is called to fix OCR errors
   - Two-step process when one would suffice

2. **Existing Working Components**:
   - Gemini Flash 2.5 integration already exists and works
   - LLM parsers already handle text cleaning
   - All the infrastructure is there, just used inefficiently

## EXACT Implementation Changes Required

### 1. Modify `module/ocr/ocr.py` - Add Vision Mode Check

**Location**: Line 259, in the `Ocr.ocr()` method

**Current Code** (lines 259-279):
```python
def ocr(self, image, direct_ocr=False):
    """
    Args:
        image (np.ndarray, list[np.ndarray]):
        direct_ocr (bool): True to skip preprocess.

    Returns:
        str, list[str]:
    """
    if image is None:
        return '' if not isinstance(self._buttons, list) or len(self._buttons) <= 1 else []

    image_list = image if isinstance(image, list) else [image]
    if not image_list:
        return []

    result_list = []
    try:
        # Pre-process
        preprocessed_images = []
        if not direct_ocr:
```

**Change To**:
```python
def ocr(self, image, direct_ocr=False):
    """
    Args:
        image (np.ndarray, list[np.ndarray]):
        direct_ocr (bool): True to skip preprocess.

    Returns:
        str, list[str]:
    """
    if image is None:
        return '' if not isinstance(self._buttons, list) or len(self._buttons) <= 1 else []

    image_list = image if isinstance(image, list) else [image]
    if not image_list:
        return []

    # Check for vision mode
    if os.environ.get('ALAS_USE_VISION_BRIDGE', 'false').lower() == 'true':
        # Check device connection
        try:
            from module.device.app_control import AppControl
            # If we can check app status, device is connected
            device_connected = hasattr(self, 'device') and self.device.app_is_running() is not None
        except:
            device_connected = False
            
        if device_connected:
            return self._vision_ocr(image_list)
    
    result_list = []
    try:
        # Pre-process
        preprocessed_images = []
        if not direct_ocr:
```

### 2. Add Vision OCR Method to `module/ocr/ocr.py`

**Location**: Add after line 325 (after `ocr_result_process` method)

**Add This Method**:
```python
def _vision_ocr(self, image_list):
    """Use Gemini vision to read text directly from images"""
    try:
        import google.generativeai as genai
        from config.vision_llm_config import GOOGLE_API_KEY, GEMINI_MODEL
        from PIL import Image
        import numpy as np
        
        if not GOOGLE_API_KEY:
            logger.warning("No Google API key, falling back to OCR")
            return self._traditional_ocr(image_list)
            
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        results = []
        for idx, img in enumerate(image_list):
            # Get button context
            button = self._buttons[idx] if isinstance(self._buttons, list) else self._buttons
            button_name = button.name if hasattr(button, 'name') else 'unknown'
            
            # Convert numpy to PIL
            if isinstance(img, np.ndarray):
                pil_img = Image.fromarray(img)
            else:
                pil_img = img
                
            # Get appropriate prompt based on button name
            prompt = self._get_vision_prompt(button_name)
            
            try:
                # Check cache first
                cache_key = f"{button_name}_{hash(img.tobytes())}"
                if hasattr(self, '_vision_cache') and cache_key in self._vision_cache:
                    age = time.time() - self._vision_cache_time.get(cache_key, 0)
                    if age < 30:  # 30 second cache
                        results.append(self._vision_cache[cache_key])
                        continue
                
                # Call Gemini
                response = model.generate_content([prompt, pil_img])
                text = response.text.strip()
                
                # Cache result
                if not hasattr(self, '_vision_cache'):
                    self._vision_cache = {}
                    self._vision_cache_time = {}
                self._vision_cache[cache_key] = text
                self._vision_cache_time[cache_key] = time.time()
                
                results.append(text)
            except Exception as e:
                logger.error(f"Vision OCR failed for {button_name}: {e}")
                results.append("")
                
        return results[0] if len(results) == 1 else results
        
    except ImportError:
        logger.warning("Google AI not available, falling back to OCR")
        return self._traditional_ocr(image_list)
        
def _traditional_ocr(self, image_list):
    """Fallback to traditional OCR"""
    # Move existing OCR logic here
    pass

def _get_vision_prompt(self, button_name):
    """Get appropriate prompt based on button context"""
    prompts = {
        'COMMISSION_TIME': "Read the time from this Azur Lane commission timer. Return format: HH:MM:SS",
        'RESEARCH_PROJECT': "Read the research project code. Format: X-NNN-XX",
        'SHOP_PRICE': "Read the medal price shown. Return only the number.",
        'FLEET_POWER': "Read the fleet power number. No commas.",
        'DORM_FOOD': "Read the food counter. Format: CURRENT/MAXIMUM",
        'SOS_CHAPTER': "Read the chapter number (3-10). Return only the number.",
        'STAGE_NAME': "Read the stage name. Examples: 7-2, D3, SP3",
    }
    
    # Check if button name contains any key
    for key, prompt in prompts.items():
        if key in button_name.upper():
            return prompt
            
    # Default prompt
    return "Read any text in this image from Azur Lane. Return only the text, no explanation."
```

### 3. Import Required Modules at Top of `module/ocr/ocr.py`

**Location**: After line 5 (after existing imports)

**Add**:
```python
import os
import time
```

### 4. Ensure Device Connection Check Works

The device connection check needs access to the device instance. Since OCR classes don't have direct access to device, we need a simpler approach:

**Alternative Approach**: Check if ADB is responding

**Modify the device check in `_vision_ocr` to**:
```python
# Check device connection by trying to get ADB devices
device_connected = False
try:
    from module.device.connection import AdbClient
    client = AdbClient()
    devices = client.device_list()
    device_connected = len(devices) > 0
except:
    device_connected = False
```

### 5. Environment Variable Setup

Create `run_alas_vision.bat`:
```batch
@echo off
echo Starting ALAS with Vision Bridge enabled...
set ALAS_USE_VISION_BRIDGE=true
set GOOGLE_API_KEY=your-api-key-here
poetry run python alas.py
```

## Testing the Implementation

1. Set environment variables:
   - `ALAS_USE_VISION_BRIDGE=true`
   - `GOOGLE_API_KEY=your-actual-key`

2. Run ALAS normally

3. Check logs for "Vision OCR" messages

4. Disconnect emulator and verify no API calls are made

## What This Implementation Does

1. **Minimal Changes**: Only modifies the existing `Ocr.ocr()` method
2. **Reuses Infrastructure**: Uses existing Gemini config from `config/vision_llm_config.py`
3. **Cost Protection**: Checks device connection before API calls
4. **Caching**: 30-second cache to avoid duplicate API calls
5. **Fallback**: Automatically falls back to traditional OCR if vision unavailable

## What We're NOT Doing

1. Not creating new files (except the .bat launcher)
2. Not modifying the existing LLM parsers
3. Not creating complex managers or factories
4. Not writing migration scripts
5. Not changing how modules call OCR

The total change is approximately 100 lines of code in one file.