#!/usr/bin/env python3
"""
Test OCR on the Research Academy screen
"""
import sys
import cv2
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.logger import logger
from module.ocr.ocr import Ocr, OCR_MODEL

# Load the research screen
img = cv2.imread("log/ocr_debug/ocr_6.png")
logger.info(f"Image shape: {img.shape}")

# Test direct OCR on a timer area
# The timer "02:00:00" appears to be around (167, 548)
timer_area = (100, 520, 250, 570)
x1, y1, x2, y2 = timer_area
timer_crop = img[y1:y2, x1:x2]
cv2.imwrite("test_timer_crop.png", timer_crop)

# Test with OCR
ocr = Ocr(timer_area, name="Timer")
result = ocr.ocr(timer_crop, direct_ocr=True)
logger.info(f"Timer OCR (no preprocessing): '{result}'")

# Test with preprocessing
result2 = ocr.ocr(timer_crop, direct_ocr=False)
logger.info(f"Timer OCR (with preprocessing): '{result2}'")

# Save preprocessed version
preprocessed = ocr.pre_process(timer_crop)
cv2.imwrite("test_timer_preprocessed.png", preprocessed)

# Test on the project name "Q-289-MI"
project_area = (70, 270, 230, 330)
x1, y1, x2, y2 = project_area
project_crop = img[y1:y2, x1:x2]
cv2.imwrite("test_project_crop.png", project_crop)

ocr2 = Ocr(project_area, name="Project")
result3 = ocr2.ocr(project_crop, direct_ocr=True)
logger.info(f"Project name OCR: '{result3}'")