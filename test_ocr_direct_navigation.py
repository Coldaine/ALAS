#!/usr/bin/env python
"""
Direct navigation and OCR test using ALAS components
Tests OCR on different screens by direct module usage
"""
import sys
import os
import time
import json
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

# Add ALAS to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from module.device.connection import Connection
from module.device.device import Device
from module.config.config import AzurLaneConfig
from module.logger import logger
from module.base.timer import Timer
from module.base.utils import *

# Import OCR
from module.ocr.ocr import OCR_MODEL

# Import specific UI elements and pages
from module.ui.assets import *
from module.ui.page import *
from module.dorm.assets import *
from module.research.assets import *


class DirectNavigationOCRTest:
    """Direct test of navigation and OCR without full ALAS initialization"""
    
    def __init__(self, serial="127.0.0.1:21503"):
        """Initialize test with direct device connection"""
        self.serial = serial
        self.output_dir = Path(f"test_nav_ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize device connection directly
        logger.info(f"Connecting to device: {serial}")
        self.device = self._init_device()
        
        # Test results
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'device': serial,
            'tests': [],
            'ocr_results': {},
            'screenshots': {},
            'errors': []
        }
    
    def _init_device(self):
        """Initialize device connection directly"""
        try:
            # Create minimal config
            config = Mock()
            config.Emulator_Serial = self.serial
            config.Emulator_ScreenshotMethod = "ADB"
            config.Emulator_ControlMethod = "ADB"
            config.Error_SaveError = False
            config.Error_ScreenshotLength = 1
            
            # Create connection
            device = Device(config=config)
            device.screenshot()
            
            logger.info("Device connected successfully")
            return device
            
        except Exception as e:
            logger.error(f"Failed to connect to device: {e}")
            raise
    
    def save_screenshot(self, name, image=None):
        """Save screenshot"""
        if image is None:
            image = self.device.image
        
        filename = f"{name}.png"
        filepath = self.output_dir / filename
        cv2.imwrite(str(filepath), image)
        
        self.results['screenshots'][name] = str(filepath)
        logger.info(f"Saved: {filename}")
        return filepath
    
    def click_button(self, button):
        """Click a button with retry"""
        logger.info(f"Clicking {button.name}")
        for _ in range(3):
            self.device.screenshot()
            if self.device.appear(button):
                self.device.click(button)
                time.sleep(1)
                return True
            time.sleep(0.5)
        return False
    
    def wait_for_screen(self, check_button, timeout=10):
        """Wait for a screen to appear"""
        logger.info(f"Waiting for {check_button.name}")
        timer = Timer(timeout)
        while not timer.reached():
            self.device.screenshot()
            if self.device.appear(check_button):
                logger.info(f"Found {check_button.name}")
                return True
            time.sleep(0.5)
        logger.warning(f"Timeout waiting for {check_button.name}")
        return False
    
    def test_ocr_on_current_screen(self, screen_name):
        """Test OCR on current screen"""
        logger.hr(f"OCR Test: {screen_name}")
        
        # Take screenshot
        self.device.screenshot()
        self.save_screenshot(f"{screen_name}_full")
        
        ocr_result = {
            'screen': screen_name,
            'timestamp': datetime.now().isoformat(),
            'texts': []
        }
        
        try:
            # Run OCR
            start_time = time.time()
            result = OCR_MODEL.ocr(self.device.image, cls=True)
            elapsed = time.time() - start_time
            
            # Parse results
            if result and isinstance(result, list):
                for line in result:
                    if line and isinstance(line, list):
                        for item in line:
                            if isinstance(item, tuple) and len(item) >= 2:
                                bbox = item[0]
                                text_data = item[1]
                                
                                if isinstance(text_data, tuple):
                                    text = text_data[0]
                                    confidence = text_data[1] if len(text_data) > 1 else 0
                                else:
                                    text = str(text_data)
                                    confidence = 0
                                
                                ocr_result['texts'].append({
                                    'text': text,
                                    'confidence': float(confidence),
                                    'bbox': bbox
                                })
            
            ocr_result['success'] = True
            ocr_result['elapsed_ms'] = elapsed * 1000
            ocr_result['text_count'] = len(ocr_result['texts'])
            
            logger.info(f"Found {len(ocr_result['texts'])} texts in {elapsed*1000:.1f}ms")
            
            # Save crops of interesting areas
            self._save_text_crops(screen_name, ocr_result['texts'][:5])
            
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            ocr_result['success'] = False
            ocr_result['error'] = str(e)
            self.results['errors'].append(f"ocr_{screen_name}: {e}")
        
        self.results['ocr_results'][screen_name] = ocr_result
        return ocr_result
    
    def _save_text_crops(self, screen_name, texts):
        """Save crops of detected text areas"""
        for i, text_data in enumerate(texts):
            try:
                bbox = text_data['bbox']
                if bbox and len(bbox) >= 4:
                    # Get bounding box
                    pts = np.array(bbox, dtype=np.int32)
                    x_min = max(0, pts[:, 0].min())
                    y_min = max(0, pts[:, 1].min())
                    x_max = min(self.device.image.shape[1], pts[:, 0].max())
                    y_max = min(self.device.image.shape[0], pts[:, 1].max())
                    
                    # Crop and save
                    crop = self.device.image[y_min:y_max, x_min:x_max]
                    if crop.size > 0:
                        crop_name = f"{screen_name}_text_{i}_{text_data['text'][:20]}"
                        # Clean filename
                        crop_name = "".join(c for c in crop_name if c.isalnum() or c in ('_', '-'))
                        self.save_screenshot(crop_name, crop)
            except Exception as e:
                logger.warning(f"Failed to save text crop: {e}")
    
    def navigate_to_research(self):
        """Navigate to research screen"""
        logger.hr("Navigating to Research")
        
        try:
            # From main menu, click research menu button
            if not self.click_button(MAIN_GOTO_RESHMENU):
                logger.warning("Failed to click research menu")
                return False
            
            # Wait for research menu
            if not self.wait_for_screen(RESHMENU_CHECK):
                return False
            
            self.save_screenshot("research_menu")
            time.sleep(1)
            
            # Click research lab
            if not self.click_button(RESHMENU_GOTO_RESEARCH):
                logger.warning("Failed to click research lab")
                return False
            
            # Wait for research screen
            if not self.wait_for_screen(RESEARCH_CHECK):
                return False
            
            logger.info("Arrived at research screen")
            return True
            
        except Exception as e:
            logger.error(f"Navigation to research failed: {e}")
            self.results['errors'].append(f"nav_research: {e}")
            return False
    
    def navigate_to_dorm(self):
        """Navigate to dorm screen"""
        logger.hr("Navigating to Dorm")
        
        try:
            # From main menu, click dorm menu button
            if not self.click_button(MAIN_GOTO_DORMMENU):
                logger.warning("Failed to click dorm menu")
                return False
            
            # Wait for dorm menu
            if not self.wait_for_screen(DORMMENU_CHECK):
                return False
            
            self.save_screenshot("dorm_menu")
            time.sleep(1)
            
            # Click dorm
            if not self.click_button(DORMMENU_GOTO_DORM):
                logger.warning("Failed to click dorm")
                return False
            
            # Wait for dorm screen
            if not self.wait_for_screen(DORM_CHECK, timeout=15):
                return False
            
            logger.info("Arrived at dorm screen")
            return True
            
        except Exception as e:
            logger.error(f"Navigation to dorm failed: {e}")
            self.results['errors'].append(f"nav_dorm: {e}")
            return False
    
    def return_to_main(self):
        """Return to main menu"""
        logger.hr("Returning to main")
        
        # Try multiple methods
        buttons_to_try = [GOTO_MAIN, GOTO_MAIN_WHITE, DORM_GOTO_MAIN]
        
        for button in buttons_to_try:
            if self.click_button(button):
                time.sleep(2)
                self.device.screenshot()
                
                # Check if we're at main
                if self.device.appear(MAIN_GOTO_FLEET) or self.device.appear(MAIN_GOTO_CAMPAIGN_WHITE):
                    logger.info("Returned to main menu")
                    return True
        
        logger.warning("Failed to return to main")
        return False
    
    def run_navigation_tests(self):
        """Run the navigation and OCR tests"""
        logger.hr("Starting Navigation OCR Tests")
        
        # Initial screenshot and OCR
        self.device.screenshot()
        self.save_screenshot("initial_state")
        self.test_ocr_on_current_screen("initial")
        
        # Test sequence
        test_sequence = [
            ("main_menu", lambda: True),  # Already there
            ("research", self.navigate_to_research),
            ("main_after_research", self.return_to_main),
            ("dorm", self.navigate_to_dorm),
            ("main_after_dorm", self.return_to_main),
        ]
        
        # Run tests
        for screen_name, nav_func in test_sequence:
            logger.hr(f"Test: {screen_name}")
            
            test_result = {
                'screen': screen_name,
                'timestamp': datetime.now().isoformat()
            }
            
            # Navigate
            start_time = time.time()
            nav_success = nav_func()
            nav_time = (time.time() - start_time) * 1000
            
            test_result['navigation_success'] = nav_success
            test_result['navigation_ms'] = nav_time
            
            if nav_success:
                time.sleep(2)  # Wait for screen to stabilize
                # Run OCR test
                ocr_result = self.test_ocr_on_current_screen(screen_name)
                test_result['ocr_success'] = ocr_result.get('success', False)
                test_result['text_count'] = ocr_result.get('text_count', 0)
            else:
                logger.warning(f"Navigation failed for {screen_name}")
                self.save_screenshot(f"{screen_name}_failed")
            
            self.results['tests'].append(test_result)
            time.sleep(1)
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save test results"""
        # JSON results
        results_file = self.output_dir / "results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # Markdown report
        report_file = self.output_dir / "report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Navigation OCR Test Report\n\n")
            f.write(f"**Date**: {self.results['timestamp']}\n")
            f.write(f"**Device**: {self.results['device']}\n\n")
            
            # Test summary
            f.write("## Test Summary\n\n")
            f.write("| Screen | Navigation | OCR | Texts Found |\n")
            f.write("|--------|------------|-----|-------------|\n")
            
            for test in self.results['tests']:
                nav = "✅" if test.get('navigation_success') else "❌"
                ocr = "✅" if test.get('ocr_success') else "❌"
                texts = test.get('text_count', '-')
                f.write(f"| {test['screen']} | {nav} | {ocr} | {texts} |\n")
            
            # OCR details
            f.write("\n## OCR Details\n\n")
            
            for screen_name, ocr_data in self.results['ocr_results'].items():
                f.write(f"### {screen_name}\n\n")
                
                if ocr_data.get('success'):
                    f.write(f"- **Status**: Success\n")
                    f.write(f"- **Time**: {ocr_data.get('elapsed_ms', 0):.1f}ms\n")
                    f.write(f"- **Texts**: {ocr_data.get('text_count', 0)}\n\n")
                    
                    if ocr_data.get('texts'):
                        f.write("**Sample texts**:\n\n")
                        for i, text in enumerate(ocr_data['texts'][:10]):
                            conf = text.get('confidence', 0)
                            f.write(f"{i+1}. `{text['text']}` (conf: {conf:.3f})\n")
                        
                        if len(ocr_data['texts']) > 10:
                            f.write(f"\n*...and {len(ocr_data['texts']) - 10} more*\n")
                else:
                    f.write(f"- **Status**: Failed\n")
                    f.write(f"- **Error**: {ocr_data.get('error', 'Unknown')}\n")
                
                f.write("\n")
            
            # Errors
            if self.results['errors']:
                f.write("## Errors\n\n")
                for error in self.results['errors']:
                    f.write(f"- {error}\n")
        
        logger.info(f"Results saved to: {self.output_dir}")
        print(f"\nTest complete! Results in: {self.output_dir}")


def main():
    """Main test runner"""
    print("=" * 80)
    print("Direct Navigation OCR Test")
    print("=" * 80)
    print("This test navigates through screens and tests OCR.")
    print("Make sure the game is on the MAIN MENU!")
    print("=" * 80)
    
    # Get device serial
    serial = "127.0.0.1:21503"  # Default MEmu
    if len(sys.argv) > 1:
        serial = sys.argv[1]
    
    print(f"\nDevice: {serial}")
    print("Starting in 3 seconds...")
    time.sleep(3)
    
    try:
        test = DirectNavigationOCRTest(serial)
        test.run_navigation_tests()
        return 0
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())