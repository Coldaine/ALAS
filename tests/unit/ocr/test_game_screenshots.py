#!/usr/bin/env python3
"""
Test OCR on actual game screenshots and rename them based on content
"""
import os
import cv2
import sys
sys.path.insert(0, 'C:\\_Development\\ALAS')

from module.logger import logger
from module.ocr.al_ocr import AlOcr

# Initialize OCR
ocr = AlOcr(name='azur_lane')

# List all files in sshots directory
sshots_dir = "sshots"
files = os.listdir(sshots_dir)

logger.info(f"Found {len(files)} files in {sshots_dir}")

for filename in files:
    filepath = os.path.join(sshots_dir, filename)
    
    # Skip if not an image
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
        continue
        
    logger.info(f"\nProcessing: {filename}")
    
    # Read image
    img = cv2.imread(filepath)
    if img is None:
        logger.warning(f"Failed to read {filename}")
        continue
    
    # Perform OCR
    text = ocr.ocr(img)
    
    if text:
        logger.info(f"OCR Result: '{text}'")
        
        # Create a descriptive name based on detected text
        # Clean up text for filename
        clean_text = text.replace('/', '_').replace('\\', '_').replace(':', '')
        clean_text = ''.join(c for c in clean_text if c.isalnum() or c in ' _-')
        clean_text = clean_text.strip()[:50]  # Limit length
        
        if clean_text:
            # Get file extension
            ext = os.path.splitext(filename)[1]
            new_name = f"{clean_text}{ext}"
            new_path = os.path.join(sshots_dir, new_name)
            
            # Don't overwrite if file exists
            if not os.path.exists(new_path):
                logger.info(f"Renaming to: {new_name}")
                os.rename(filepath, new_path)
            else:
                logger.info(f"File already exists: {new_name}")
    else:
        logger.info("No text detected")

logger.info("\nScreenshot processing complete!")