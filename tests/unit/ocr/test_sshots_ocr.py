#!/usr/bin/env python3
"""
Test OCR on specific areas of screenshots in sshots folder
"""
import os
import cv2
import sys
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.logger import logger
from module.ocr.ocr import Ocr, DigitCounter
from module.ocr.al_ocr import AlOcr

logger.info("=== Testing OCR on Screenshots ===")

# List files in sshots
sshots_dir = "sshots"
files = [f for f in os.listdir(sshots_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
logger.info(f"Found {len(files)} image files")

for filename in files:
    filepath = os.path.join(sshots_dir, filename)
    logger.info(f"\n{'='*50}")
    logger.info(f"Testing: {filename}")
    
    img = cv2.imread(filepath)
    if img is None:
        logger.warning(f"Failed to read {filename}")
        continue
    
    height, width = img.shape[:2]
    logger.info(f"Image size: {width}x{height}")
    
    # Test specific regions based on common UI elements
    test_regions = [
        # Top area - usually has titles/headers
        ("Top Header", (int(width*0.3), 10, int(width*0.7), 80)),
        # Center area - main content
        ("Center Content", (int(width*0.2), int(height*0.4), int(width*0.8), int(height*0.6))),
        # Bottom area - often has buttons/counters
        ("Bottom Area", (int(width*0.2), int(height*0.8), int(width*0.8), int(height*0.95))),
    ]
    
    # If it's the Dorm screenshot, test specific counter areas
    if "dorm" in filename.lower():
        test_regions = [
            ("Comfort Level", (1200, 40, 1400, 100)),
            ("Train Counter", (240, 820, 340, 860)),
            ("Food Storage", (100, 820, 200, 860)),
        ]
    
    for region_name, coords in test_regions:
        x1, y1, x2, y2 = coords
        
        # Ensure coordinates are within image bounds
        x1 = max(0, min(x1, width-1))
        x2 = max(0, min(x2, width-1))
        y1 = max(0, min(y1, height-1))
        y2 = max(0, min(y2, height-1))
        
        if x2 <= x1 or y2 <= y1:
            continue
            
        crop = img[y1:y2, x1:x2]
        
        # Try OCR
        ocr = Ocr(coords, name=region_name)
        result = ocr.ocr(crop, direct_ocr=True)
        
        if result:
            logger.info(f"  {region_name}: '{result}'")
        
        # If it looks like a counter, try DigitCounter
        if "counter" in region_name.lower() or "/" in str(result):
            counter = DigitCounter(coords, name=f"{region_name}_Counter")
            counter_result = counter.ocr(crop, direct_ocr=True)
            if counter_result != (0, 0, 0):
                logger.info(f"    Counter parsed: {counter_result}")

logger.info(f"\n{'='*50}")
logger.info("OCR testing complete!")