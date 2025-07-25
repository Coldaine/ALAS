#!/usr/bin/env python3
"""
Test OCR with actual game screenshots
"""
import cv2
import os
from module.ocr.ocr import Ocr, OCR_MODEL

print("=== Testing OCR with Game Screenshots ===\n")

# Test images
test_images = [
    ("sshots/guild_mission_complete.png", [(340, 50, 500, 90)]),  # "Mission Complete" text
    ("sshots/depot_items_view.png", [(50, 10, 100, 35)]),         # "Depot" title
    ("sshots/research_lab_projects.png", [(10, 10, 100, 35)]),    # "Details" title
]

for img_path, regions in test_images:
    if os.path.exists(img_path):
        print(f"\nTesting: {img_path}")
        img = cv2.imread(img_path)
        
        # Test full image OCR
        print("  Full image OCR:")
        results = OCR_MODEL.ocr([img], cls=True)
        if results and results[0]:
            print(f"    Found {len(results[0])} text regions")
            for i, (box, (text, conf)) in enumerate(results[0][:5]):
                print(f"    [{i}] '{text}' (conf: {conf:.3f})")
        else:
            print("    No text detected")
        
        # Test specific regions
        for region in regions:
            x1, y1, x2, y2 = region
            crop = img[y1:y2, x1:x2]
            print(f"\n  Region {region} OCR:")
            
            ocr_obj = Ocr(buttons=region, name=f"test_{os.path.basename(img_path)}")
            result = ocr_obj.ocr(crop, direct_ocr=True)
            print(f"    Result: '{result}'")

print("\n=== Testing with ALAS Button Areas ===")

# Test typical ALAS button areas
button_coords = [
    (100, 100, 200, 130),  # Typical button size
    (50, 50, 150, 80),     # Smaller button
]

test_img = "sshots/guild_mission_complete.png"
if os.path.exists(test_img):
    img = cv2.imread(test_img)
    
    for coords in button_coords:
        x1, y1, x2, y2 = coords
        if x2 <= img.shape[1] and y2 <= img.shape[0]:
            crop = img[y1:y2, x1:x2]
            
            # Test with Ocr class (includes preprocessing)
            ocr = Ocr(buttons=coords, name="test_button")
            result = ocr.ocr(crop)
            print(f"\nButton area {coords}: '{result}'")