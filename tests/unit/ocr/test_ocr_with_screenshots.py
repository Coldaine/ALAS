#!/usr/bin/env python3
"""
Test OCR with actual game screenshots
"""
import cv2
import os
import sys
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.ocr.ocr import Ocr, DigitCounter, OCR_MODEL
from module.base.button import Button

print("=== Testing OCR with Game Screenshots ===\n")

# First, let's look at the dorm screenshot to identify where the food counter might be
dorm_img_path = "sshots/Dorm.bmp"
if os.path.exists(dorm_img_path):
    print(f"Loading {dorm_img_path}...")
    dorm_img = cv2.imread(dorm_img_path)
    print(f"Dorm image shape: {dorm_img.shape}")
    
    # Let's test general OCR on the whole image first to see what text we can find
    print("\n1. Testing general OCR on full dorm image:")
    results = OCR_MODEL.ocr([dorm_img])
    if results and results[0]:
        print(f"   Found {len(results[0])} text regions:")
        for i, (box, (text, conf)) in enumerate(results[0][:10]):  # Show first 10
            print(f"   [{i}] '{text}' (conf: {conf:.3f}) at {box[0]}")
    else:
        print("   No text detected")

# Test specific areas where counters typically appear
print("\n2. Testing DigitCounter on common UI areas:")

# Common areas for counters in Azur Lane (these are estimates)
test_areas = [
    # Top bar (resources, etc)
    ("Top left resource", (50, 10, 150, 40)),
    ("Top center", (400, 10, 500, 40)),
    ("Top right resource", (700, 10, 800, 40)),
    # Dorm specific areas
    ("Dorm food area", (800, 260, 1000, 300)),  # Based on OCR_DORM_FILL coordinates
    ("Dorm slot counter", (100, 650, 170, 700)),  # Based on OCR_DORM_SLOT coordinates
]

for name, area in test_areas:
    x1, y1, x2, y2 = area
    if x2 <= dorm_img.shape[1] and y2 <= dorm_img.shape[0]:
        crop = dorm_img[y1:y2, x1:x2]
        
        # Test with DigitCounter
        counter_ocr = DigitCounter(Button(area=area), name=f"Test_{name}")
        result = counter_ocr.ocr(crop)
        
        print(f"\n   {name} {area}:")
        print(f"   DigitCounter result: {result}")
        
        # Also test raw OCR to see what text is there
        raw_ocr = Ocr(Button(area=area), name=f"Raw_{name}")
        raw_result = raw_ocr.ocr(crop)
        print(f"   Raw OCR result: '{raw_result}'")

# Test other screenshots
print("\n\n3. Testing other screenshots:")

other_images = [
    ("guild_mission_complete.png", [(340, 50, 500, 90)]),  # "Mission Complete" area
    ("depot_items_view.png", [(50, 10, 100, 35)]),         # "Depot" title
    ("research_lab_projects.png", [(10, 10, 100, 35)]),    # "Details" title
]

for img_name, test_regions in other_images:
    img_path = f"sshots/{img_name}"
    if os.path.exists(img_path):
        print(f"\n   Testing {img_name}:")
        img = cv2.imread(img_path)
        
        for region in test_regions:
            x1, y1, x2, y2 = region
            if x2 <= img.shape[1] and y2 <= img.shape[0]:
                crop = img[y1:y2, x1:x2]
                
                ocr = Ocr(Button(area=region), name=f"test_{img_name}")
                result = ocr.ocr(crop)
                print(f"   Region {region}: '{result}'")

print("\n\n4. Testing DigitCounter parsing:")
# Test the DigitCounter parsing directly
test_counter = DigitCounter(Button(area=(0,0,100,100)), name="TestCounter")

# Test various formats
test_strings = ["3/6", "100/500", "0/10", "invalid", ""]
for test_str in test_strings:
    result = test_counter._parse_counter(test_str)
    print(f"   '{test_str}' -> {result}")

print("\nDone!")