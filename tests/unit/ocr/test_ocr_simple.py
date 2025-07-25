#!/usr/bin/env python3
"""
Simple test script to verify OCR functionality without logger
"""
import numpy as np
from PIL import Image, ImageDraw
import os
import sys

# Add module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def create_test_image(text="TEST 123", width=200, height=50):
    """Create a simple test image with text"""
    # Create white image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw black text with default font
    draw.text((10, 10), text, fill='black')
    
    # Convert to numpy array
    return np.array(img)


def test_ocr_backend():
    """Test current OCR backend (PaddleOCR/EasyOCR)"""
    print("Testing OCR backend...")
    
    try:
        from module.ocr.ocr import OCR_MODEL
        
        # Create test image
        img = create_test_image("HELLO WORLD")
        
        # Try OCR with current backend
        result = OCR_MODEL.ocr([img], cls=True)
        print(f"OCR backend: {type(OCR_MODEL).__name__}")
        print(f"OCR result: {result}")
        
        return True
        
    except Exception as e:
        print(f"OCR backend error: {e}")
        return False


def test_ocr_module():
    """Test our OCR module"""
    print("\nTesting OCR module...")
    
    try:
        # Import directly to avoid logger issues
        from module.ocr.al_ocr import AlOcr
        
        # Create OCR instance
        ocr = AlOcr(name='azur_lane')
        
        # Create test image
        img = create_test_image("TEST 123")
        
        # Try OCR
        result = ocr.ocr(img)
        print(f"AlOcr result: '{result}'")
        
        # Test multiple images
        images = [
            create_test_image("HELLO"),
            create_test_image("WORLD"),
            create_test_image("12345")
        ]
        
        results = ocr.ocr_for_single_lines(images)
        print(f"Multiple OCR results: {results}")
        
    except Exception as e:
        print(f"OCR module error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("="*60)
    print("ALAS OCR System Test")
    print("="*60)
    
    # Test current OCR backend
    if test_ocr_backend():
        print("\n" + "="*40)
        # Test our module
        test_ocr_module()
    else:
        print("\nOCR backend not available.")
        print("Install OCR dependencies:")
        print("1. poetry add paddleocr  # Recommended")
        print("2. poetry add easyocr    # Fallback")