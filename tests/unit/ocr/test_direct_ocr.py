#!/usr/bin/env python3
"""
Test OCR directly without preprocessing
"""
import cv2
import sys
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.ocr.ocr import Ocr, DigitCounter
from module.logger import logger

print("=== Testing Direct OCR (no preprocessing) ===\n")

# Load image
dorm_img = cv2.imread("sshots/Dorm.bmp")
print(f"Image shape: {dorm_img.shape}")

# Test areas based on typical ALAS dorm coordinates
# Adjusting based on what we can see in the screenshot
test_areas = [
    ("Top Comfort", (1240, 50, 1380, 110)),     # "Comfort 433" area
    ("Train Status", (250, 810, 370, 870)),     # "Train 6/6" area  
    ("Supplies", (250, 840, 420, 900)),         # Experience/supplies
]

for name, area in test_areas:
    x1, y1, x2, y2 = area
    
    # Check bounds
    if x2 > dorm_img.shape[1] or y2 > dorm_img.shape[0]:
        print(f"\n{name}: Out of bounds ({area}), adjusting...")
        x2 = min(x2, dorm_img.shape[1])
        y2 = min(y2, dorm_img.shape[0])
        area = (x1, y1, x2, y2)
    
    crop = dorm_img[y1:y2, x1:x2]
    filename = f"direct_{name.replace(' ', '_')}.png"
    cv2.imwrite(filename, crop)
    
    print(f"\n{name} {area}:")
    print(f"   Saved to {filename} (shape: {crop.shape})")
    
    # Test with direct OCR (no preprocessing)
    ocr = Ocr(area, name=name)
    result = ocr.ocr(crop, direct_ocr=True)  # Skip preprocessing
    print(f"   Direct OCR result: '{result}'")
    
    # Also try DigitCounter with direct OCR
    if any(char in name.lower() for char in ["train", "supplies", "/"]):
        counter = DigitCounter(area, name=f"Counter_{name}")
        counter_result = counter.ocr(crop, direct_ocr=True)
        print(f"   DigitCounter result: {counter_result}")

# Try a larger area to see if we can get any text
print("\n\nTesting larger area:")
large_area = (200, 50, 600, 150)  # Top area
crop = dorm_img[large_area[1]:large_area[3], large_area[0]:large_area[2]]
cv2.imwrite("direct_large_area.png", crop)

ocr = Ocr(large_area, name="LargeArea")
result = ocr.ocr(crop, direct_ocr=True)
print(f"Large area OCR: '{result}'")

print("\nDone!")