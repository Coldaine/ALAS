#!/usr/bin/env python3
"""
Test OCR specifically on Dorm.bmp with targeted regions
"""
import cv2
import sys
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.logger import logger
from module.ocr.ocr import Ocr, DigitCounter

logger.info("=== Testing OCR on Dorm.bmp ===")

# Load the Dorm screenshot
img = cv2.imread("sshots/Dorm.bmp")
if img is None:
    logger.error("Could not load Dorm.bmp")
    exit(1)

height, width = img.shape[:2]
logger.info(f"Dorm image size: {width}x{height}")

# Define specific regions based on typical Dorm UI layout
test_regions = [
    # Top right - Comfort level
    ("Comfort", (1200, 40, 1400, 100)),
    
    # Bottom area - various counters
    ("Train", (240, 825, 330, 855)),
    ("Food", (100, 825, 200, 855)),
    ("Supplies", (450, 825, 550, 855)),
    
    # Time display
    ("Time", (50, 50, 200, 100)),
]

for region_name, coords in test_regions:
    x1, y1, x2, y2 = coords
    
    # Ensure coordinates are within bounds
    x1 = max(0, min(x1, width-1))
    x2 = max(0, min(x2, width-1))
    y1 = max(0, min(y1, height-1))
    y2 = max(0, min(y2, height-1))
    
    if x2 <= x1 or y2 <= y1:
        logger.warning(f"Invalid region {region_name}: {coords}")
        continue
    
    crop = img[y1:y2, x1:x2]
    
    # Save crop for debugging
    cv2.imwrite(f"test_dorm_{region_name.lower()}.png", crop)
    
    # Test with regular OCR
    ocr = Ocr(coords, name=region_name)
    result = ocr.ocr(crop, direct_ocr=True)
    logger.info(f"{region_name}: '{result}'")
    
    # If it contains a slash, try DigitCounter
    if "/" in str(result):
        counter = DigitCounter(coords, name=f"{region_name}_Counter")
        counter_result = counter.ocr(crop, direct_ocr=True)
        logger.info(f"  Parsed as counter: {counter_result}")

logger.info("\nOCR test complete!")