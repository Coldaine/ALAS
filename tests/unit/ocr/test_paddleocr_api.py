#!/usr/bin/env python3
"""
Test script to document PaddleOCR API methods and capabilities
"""
import numpy as np
from paddleocr import PaddleOCR
import cv2
import os

# Initialize PaddleOCR with correct parameters
ocr = PaddleOCR(lang='en')

print("=== PaddleOCR API Documentation ===\n")

# Document available methods
print("Available PaddleOCR methods:")
methods = [method for method in dir(ocr) if not method.startswith('_')]
for method in sorted(methods):
    print(f"  - {method}")

print("\n=== Testing PaddleOCR with sample images ===\n")

# Test with screenshots
test_images = [
    "sshots/guild_mission_complete.png",
    "sshots/depot_items_view.png",
    "sshots/research_lab_projects.png"
]

for img_path in test_images:
    if os.path.exists(img_path):
        print(f"\nTesting: {img_path}")
        
        # Read image
        img = cv2.imread(img_path)
        
        # Method 1: Direct OCR (full image)
        print("  Full image OCR:")
        result = ocr.ocr(img, cls=True)
        
        if result and result[0]:
            for line in result[0][:3]:  # Show first 3 detections
                box, (text, confidence) = line
                print(f"    Text: '{text}' (confidence: {confidence:.3f})")
        else:
            print("    No text detected")
        
        # Method 2: Test with cropped region
        print("  Cropped region OCR (top-right corner):")
        h, w = img.shape[:2]
        crop = img[0:100, w-200:w]  # Top-right corner
        
        result_crop = ocr.ocr(crop, cls=True)
        if result_crop and result_crop[0]:
            for line in result_crop[0]:
                box, (text, confidence) = line
                print(f"    Text: '{text}' (confidence: {confidence:.3f})")
        else:
            print("    No text detected in crop")

print("\n=== PaddleOCR Output Format ===")
print("""
ocr.ocr() returns:
- List of results per image [result_image1, result_image2, ...]
- Each result_image is either:
  - None (no text detected)
  - List of detections [[box, (text, confidence)], ...]
  - box: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
  - text: detected string
  - confidence: float 0-1
""")

# Test batch processing
print("\n=== Batch Processing Test ===")
if len(test_images) >= 2:
    images = []
    for path in test_images[:2]:
        if os.path.exists(path):
            images.append(cv2.imread(path))
    
    if images:
        print(f"Processing {len(images)} images in batch...")
        batch_results = ocr.ocr(images, cls=True)
        print(f"Batch results: {len(batch_results)} results returned")
        for i, result in enumerate(batch_results):
            text_count = len(result) if result else 0
            print(f"  Image {i}: {text_count} text regions detected")