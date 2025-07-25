#!/usr/bin/env python3
"""
Simple test of OCR on dorm screenshot
"""
import cv2
import numpy as np
import sys
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.ocr.ocr import Ocr, DigitCounter, Digit
from module.base.button import Button
from module.base.utils import extract_letters

print("=== Simple OCR Test on Dorm Screenshot ===\n")

# Load dorm image
dorm_img = cv2.imread("sshots/Dorm.bmp")
print(f"Loaded dorm image: {dorm_img.shape}")

# Test specific areas based on the ALAS dorm module coordinates
# From dorm/assets.py: OCR_DORM_FILL area (813, 271, 987, 296)
# From dorm/assets.py: OCR_DORM_SLOT area (112, 662, 155, 694)

print("\n1. Testing Dorm Fill area (food counter):")
fill_area = (813, 271, 987, 296)
x1, y1, x2, y2 = fill_area
fill_crop = dorm_img[y1:y2, x1:x2]
cv2.imwrite("test_fill_crop.png", fill_crop)
print(f"   Saved fill area crop to test_fill_crop.png")

# Test with DigitCounter (which should parse X/Y format)
# Pass the area directly, not a Button object
fill_counter = DigitCounter(fill_area, name="DormFill")
fill_result = fill_counter.ocr(fill_crop)
print(f"   DigitCounter result: {fill_result}")

# Test raw OCR
fill_ocr = Ocr(fill_area, name="DormFillRaw")
fill_raw = fill_ocr.ocr(fill_crop)
print(f"   Raw OCR result: '{fill_raw}'")

print("\n2. Testing Dorm Slot area:")
slot_area = (112, 662, 155, 694)
x1, y1, x2, y2 = slot_area
slot_crop = dorm_img[y1:y2, x1:x2]
cv2.imwrite("test_slot_crop.png", slot_crop)
print(f"   Saved slot area crop to test_slot_crop.png")

# Test with DigitCounter
slot_counter = DigitCounter(slot_area, letter=(107, 89, 82), threshold=128, name="DormSlot")
slot_result = slot_counter.ocr(slot_crop)
print(f"   DigitCounter result: {slot_result}")

# Test raw OCR
slot_ocr = Ocr(slot_area, letter=(107, 89, 82), threshold=128, name="DormSlotRaw")
slot_raw = slot_ocr.ocr(slot_crop)
print(f"   Raw OCR result: '{slot_raw}'")

# Let's also check what the preprocessing does
print("\n3. Testing preprocessing on slot area:")
preprocessed = extract_letters(slot_crop, letter=(107, 89, 82), threshold=128)
cv2.imwrite("test_slot_preprocessed.png", preprocessed)
print(f"   Saved preprocessed image to test_slot_preprocessed.png")

print("\n4. Manual parsing test:")
# Test the parser directly
test_values = ["3/6", "100/5800", "0/0", "abc", ""]
for val in test_values:
    parsed = slot_counter._parse_counter(val)
    print(f"   '{val}' -> {parsed}")

print("\nDone! Check the saved PNG files to see the cropped areas.")