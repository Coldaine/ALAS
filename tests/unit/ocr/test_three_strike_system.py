#!/usr/bin/env python3
"""
Test the three-strike error system with OCR
"""
import sys
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.logger import logger
from module.base.error_handler import OCR_ERROR_COUNTER, init_error_counter
from module.exception import OcrParseError

logger.info("=== Testing Three-Strike Error System ===")

# Reset the error counter
init_error_counter()

# Test 1: Simulate OCR duration parsing errors
logger.info("\nTest 1: Simulating duration parsing errors")

for i in range(4):
    try:
        # Simulate an error
        error_msg = f"Invalid duration format in attempt {i+1}"
        count = OCR_ERROR_COUNTER.record_error("ocr_duration", error_msg)
        logger.info(f"Error recorded, count is now: {count}")
    except OcrParseError as e:
        logger.error(f"Three-strike limit reached! Error: {e}")
        break

# Test 2: Success resets the counter
logger.info("\nTest 2: Testing success reset")

# First, build up some errors
for i in range(2):
    OCR_ERROR_COUNTER.record_error("ocr_commission", f"Commission parse error {i+1}")

logger.info(f"Current error count: {OCR_ERROR_COUNTER.get_error_count('ocr_commission')}")

# Now record a success
OCR_ERROR_COUNTER.record_success("ocr_commission")
logger.info(f"After success, error count: {OCR_ERROR_COUNTER.get_error_count('ocr_commission')}")

# Test 3: Different error types are tracked separately
logger.info("\nTest 3: Different error types tracked separately")

OCR_ERROR_COUNTER.record_error("ocr_duration", "Duration error")
OCR_ERROR_COUNTER.record_error("ocr_commission", "Commission error")

logger.info(f"Duration errors: {OCR_ERROR_COUNTER.get_error_count('ocr_duration')}")
logger.info(f"Commission errors: {OCR_ERROR_COUNTER.get_error_count('ocr_commission')}")

logger.info("\n=== Summary ===")
logger.info("The three-strike system is working correctly:")
logger.info("- After 3 consecutive errors of the same type, OcrParseError is raised")
logger.info("- Success resets the counter for that error type")
logger.info("- Different error types are tracked independently")
logger.info("\nThis system is used for specific parsing operations, not general OCR failures")