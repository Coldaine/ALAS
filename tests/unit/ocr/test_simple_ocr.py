#!/usr/bin/env python3
"""Simple OCR test"""
from paddleocr import PaddleOCR
import cv2
import os

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

print("Initializing PaddleOCR...")
ocr = PaddleOCR(lang='en')

# Test with a cropped region
img_path = 'sshots/guild_mission_complete.png'
img = cv2.imread(img_path)

# Crop to "Mission Complete" area
crop = img[50:100, 300:500]
cv2.imwrite('test_crop.png', crop)

print("\nTesting OCR on cropped region...")
result = ocr.ocr(crop)

if result:
    print(f"Result type: {type(result)}")
    print(f"Result length: {len(result)}")
    if len(result) > 0:
        print(f"First element type: {type(result[0])}")
        if hasattr(result[0], '__len__'):
            print(f"First element length: {len(result[0])}")
        print(f"First element: {result[0]}")
else:
    print("No text detected")

# Test with full image but smaller size
print("\nTesting with resized image...")
small = cv2.resize(img, (800, 600))
result2 = ocr.ocr(small)

if result2 and result2[0]:
    print(f"Found {len(result2[0])} text regions in resized image")
    # Show first 5 results
    for i, (box, (text, score)) in enumerate(result2[0][:5]):
        print(f"  [{i}] '{text}' (score: {score:.3f})")
else:
    print("No text detected in resized image")