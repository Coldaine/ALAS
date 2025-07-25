#!/usr/bin/env python3
"""
Test direct PaddleOCR 3.1.0 API
"""
import cv2
import numpy as np
from paddleocr import PaddleOCR

print("Testing PaddleOCR 3.1.0 direct API...")

# Initialize
ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

# Create test image
img = np.ones((50, 200, 3), dtype=np.uint8) * 255
cv2.putText(img, "TEST 123", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
cv2.imwrite("test_direct_paddle.png", img)

# Test ocr() method
print("\nTesting ocr() method:")
result = ocr.ocr(img, cls=True)
print(f"Result type: {type(result)}")
print(f"Result: {result}")

if result and result[0]:
    print(f"\nFirst detection: {result[0][0]}")
    print(f"Number of detections: {len(result[0])}")
    
# Test on grayscale converted to RGB
print("\nTesting with grayscale->RGB conversion:")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
result2 = ocr.ocr(rgb, cls=True)
print(f"Result: {result2}")