#!/usr/bin/env python3
"""
Test with EasyOCR fallback
"""
import cv2
import sys
sys.path.insert(0, 'C:\\_Development\\ALAS')

# Force EasyOCR by preventing PaddleOCR import
import module.ocr.ocr
module.ocr.ocr.PaddleOCR = None  # Disable PaddleOCR

# Now import will use EasyOCR fallback
from module.ocr.ocr import Ocr, DigitCounter, OCR_MODEL
from module.logger import logger

print("=== Testing with EasyOCR Fallback ===\n")
print(f"OCR backend: {OCR_MODEL.name if hasattr(OCR_MODEL, 'name') else type(OCR_MODEL)}")

# Test on guild mission complete screenshot (should have clear text)
img = cv2.imread("sshots/guild_mission_complete.png")
print(f"\nTesting guild_mission_complete.png (shape: {img.shape})")

# Test the "Mission Complete" text area
mission_area = (340, 50, 500, 90)
x1, y1, x2, y2 = mission_area
crop = img[y1:y2, x1:x2]
cv2.imwrite("test_mission_text.png", crop)

ocr = Ocr(mission_area, name="MissionText")
result = ocr.ocr(crop, direct_ocr=True)
print(f"Mission text OCR: '{result}'")

# Test dorm with train counter
dorm_img = cv2.imread("sshots/Dorm.bmp")
print(f"\nTesting Dorm.bmp for counters")

# The "Train 6/6" area based on visual inspection
train_area = (240, 825, 330, 855)
x1, y1, x2, y2 = train_area
crop = dorm_img[y1:y2, x1:x2]
cv2.imwrite("test_train_counter.png", crop)

counter = DigitCounter(train_area, name="TrainCounter")
result = counter.ocr(crop, direct_ocr=True)
print(f"Train counter result: {result}")

print("\nDone!")