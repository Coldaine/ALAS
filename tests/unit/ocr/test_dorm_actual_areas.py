#!/usr/bin/env python3
"""
Test OCR on actual visible areas in the dorm screenshot
"""
import cv2
import sys
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.ocr.ocr import Ocr, DigitCounter, Digit
from module.logger import logger

print("=== Testing OCR on Dorm Screenshot Visible Areas ===\n")

dorm_img = cv2.imread("sshots/Dorm.bmp")
print(f"Dorm image shape: {dorm_img.shape}")  # (1307, 2322, 3)

# Based on the visible screenshot, let's test these areas:
test_areas = [
    # Top bar
    ("Comfort value", (1285, 65, 1361, 100)),  # "Comfort 433" area
    ("Train counter", (280, 825, 350, 855)),   # "Train 6/6" area
    ("EXP display", (280, 855, 400, 885)),     # "1250/8000" supplies area
    
    # Try some adjusted coordinates based on typical ALAS locations
    ("Slot area adjusted", (280, 820, 350, 860)),  # Adjusted for "6/6"
]

for name, area in test_areas:
    x1, y1, x2, y2 = area
    
    # Skip if area is out of bounds
    if x2 > dorm_img.shape[1] or y2 > dorm_img.shape[0]:
        print(f"\n{name}: Out of bounds, skipping")
        continue
        
    crop = dorm_img[y1:y2, x1:x2]
    cv2.imwrite(f"test_{name.replace(' ', '_')}.png", crop)
    
    print(f"\n{name} {area}:")
    
    # Test with raw OCR
    ocr = Ocr(area, name=f"OCR_{name}")
    raw_result = ocr.ocr(crop)
    print(f"   Raw OCR: '{raw_result}'")
    
    # Test with DigitCounter if it might be a counter
    if "counter" in name.lower() or "/" in str(raw_result):
        counter = DigitCounter(area, name=f"Counter_{name}")
        counter_result = counter.ocr(crop)
        print(f"   DigitCounter: {counter_result}")

# Let's also try to find text in the whole image with simpler approach
print("\n\nTesting with EasyOCR fallback:")
# Force use of EasyOCR by temporarily disabling PaddleOCR
try:
    # Test with a known text area
    comfort_area = (1285, 65, 1361, 100)
    if comfort_area[2] <= dorm_img.shape[1] and comfort_area[3] <= dorm_img.shape[0]:
        crop = dorm_img[comfort_area[1]:comfort_area[3], comfort_area[0]:comfort_area[2]]
        
        # Save for inspection
        cv2.imwrite("test_comfort_crop.png", crop)
        print(f"Saved comfort area crop (shape: {crop.shape})")
        
except Exception as e:
    print(f"Error: {e}")

print("\nDone! Check the saved PNG files.")