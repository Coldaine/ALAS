#!/usr/bin/env python3
"""
Simple test script to verify OCR functionality
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import sys

# Add module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from module.ocr.models import OCR_MODEL
from module.logger import logger


def create_test_image(text="TEST 123", width=200, height=50):
    """Create a simple test image with text"""
    # Create white image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a basic font
    try:
        # Try to use Arial if available
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        # Fall back to default font
        font = ImageFont.load_default()
    
    # Draw black text
    draw.text((10, 10), text, fill='black', font=font)
    
    # Convert to numpy array
    return np.array(img)


def test_ocr_models():
    """Test each OCR model"""
    print("="*60)
    print("Testing OCR Models")
    print("="*60)
    
    # Create test images
    test_cases = [
        ("HELLO WORLD", "Basic English text"),
        ("12345", "Numbers only"),
        ("AZUR LANE", "Game specific text"),
        ("10:30:45", "Time format"),
        ("STAGE 3-4", "Stage format"),
    ]
    
    # Test each model
    models_to_test = [
        ("azur_lane", OCR_MODEL.azur_lane),
        ("cnocr", OCR_MODEL.cnocr),
    ]
    
    for model_name, model in models_to_test:
        print(f"\n--- Testing {model_name} model ---")
        
        for text, description in test_cases:
            # Create test image
            img = create_test_image(text)
            
            # Run OCR
            try:
                result = model.ocr(img)
                status = "[OK]" if result else "[EMPTY]"
                print(f"{status} {description}: '{text}' -> '{result}'")
            except Exception as e:
                print(f"[ERROR] {description}: {e}")
    
    # Test single line methods
    print("\n--- Testing single line methods ---")
    images = [create_test_image(text) for text, _ in test_cases[:3]]
    
    try:
        results = OCR_MODEL.azur_lane.ocr_for_single_lines(images)
        print(f"ocr_for_single_lines: {results}")
    except Exception as e:
        print(f"Error in ocr_for_single_lines: {e}")
    
    try:
        results = OCR_MODEL.azur_lane.atomic_ocr_for_single_lines(images, alphabet="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        print(f"atomic_ocr_for_single_lines: {[[''.join(chars) for chars in result] for result in results]}")
    except Exception as e:
        print(f"Error in atomic_ocr_for_single_lines: {e}")


def test_ocr_backend_availability():
    """Check if OCR backend is available"""
    print("\n--- Checking OCR backend availability ---")
    
    try:
        from module.ocr.ocr import OCR_MODEL
        backend_name = type(OCR_MODEL).__name__
        print(f"[OK] OCR backend loaded: {backend_name}")
        
        if hasattr(OCR_MODEL, 'name'):
            print(f"[INFO] Backend details: {OCR_MODEL.name}")
            
    except Exception as e:
        print(f"[ERROR] OCR backend not available: {e}")
        print("\nPlease install OCR dependencies:")
        print("1. poetry add paddleocr  # Recommended")
        print("2. poetry add easyocr    # Fallback")
        return False
    
    return True


if __name__ == "__main__":
    print("="*60)
    print("ALAS OCR System Test")
    print("="*60)
    
    # Test OCR backend availability first
    if test_ocr_backend_availability():
        # Run OCR tests
        test_ocr_models()
    else:
        print("\nSkipping OCR tests - OCR backend not available")