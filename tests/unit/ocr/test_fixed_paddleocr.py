"""Test the fixed PaddleOCR 3.x implementation"""
import numpy as np
from module.ocr.ocr import OCR_MODEL

# Test 1: Check if OCR_MODEL exists and has required methods
print("Testing OCR_MODEL...")
print(f"OCR_MODEL type: {type(OCR_MODEL)}")
print(f"Has ocr method: {hasattr(OCR_MODEL, 'ocr')}")
print(f"Has close method: {hasattr(OCR_MODEL, 'close')}")

# Test 2: Create a simple test image with text
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (200, 50), color='white')
draw = ImageDraw.Draw(img)
try:
    # Try to use a basic font
    font = ImageFont.load_default()
except:
    font = None
draw.text((10, 10), "Test 123", fill='black', font=font)
img_array = np.array(img)

# Test 3: Test OCR with cls=True parameter
print("\nTesting OCR with cls=True...")
try:
    result = OCR_MODEL.ocr([img_array], cls=True)
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
    print("SUCCESS: OCR call with cls=True succeeded")
except Exception as e:
    print(f"FAILED: OCR call failed: {e}")

# Test 4: Test resource cleanup
print("\nTesting close method...")
try:
    OCR_MODEL.close()
    print("SUCCESS: close() method succeeded")
except Exception as e:
    print(f"FAILED: close() method failed: {e}")