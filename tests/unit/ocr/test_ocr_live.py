#!/usr/bin/env python3
"""
Test OCR on a live screenshot from the emulator
"""
import sys
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.logger import logger
from module.device.device import Device
from module.ocr.ocr import Ocr
from module.config.config import Config
import cv2

# Initialize config and device
config = Config('alas')
device = Device(config=config)

logger.info("Taking screenshot from emulator...")
screenshot = device.screenshot()

# Save screenshot for inspection
cv2.imwrite('test_live_screenshot.png', screenshot)
logger.info(f"Screenshot saved. Shape: {screenshot.shape}")

# Test OCR on different areas
test_areas = [
    ("Top area", (100, 50, 400, 100)),
    ("Center", (500, 300, 800, 400)),
    ("Bottom", (100, 600, 400, 700)),
]

for name, area in test_areas:
    ocr = Ocr(area, name=name)
    x1, y1, x2, y2 = area
    crop = screenshot[y1:y2, x1:x2]
    
    # Save crop
    cv2.imwrite(f'test_crop_{name.replace(" ", "_")}.png', crop)
    
    # Test OCR
    result = ocr.ocr(crop, direct_ocr=True)
    logger.info(f"{name}: '{result}'")