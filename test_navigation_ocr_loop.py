#!/usr/bin/env python
"""
Closed-loop navigation test for ALAS
Navigates to problem screens (research, dorm, etc.), takes screenshots, runs OCR, and records results.
This script runs while ALAS is on main menu in the emulator.
"""
import sys
import os
import time
import json
import numpy as np
import cv2
from datetime import datetime
from pathlib import Path

# Add ALAS to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import ALAS modules
from module.device.device import Device
from module.device.screenshot import Screenshot
from module.config.config import AzurLaneConfig
from module.ui.ui import UI
from module.ui.page import page_main, page_research, page_dorm, page_reshmenu, page_dormmenu
from module.base.button import Button
from module.logger import logger

# Import OCR modules
from module.ocr.ocr import OCR_MODEL
from module.ocr.models import OCR_MODEL as OCR_FACTORY

# Import specific OCR instances used in problem areas
from module.dorm.dorm import OCR_FILL, OCR_SLOT
from module.research.research import OCR_DURATION


class NavigationOCRTest(UI):
    """Test navigation to problem screens and OCR functionality"""
    
    def __init__(self, config_path='config/alas.json'):
        """Initialize test with ALAS configuration"""
        # Load config
        self.config = AzurLaneConfig()
        self.config.load_json(config_path)
        
        # Initialize device connection
        self.device = Device(config=self.config)
        
        # Test results storage
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'serial': self.config.Emulator_Serial,
                'screenshot_method': self.config.Emulator_ScreenshotMethod,
            },
            'navigation': {},
            'ocr_results': {},
            'screenshots': {},
            'errors': []
        }
        
        # Create output directory
        self.output_dir = Path(f"test_navigation_ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"Test output directory: {self.output_dir}")
    
    def save_screenshot(self, name, image=None):
        """Save screenshot with timestamp"""
        if image is None:
            image = self.device.image
        
        filename = f"{name}_{datetime.now().strftime('%H%M%S')}.png"
        filepath = self.output_dir / filename
        cv2.imwrite(str(filepath), image)
        
        self.results['screenshots'][name] = str(filepath)
        logger.info(f"Saved screenshot: {filepath}")
        return filepath
    
    def test_ocr_on_current_screen(self, screen_name):
        """Run OCR tests on current screen"""
        logger.hr(f"Testing OCR on {screen_name}")
        
        # Take screenshot
        self.device.screenshot()
        self.save_screenshot(f"{screen_name}_full")
        
        ocr_results = {}
        
        # Test generic OCR on full screen
        try:
            logger.info("Running full screen OCR...")
            start_time = time.time()
            result = OCR_MODEL.ocr(self.device.image, cls=True)
            elapsed = time.time() - start_time
            
            # Parse results
            text_found = []
            if result and isinstance(result, list):
                for line in result:
                    if line and isinstance(line, list):
                        for item in line:
                            if isinstance(item, tuple) and len(item) >= 2:
                                text = item[1][0] if isinstance(item[1], tuple) else item[1]
                                confidence = item[1][1] if isinstance(item[1], tuple) and len(item[1]) > 1 else 0
                                text_found.append({
                                    'text': text,
                                    'confidence': float(confidence),
                                    'bbox': item[0] if len(item) > 0 else None
                                })
            
            ocr_results['full_screen'] = {
                'text_count': len(text_found),
                'texts': text_found,
                'elapsed_ms': elapsed * 1000
            }
            logger.info(f"Found {len(text_found)} text regions in {elapsed*1000:.1f}ms")
            
        except Exception as e:
            logger.error(f"Full screen OCR failed: {e}")
            ocr_results['full_screen'] = {'error': str(e)}
            self.results['errors'].append(f"{screen_name}_full_ocr: {e}")
        
        # Test specific OCR areas based on screen
        if screen_name == 'dorm':
            # Test dorm-specific OCR
            try:
                logger.info("Testing DORM FILL OCR...")
                # Get the area for OCR_FILL
                if hasattr(OCR_FILL, 'button'):
                    area = OCR_FILL.button.area
                    crop = self.device.image[area[1]:area[3], area[0]:area[2]]
                    self.save_screenshot(f"{screen_name}_fill_area", crop)
                    
                    # Run OCR on crop
                    fill_result = OCR_FILL.ocr(self.device.image)
                    ocr_results['dorm_fill'] = {
                        'result': fill_result,
                        'area': area
                    }
                    logger.info(f"DORM FILL result: {fill_result}")
                    
                # Test SLOT OCR
                logger.info("Testing DORM SLOT OCR...")
                slot_result = OCR_SLOT.ocr(self.device.image)
                ocr_results['dorm_slot'] = {
                    'result': slot_result,
                }
                logger.info(f"DORM SLOT result: {slot_result}")
                
            except Exception as e:
                logger.error(f"Dorm OCR failed: {e}")
                ocr_results['dorm_specific'] = {'error': str(e)}
                self.results['errors'].append(f"{screen_name}_dorm_ocr: {e}")
        
        elif screen_name == 'research':
            # Test research-specific OCR
            try:
                logger.info("Testing RESEARCH DURATION OCR...")
                duration_result = OCR_DURATION.ocr(self.device.image)
                ocr_results['research_duration'] = {
                    'result': duration_result,
                }
                logger.info(f"RESEARCH DURATION result: {duration_result}")
                
            except Exception as e:
                logger.error(f"Research OCR failed: {e}")
                ocr_results['research_specific'] = {'error': str(e)}
                self.results['errors'].append(f"{screen_name}_research_ocr: {e}")
        
        self.results['ocr_results'][screen_name] = ocr_results
        return ocr_results
    
    def navigate_and_test(self, destination_page, screen_name):
        """Navigate to a page and run OCR tests"""
        logger.hr(f"Navigating to {screen_name}")
        
        nav_start = time.time()
        try:
            # Navigate to destination
            self.ui_goto(destination_page)
            nav_elapsed = time.time() - nav_start
            
            self.results['navigation'][screen_name] = {
                'success': True,
                'elapsed_ms': nav_elapsed * 1000
            }
            logger.info(f"Navigation to {screen_name} successful in {nav_elapsed*1000:.1f}ms")
            
            # Wait for screen to stabilize
            time.sleep(1.0)
            
            # Run OCR tests
            self.test_ocr_on_current_screen(screen_name)
            
            # Take final screenshot
            self.save_screenshot(f"{screen_name}_final")
            
        except Exception as e:
            logger.error(f"Navigation to {screen_name} failed: {e}")
            self.results['navigation'][screen_name] = {
                'success': False,
                'error': str(e),
                'elapsed_ms': (time.time() - nav_start) * 1000
            }
            self.results['errors'].append(f"{screen_name}_navigation: {e}")
            self.save_screenshot(f"{screen_name}_error")
    
    def return_to_main(self):
        """Return to main menu"""
        logger.hr("Returning to main menu")
        try:
            self.ui_goto_main()
            logger.info("Returned to main menu")
            return True
        except Exception as e:
            logger.error(f"Failed to return to main: {e}")
            self.results['errors'].append(f"return_to_main: {e}")
            return False
    
    def run_test_loop(self):
        """Run the complete test loop"""
        logger.hr("Starting Navigation OCR Test Loop")
        
        # Verify we're on main menu
        logger.info("Verifying main menu...")
        self.device.screenshot()
        if not self.is_in_main():
            logger.error("Not on main menu! Please navigate to main menu before running test.")
            return False
        
        self.save_screenshot("main_menu_start")
        
        # Test sequence
        test_screens = [
            (page_reshmenu, 'research_menu'),
            (page_research, 'research'),
            # Return to main between tests
            (page_main, 'main_after_research'),
            (page_dormmenu, 'dorm_menu'),
            (page_dorm, 'dorm'),
            # Return to main
            (page_main, 'main_after_dorm'),
        ]
        
        # Run tests
        for destination, screen_name in test_screens:
            logger.hr(f"Test: {screen_name}")
            
            if destination == page_main:
                if not self.return_to_main():
                    logger.error("Failed to return to main, aborting test")
                    break
                self.save_screenshot(screen_name)
            else:
                self.navigate_and_test(destination, screen_name)
                time.sleep(1.0)  # Wait between navigations
        
        # Final return to main
        self.return_to_main()
        self.save_screenshot("main_menu_end")
        
        # Save results
        self.save_results()
        return True
    
    def save_results(self):
        """Save test results to JSON"""
        results_file = self.output_dir / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to: {results_file}")
        
        # Generate summary report
        self.generate_report()
    
    def generate_report(self):
        """Generate human-readable test report"""
        report_file = self.output_dir / "test_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# Navigation OCR Test Report\n\n")
            f.write(f"**Timestamp**: {self.results['timestamp']}\n")
            f.write(f"**Device**: {self.results['config']['serial']}\n")
            f.write(f"**Screenshot Method**: {self.results['config']['screenshot_method']}\n\n")
            
            f.write("## Navigation Results\n\n")
            f.write("| Screen | Success | Time (ms) | Error |\n")
            f.write("|--------|---------|-----------|-------|\n")
            
            for screen, result in self.results['navigation'].items():
                success = "✅" if result.get('success', False) else "❌"
                time_ms = f"{result.get('elapsed_ms', 0):.1f}"
                error = result.get('error', '-')
                f.write(f"| {screen} | {success} | {time_ms} | {error} |\n")
            
            f.write("\n## OCR Results\n\n")
            
            for screen, ocr_data in self.results['ocr_results'].items():
                f.write(f"### {screen}\n\n")
                
                # Full screen OCR
                if 'full_screen' in ocr_data:
                    full = ocr_data['full_screen']
                    if 'error' in full:
                        f.write(f"**Full Screen OCR**: ❌ Error - {full['error']}\n\n")
                    else:
                        f.write(f"**Full Screen OCR**: {full.get('text_count', 0)} texts found in {full.get('elapsed_ms', 0):.1f}ms\n\n")
                        
                        if full.get('texts'):
                            f.write("| Text | Confidence |\n")
                            f.write("|------|------------|\n")
                            for text_item in full['texts'][:10]:  # Show first 10
                                text = text_item.get('text', '')
                                conf = text_item.get('confidence', 0)
                                f.write(f"| {text} | {conf:.3f} |\n")
                            
                            if len(full['texts']) > 10:
                                f.write(f"\n*... and {len(full['texts']) - 10} more texts*\n")
                        f.write("\n")
                
                # Screen-specific OCR
                for key, value in ocr_data.items():
                    if key != 'full_screen':
                        f.write(f"**{key}**: {value.get('result', value)}\n")
                
                f.write("\n")
            
            if self.results['errors']:
                f.write("## Errors\n\n")
                for error in self.results['errors']:
                    f.write(f"- {error}\n")
            
            f.write("\n## Screenshots\n\n")
            for name, path in self.results['screenshots'].items():
                f.write(f"- **{name}**: {path}\n")
        
        logger.info(f"Report saved to: {report_file}")


def main():
    """Main test runner"""
    print("=" * 80)
    print("ALAS Navigation OCR Test")
    print("=" * 80)
    print("This test will navigate through problem screens and test OCR functionality.")
    print("IMPORTANT: Make sure ALAS is on the MAIN MENU before starting!")
    print("=" * 80)
    
    # Check if config exists
    config_path = 'config/alas.json'
    if not os.path.exists(config_path):
        print(f"ERROR: Config file not found at {config_path}")
        print("Please ensure ALAS is properly configured.")
        return 1
    
    try:
        # Create and run test
        test = NavigationOCRTest(config_path)
        
        print("\nStarting test in 3 seconds...")
        time.sleep(3)
        
        success = test.run_test_loop()
        
        if success:
            print(f"\nTest completed successfully!")
            print(f"Results saved to: {test.output_dir}")
            return 0
        else:
            print(f"\nTest failed! Check logs and results in: {test.output_dir}")
            return 1
            
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())