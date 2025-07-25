#!/usr/bin/env python3
"""
Test PaddleOCR API directly to understand its output format
"""
from paddleocr import PaddleOCR
import cv2
import json

# Initialize PaddleOCR
ocr = PaddleOCR(lang='en')

# Test with screenshot
img_path = 'sshots/guild_mission_complete.png'
img = cv2.imread(img_path)

print("=== Testing PaddleOCR predict() method ===")
try:
    result = ocr.predict(img)
    print(f"Result type: {type(result)}")
    print(f"Result: {json.dumps(result, indent=2, default=str)}")
except Exception as e:
    print(f"predict() failed: {e}")

print("\n=== Testing old ocr() method (if available) ===")
try:
    # Try the old API
    result = ocr.ocr(img)
    print(f"Result type: {type(result)}")
    if isinstance(result, list) and result:
        print(f"Number of results: {len(result)}")
        if result[0]:
            print(f"First detection: {result[0][0] if result[0] else 'None'}")
except AttributeError:
    print("ocr() method not available")

print("\n=== Checking available methods ===")
methods = [m for m in dir(ocr) if not m.startswith('_')]
print(f"Available methods: {methods}")

# Try different approaches
print("\n=== Testing with smaller image region ===")
# Crop to a smaller region that likely contains text
crop = img[50:100, 300:500]  # Mission Complete area
cv2.imwrite('test_crop.png', crop)

result = ocr.predict(crop)
print(f"Cropped result: {json.dumps(result, indent=2, default=str)}")