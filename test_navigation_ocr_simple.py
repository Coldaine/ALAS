#!/usr/bin/env python
"""
Simplified closed-loop navigation test for ALAS
Uses direct ALAS instance to navigate and test OCR
"""
import sys
import os
import time
import json
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path

# Add ALAS to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import ALAS
from alas import AzurLaneAutoScript
from module.logger import logger
from module.ocr.ocr import OCR_MODEL


class SimpleNavigationTest:
    """Simplified navigation test using ALAS instance"""
    
    def __init__(self):
        """Initialize test"""
        # Create output directory
        self.output_dir = Path(f"test_navigation_ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.output_dir.mkdir(exist_ok=True)
        
        # Test results
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'screens_tested': [],
            'ocr_results': {},
            'screenshots': {},
            'errors': []
        }
        
        logger.info(f"Test output directory: {self.output_dir}")
    
    def save_screenshot(self, alas, name):
        """Save current screenshot"""
        try:
            image = alas.device.image
            if image is None:
                alas.device.screenshot()
                image = alas.device.image
            
            filename = f"{name}_{datetime.now().strftime('%H%M%S')}.png"
            filepath = self.output_dir / filename
            cv2.imwrite(str(filepath), image)
            
            self.results['screenshots'][name] = str(filepath)
            logger.info(f"Saved screenshot: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save screenshot {name}: {e}")
            self.results['errors'].append(f"screenshot_{name}: {e}")
            return None
    
    def test_ocr_on_image(self, image, screen_name):
        """Run OCR on an image"""
        logger.info(f"Running OCR on {screen_name}")
        
        try:
            start_time = time.time()
            result = OCR_MODEL.ocr(image, cls=True)
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
                                    'text': str(text),
                                    'confidence': float(confidence)
                                })
            
            self.results['ocr_results'][screen_name] = {
                'success': True,
                'text_count': len(text_found),
                'texts': text_found[:20],  # Limit to first 20
                'elapsed_ms': elapsed * 1000
            }
            
            logger.info(f"OCR found {len(text_found)} texts in {elapsed*1000:.1f}ms")
            return True
            
        except Exception as e:
            logger.error(f"OCR failed on {screen_name}: {e}")
            self.results['ocr_results'][screen_name] = {
                'success': False,
                'error': str(e)
            }
            self.results['errors'].append(f"ocr_{screen_name}: {e}")
            return False
    
    def test_screen_navigation(self, alas, screen_name, navigation_func):
        """Test navigation to a specific screen"""
        logger.hr(f"Testing {screen_name}")
        
        try:
            # Navigate to screen
            start_time = time.time()
            navigation_func()
            nav_time = (time.time() - start_time) * 1000
            
            logger.info(f"Navigation took {nav_time:.1f}ms")
            time.sleep(2)  # Wait for screen to stabilize
            
            # Take screenshot
            alas.device.screenshot()
            self.save_screenshot(alas, f"{screen_name}_arrived")
            
            # Run OCR
            self.test_ocr_on_image(alas.device.image, screen_name)
            
            self.results['screens_tested'].append({
                'name': screen_name,
                'success': True,
                'navigation_ms': nav_time
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to test {screen_name}: {e}")
            self.results['screens_tested'].append({
                'name': screen_name,
                'success': False,
                'error': str(e)
            })
            self.results['errors'].append(f"navigation_{screen_name}: {e}")
            self.save_screenshot(alas, f"{screen_name}_error")
            return False
    
    def run_tests(self):
        """Run all navigation tests"""
        logger.hr("Starting Navigation OCR Tests")
        
        # Initialize ALAS
        try:
            logger.info("Initializing ALAS...")
            alas = AzurLaneAutoScript(config_file='config/alas.json')
            alas.device.screenshot()
            logger.info("ALAS initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ALAS: {e}")
            self.results['errors'].append(f"init_alas: {e}")
            return False
        
        # Save initial screenshot
        self.save_screenshot(alas, "initial_state")
        
        # Test main menu OCR first
        logger.hr("Testing main menu")
        self.test_ocr_on_image(alas.device.image, "main_menu")
        
        # Define test sequences
        test_sequences = [
            # Research test
            {
                'name': 'research',
                'steps': [
                    ('research_menu', lambda: alas.ui_goto(alas.ui.page_reshmenu)),
                    ('research_lab', lambda: alas.ui_goto(alas.ui.page_research)),
                    ('back_to_main_1', lambda: alas.ui_goto_main()),
                ]
            },
            # Dorm test
            {
                'name': 'dorm',
                'steps': [
                    ('dorm_menu', lambda: alas.ui_goto(alas.ui.page_dormmenu)),
                    ('dorm_room', lambda: alas.ui_goto(alas.ui.page_dorm)),
                    ('back_to_main_2', lambda: alas.ui_goto_main()),
                ]
            }
        ]
        
        # Run test sequences
        for sequence in test_sequences:
            logger.hr(f"Running {sequence['name']} sequence")
            
            for step_name, step_func in sequence['steps']:
                if not self.test_screen_navigation(alas, step_name, step_func):
                    logger.warning(f"Failed at step {step_name}, continuing...")
                time.sleep(1)  # Wait between steps
        
        # Final screenshot
        self.save_screenshot(alas, "final_state")
        
        # Save results
        self.save_results()
        return True
    
    def save_results(self):
        """Save test results"""
        # Save JSON results
        results_file = self.output_dir / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Generate markdown report
        report_file = self.output_dir / "test_report.md"
        with open(report_file, 'w') as f:
            f.write("# Navigation OCR Test Report\n\n")
            f.write(f"**Timestamp**: {self.results['timestamp']}\n\n")
            
            # Navigation summary
            f.write("## Navigation Summary\n\n")
            f.write("| Screen | Success | Time (ms) |\n")
            f.write("|--------|---------|----------|\n")
            
            for screen in self.results['screens_tested']:
                success = "✅" if screen['success'] else "❌"
                time_ms = screen.get('navigation_ms', '-')
                if isinstance(time_ms, (int, float)):
                    time_ms = f"{time_ms:.1f}"
                f.write(f"| {screen['name']} | {success} | {time_ms} |\n")
            
            # OCR results
            f.write("\n## OCR Results\n\n")
            
            for screen_name, ocr_data in self.results['ocr_results'].items():
                f.write(f"### {screen_name}\n\n")
                
                if ocr_data['success']:
                    f.write(f"- **Status**: ✅ Success\n")
                    f.write(f"- **Texts found**: {ocr_data['text_count']}\n")
                    f.write(f"- **Time**: {ocr_data['elapsed_ms']:.1f}ms\n\n")
                    
                    if ocr_data.get('texts'):
                        f.write("**Sample texts** (confidence):\n\n")
                        for text_item in ocr_data['texts'][:10]:
                            text = text_item['text']
                            conf = text_item['confidence']
                            f.write(f"- `{text}` ({conf:.3f})\n")
                else:
                    f.write(f"- **Status**: ❌ Failed\n")
                    f.write(f"- **Error**: {ocr_data.get('error', 'Unknown')}\n\n")
            
            # Errors
            if self.results['errors']:
                f.write("\n## Errors\n\n")
                for error in self.results['errors']:
                    f.write(f"- {error}\n")
            
            # Screenshots
            f.write("\n## Screenshots\n\n")
            for name, path in self.results['screenshots'].items():
                filename = os.path.basename(path)
                f.write(f"- **{name}**: `{filename}`\n")
        
        logger.info(f"Results saved to: {self.output_dir}")
        print(f"\nTest results saved to: {self.output_dir}")
        print(f"- JSON results: {results_file}")
        print(f"- Markdown report: {report_file}")


def main():
    """Main test runner"""
    print("=" * 80)
    print("ALAS Navigation OCR Test (Simplified)")
    print("=" * 80)
    print("This test will navigate through screens and test OCR functionality.")
    print("IMPORTANT: Make sure the game is on the MAIN MENU!")
    print("=" * 80)
    
    # Check config
    if not os.path.exists('config/alas.json'):
        print("ERROR: config/alas.json not found!")
        return 1
    
    print("\nStarting test in 3 seconds...")
    time.sleep(3)
    
    try:
        test = SimpleNavigationTest()
        success = test.run_tests()
        
        if success:
            print("\nTest completed successfully!")
            return 0
        else:
            print("\nTest failed! Check the output directory for details.")
            return 1
            
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())