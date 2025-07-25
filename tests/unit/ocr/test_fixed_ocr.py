#!/usr/bin/env python3
"""
Test the fixed OCR implementation
"""
import sys
import cv2
import numpy as np
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.logger import logger

# Create test image
img = np.ones((50, 200, 3), dtype=np.uint8) * 255
cv2.putText(img, "TEST 123", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

logger.info("Testing fixed OCR...")

# Import after creating test image to avoid initialization issues
from module.ocr.ocr import OCR_MODEL

# Test the OCR
result = OCR_MODEL.ocr(img)
logger.info(f"OCR Result: {result}")

# Test with ALAS OCR wrapper
from module.ocr.ocr import Ocr

ocr = Ocr((0, 0, 200, 50), name="TestOCR")
text_result = ocr.ocr(img, direct_ocr=True)
logger.info(f"ALAS Ocr result: '{text_result}'")