"""
Integration tests for the complete screenshot system.
Tests the full flow from device capture to image validation.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import numpy as np
import cv2
import time
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from collections import deque

from module.device.device import Device
from module.device.screenshot import Screenshot
from module.base.timer import Timer
from module.config.config import AzurLaneConfig


class MockEmulator:
    """Mock emulator that provides different screenshot scenarios"""
    
    def __init__(self):
        self.scenario = "normal"
        self.call_count = 0
        self.screenshots = {
            "normal": self._create_normal_screen(),
            "black": np.zeros((720, 1280, 3), dtype=np.uint8),
            "loading": self._create_loading_screen(),
            "combat": self._create_combat_screen(),
            "transition": self._create_transition_sequence()
        }
    
    def _create_normal_screen(self):
        """Create a normal main menu screen"""
        img = np.full((720, 1280, 3), (30, 40, 60), dtype=np.uint8)
        # Add UI elements
        cv2.rectangle(img, (1100, 650), (1250, 700), (231, 181, 90), -1)
        cv2.putText(img, "MAIN MENU", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        return img
    
    def _create_loading_screen(self):
        """Create a loading screen"""
        img = np.full((720, 1280, 3), (10, 10, 10), dtype=np.uint8)
        cv2.putText(img, "LOADING...", (500, 360), cv2.FONT_HERSHEY_SIMPLEX, 2, (100, 100, 100), 3)
        return img
    
    def _create_combat_screen(self):
        """Create a combat screen"""
        img = np.full((720, 1280, 3), (50, 100, 150), dtype=np.uint8)
        # Add combat UI
        cv2.rectangle(img, (1080, 70), (1230, 120), (255, 100, 100), -1)
        cv2.putText(img, "AUTO", (1120, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return img
    
    def _create_transition_sequence(self):
        """Create a sequence simulating screen transition"""
        sequence = []
        # Start with normal
        sequence.append(self.screenshots["normal"])
        # Fade to black
        for i in range(3):
            fade = self.screenshots["normal"] * (0.7 - i * 0.3)
            sequence.append(fade.astype(np.uint8))
        # Black screens
        sequence.extend([self.screenshots["black"]] * 2)
        # Fade in loading
        sequence.append(self.screenshots["loading"])
        # Final normal screen
        sequence.append(self.screenshots["normal"])
        return sequence
    
    def get_screenshot(self):
        """Get next screenshot based on scenario"""
        self.call_count += 1
        
        if self.scenario == "transition":
            sequence = self.screenshots["transition"]
            idx = min(self.call_count - 1, len(sequence) - 1)
            return sequence[idx].copy()
        else:
            return self.screenshots[self.scenario].copy()


class TestDeviceScreenshotIntegration:
    """Test Device class screenshot integration"""
    
    def setup_method(self):
        """Setup test device"""
        self.mock_emulator = MockEmulator()
        
        # Create mock config
        self.mock_config = Mock(spec=AzurLaneConfig)
        self.mock_config.Emulator_Serial = "test_device"
        self.mock_config.Emulator_ScreenshotMethod = "test_method"
        self.mock_config.Emulator_ScreenshotDedithering = False
        self.mock_config.Error_SaveError = True
        self.mock_config.Error_ScreenshotLength = 30
        self.mock_config.Optimization_ScreenshotInterval = 0.1
        
    def test_device_screenshot_normal_flow(self):
        """Test normal screenshot flow through Device"""
        with patch('module.device.device.Screenshot.__init__', return_value=None):
            device = Device()
            device.config = self.mock_config
            device.serial = "test_device"
            
            # Setup screenshot internals
            device._screenshot_interval = Mock()
            device.screenshot_deque = deque(maxlen=30)
            device.stuck_timer = Mock()
            device.stuck_timer.reached.return_value = False
            device.stuck_long_timer = Mock()
            device.stuck_long_timer.reached.return_value = False
            
            # Mock screenshot method
            device.screenshot_methods = {
                "test_method": lambda: self.mock_emulator.get_screenshot()
            }
            
            # Mock validation methods
            with patch.object(device, 'check_screen_size', return_value=True):
                with patch.object(device, '_handle_orientated_image', side_effect=lambda x: x):
                    with patch('module.base.utils.get_color', return_value=(30, 40, 60)):
                        # Call screenshot
                        result = device.screenshot()
            
            # Verify
            assert result.shape == (720, 1280, 3)
            assert np.mean(result) > 10  # Not black
    
    def test_device_stuck_detection(self):
        """Test Device stuck detection during screenshot"""
        with patch('module.device.device.Screenshot.__init__', return_value=None):
            device = Device()
            device.config = self.mock_config
            device.serial = "test_device"
            
            # Setup timers
            device.stuck_timer = Mock()
            device.stuck_timer.reached.return_value = True  # Simulate stuck
            device.stuck_long_timer = Mock()
            device.stuck_long_timer.reached.return_value = False
            
            # Mock parent screenshot
            with patch.object(Screenshot, 'screenshot', return_value=self.mock_emulator.get_screenshot()):
                with pytest.raises(Exception) as exc_info:
                    device.screenshot()
            
            assert "stuck" in str(exc_info.value).lower()
    
    def test_black_screen_recovery_flow(self):
        """Test full recovery flow for black screens"""
        with patch('module.device.device.Screenshot.__init__', return_value=None):
            device = Device()
            device.config = self.mock_config
            device.serial = "test_device"
            
            # Simulate black screen then recovery
            self.mock_emulator.scenario = "transition"
            
            device._screenshot_interval = Mock()
            device.screenshot_deque = deque(maxlen=30)
            device.stuck_timer = Mock()
            device.stuck_timer.reached.return_value = False
            device.stuck_long_timer = Mock()
            device.stuck_long_timer.reached.return_value = False
            
            attempts = []
            def track_screenshot():
                img = self.mock_emulator.get_screenshot()
                attempts.append(np.mean(img))
                return img
            
            device.screenshot_methods = {"test_method": track_screenshot}
            
            with patch.object(device, 'check_screen_size', return_value=True):
                with patch.object(device, '_handle_orientated_image', side_effect=lambda x: x):
                    with patch('module.base.utils.get_color') as mock_color:
                        # Return black color for black screens
                        mock_color.side_effect = lambda img, area: (0, 0, 0) if np.mean(img) < 1 else tuple(np.mean(img, axis=(0,1)).astype(int))
                        
                        with patch('time.sleep', Mock()):  # Skip sleep
                            result = device.screenshot()
            
            # Should have retried through black screens
            assert len(attempts) > 5  # Multiple attempts
            assert attempts[0] > 10  # Started normal
            assert min(attempts[1:5]) < 1  # Had black screens
            assert np.mean(result) > 10  # Ended with valid screen


class TestScreenshotPerformance:
    """Test screenshot performance characteristics"""
    
    def test_screenshot_timing(self):
        """Measure screenshot timing with different scenarios"""
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "test"
        screenshot_obj.config.Emulator_ScreenshotDedithering = True
        screenshot_obj.config.Error_SaveError = False
        screenshot_obj._screenshot_interval = Mock()
        
        timings = {
            "capture": [],
            "dedither": [],
            "validation": [],
            "total": []
        }
        
        def timed_capture():
            start = time.time()
            img = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
            timings["capture"].append(time.time() - start)
            return img
        
        # Mock components with timing
        screenshot_obj.screenshot_methods = {"test": timed_capture}
        
        original_denoise = cv2.fastNlMeansDenoising
        def timed_denoise(src, dst, **kwargs):
            start = time.time()
            # Simulate dedithering time
            time.sleep(0.05)  # 50ms
            timings["dedither"].append(time.time() - start)
        
        with patch.object(screenshot_obj, 'check_screen_size') as mock_size:
            with patch.object(screenshot_obj, 'check_screen_black') as mock_black:
                with patch.object(screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                    with patch('cv2.fastNlMeansDenoising', timed_denoise):
                        
                        def timed_validation():
                            start = time.time()
                            result = True
                            timings["validation"].append(time.time() - start)
                            return result
                        
                        mock_size.side_effect = timed_validation
                        mock_black.side_effect = timed_validation
                        
                        # Run screenshot
                        start_total = time.time()
                        screenshot_obj.screenshot()
                        timings["total"].append(time.time() - start_total)
        
        # Analyze timings
        assert len(timings["capture"]) == 1
        assert len(timings["dedither"]) == 1  # Only first attempt
        assert len(timings["validation"]) == 2  # size and black check
        
        # Dedithering should be significant portion
        assert timings["dedither"][0] > 0.04  # At least 40ms
        
        """
        PERFORMANCE ANALYSIS:
        - Capture: Variable (depends on method)
        - Dedithering: 40-60ms (only first attempt now)
        - Validation: <5ms typically
        - Total: Capture + 50ms (first) or Capture + 5ms (retry)
        """


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_screenshot_with_invalid_resolution(self):
        """Test handling of wrong resolution screenshots"""
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "test"
        screenshot_obj.config.Emulator_ScreenshotDedithering = False
        screenshot_obj.config.Error_SaveError = False
        screenshot_obj._screenshot_interval = Mock()
        screenshot_obj._screen_size_checked = False
        
        # Return wrong size image
        wrong_size = np.zeros((1080, 1920, 3), dtype=np.uint8)
        screenshot_obj.screenshot_methods = {"test": lambda: wrong_size}
        
        with patch.object(screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
            with patch('module.base.utils.image_size', return_value=(1920, 1080)):
                # Should raise RequestHumanTakeover
                with pytest.raises(Exception) as exc_info:
                    screenshot_obj.screenshot()
        
        assert "resolution" in str(exc_info.value).lower() or "1280x720" in str(exc_info.value)
    
    def test_screenshot_memory_leak_prevention(self):
        """Test that screenshot deque doesn't grow indefinitely"""
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "test"
        screenshot_obj.config.Emulator_ScreenshotDedithering = False
        screenshot_obj.config.Error_SaveError = True
        screenshot_obj.config.Error_ScreenshotLength = 10  # Small for testing
        screenshot_obj._screenshot_interval = Mock()
        
        # Generate many screenshots
        screenshot_obj.screenshot_methods = {
            "test": lambda: np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        }
        
        with patch.object(screenshot_obj, 'check_screen_size', return_value=True):
            with patch.object(screenshot_obj, 'check_screen_black', return_value=True):
                with patch.object(screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                    # Take many screenshots
                    for _ in range(50):
                        screenshot_obj.screenshot()
        
        # Deque should be limited
        assert len(screenshot_obj.screenshot_deque) <= 10
        
        """
        MEMORY MANAGEMENT:
        - Deque limited to Error_ScreenshotLength (default 30)
        - Old screenshots automatically removed
        - Prevents memory growth over time
        """


class TestMethodFallbackProposal:
    """Test proposed method fallback implementation"""
    
    def test_proposed_fallback_chain(self):
        """Test how method fallback should work"""
        # This is a PROPOSAL for how it should work
        
        class ScreenshotWithFallback(Screenshot):
            def screenshot(self):
                """Enhanced screenshot with method fallback"""
                self._screenshot_interval.wait()
                self._screenshot_interval.reset()
                
                # Method priority order
                method_chain = [
                    self.config.Emulator_ScreenshotMethod,
                    "uiautomator2",  # Cross-platform fallback
                    "ADB"  # Universal fallback
                ]
                
                for attempt in range(10):
                    # Try each method in the chain
                    for method_name in method_chain:
                        try:
                            method = self.screenshot_methods.get(method_name)
                            if not method:
                                continue
                                
                            self.image = method()
                            
                            # Skip dedithering on retries
                            if self.config.Emulator_ScreenshotDedithering and attempt == 0:
                                cv2.fastNlMeansDenoising(self.image, self.image, h=17, templateWindowSize=1, searchWindowSize=2)
                            
                            self.image = self._handle_orientated_image(self.image)
                            
                            if self.config.Error_SaveError:
                                self.screenshot_deque.append({"time": time.time(), "image": self.image})
                            
                            if self.check_screen_size() and self.check_screen_black():
                                return self.image
                            else:
                                break  # Try next attempt with same method first
                                
                        except Exception as e:
                            print(f"Method {method_name} failed: {e}")
                            continue  # Try next method
                    
                    # Exponential backoff
                    if attempt < 9:
                        wait_time = min(0.5 * (2 ** attempt), 5.0)
                        time.sleep(wait_time)
                
                return self.image
        
        """
        PROPOSED ENHANCEMENT:
        - Try primary method first
        - On exception, try fallback methods
        - Maintain retry count across all methods
        - Log which methods failed for debugging
        - Automatically discover working method
        """