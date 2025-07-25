#!/usr/bin/env python3
"""
Test OCR on actual screenshots with simplified approach
"""
import cv2
import sys
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.logger import logger
from module.ocr.al_ocr import AlOcr

logger.info("=== Testing OCR on Actual Screenshots ===")

# Use AlOcr for simpler testing
ocr = AlOcr(name='azur_lane')

# Test files
test_files = [
    ("sshots/cii ree rre MS Prototype Prototype Prototype Proto.png", "Depot/Inventory"),
    ("sshots/doys Move 00009_00055 Supplies 124800  MEN EXP EXP.bmp", "Dorm"),
    ("sshots/FLEET MISSION 100_100 Personal tasks completed thi.png", "Fleet Mission"),
]

for filepath, description in test_files:
    logger.info(f"\n{'='*50}")
    logger.info(f"Testing {description}: {filepath}")
    
    # Read image
    img = cv2.imread(filepath)
    if img is None:
        logger.warning(f"Failed to read {filepath}")
        continue
    
    height, width = img.shape[:2]
    logger.info(f"Image size: {width}x{height}")
    
    # Test small regions to avoid timeout
    # Top center region
    top_region = img[20:100, width//3:2*width//3]
    result = ocr.ocr(top_region)
    if result:
        logger.info(f"Top region text: '{result}'")
    
    # For dorm, test specific counter area
    if "dorm" in description.lower() or "doys" in filepath.lower():
        # Bottom left area where counters usually are
        counter_region = img[height-100:height-50, 50:350]
        cv2.imwrite("test_dorm_counter.png", counter_region)
        result = ocr.ocr(counter_region)
        if result:
            logger.info(f"Counter region text: '{result}'")
            if "/" in result:
                logger.info("  -> Contains counter format!")

logger.info("\n=== Test Complete ===")