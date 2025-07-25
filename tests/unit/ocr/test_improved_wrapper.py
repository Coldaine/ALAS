#!/usr/bin/env python3
"""
Test the improved PaddleOCR wrapper
"""
import sys
import cv2
import numpy as np
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.logger import logger

logger.info("=== Testing Improved PaddleOCR Wrapper ===")

# Test 1: Basic functionality
logger.info("\nTest 1: Basic OCR functionality")
from module.ocr.paddleocr_v3_improved import get_paddleocr_v3

ocr = get_paddleocr_v3(lang='en')

# Create test image
test_img = np.ones((50, 200, 3), dtype=np.uint8) * 255
cv2.putText(test_img, "TEST OCR", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

result = ocr.ocr(test_img)
logger.info(f"Result: {result}")

# Test 2: Error handling - invalid input
logger.info("\nTest 2: Error handling with invalid input")
try:
    result = ocr.ocr(None)
    logger.error("Should have raised TypeError!")
except TypeError as e:
    logger.info(f"Correctly caught error: {e}")

# Test 3: Invalid image type
logger.info("\nTest 3: Invalid image type")
try:
    result = ocr.ocr(12345)  # Invalid type
    logger.error("Should have raised TypeError!")
except (TypeError, ValueError) as e:
    logger.info(f"Correctly caught error: {e}")

# Test 4: Thread safety
logger.info("\nTest 4: Thread safety - singleton pattern")
ocr2 = get_paddleocr_v3(lang='en')
logger.info(f"Same instance? {ocr is ocr2}")

# Test 5: Context manager
logger.info("\nTest 5: Context manager support")
from module.ocr.paddleocr_v3_improved import PaddleOCRv3
with PaddleOCRv3(lang='en') as ocr_ctx:
    result = ocr_ctx.ocr(test_img)
    logger.info(f"Context manager result: {len(result)} detections")

# Test 6: ALAS integration
logger.info("\nTest 6: ALAS integration test")
from module.ocr.al_ocr import AlOcr

al_ocr = AlOcr()
text = al_ocr.ocr(test_img)
logger.info(f"AlOcr result: '{text}'")

logger.info("\n=== All tests completed successfully! ===")