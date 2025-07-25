#!/usr/bin/env python3
"""
Test ALAS OCR system after PaddleOCR 3.x fix
"""
import sys
import cv2
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.logger import logger
from module.ocr.ocr import Ocr, DigitCounter

logger.info("=== Testing ALAS OCR with PaddleOCR 3.x Fix ===")

# Test 1: Simple text image
test_img = cv2.imread("test_paddle_fix.png")
if test_img is not None:
    logger.info("\nTest 1: Simple text image")
    ocr = Ocr((0, 0, 300, 100), name="TestOCR")
    result = ocr.ocr(test_img)
    logger.info(f"Result: '{result}'")

# Test 2: Dorm screenshot with counters
dorm_img = cv2.imread("sshots/Dorm.bmp")
if dorm_img is not None:
    logger.info("\nTest 2: Dorm screenshot")
    
    # Test train counter area
    train_area = (250, 810, 370, 870)
    train_counter = DigitCounter(train_area, name="TrainCounter")
    x1, y1, x2, y2 = train_area
    train_crop = dorm_img[y1:y2, x1:x2]
    
    logger.info("Testing DigitCounter on train area...")
    result = train_counter.ocr(train_crop, direct_ocr=True)
    logger.info(f"Train counter result: {result}")
    
    # Test if unpacking works
    try:
        current, _, total = result
        logger.info(f"Unpacked values: current={current}, total={total}")
    except Exception as e:
        logger.error(f"Failed to unpack: {e}")

# Test 3: Direct OCR_MODEL access (as used by AlOcr)
logger.info("\nTest 3: Direct OCR_MODEL access")
from module.ocr.ocr import OCR_MODEL

test_result = OCR_MODEL.ocr([test_img], cls=True)
logger.info(f"OCR_MODEL type: {type(OCR_MODEL)}")
logger.info(f"Direct OCR_MODEL result: {test_result}")

# Test 4: AlOcr interface
logger.info("\nTest 4: AlOcr interface")
from module.ocr.al_ocr import AlOcr

al_ocr = AlOcr(name='azur_lane')
if test_img is not None:
    text = al_ocr.ocr(test_img)
    logger.info(f"AlOcr result: '{text}'")

logger.info("\n=== OCR Testing Complete ===")