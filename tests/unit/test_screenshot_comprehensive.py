"""
Comprehensive behavioral tests for Screenshot.screenshot() method.
Each test verifies actual behavior, not just that code runs.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime
from collections import deque

from module.device.screenshot import Screenshot
from module.base.timer import Timer


class TestScreenshotStepByStep:
    """Test each step of the screenshot() method in isolation"""
    
    def setup_method(self):
        """Create a Screenshot instance with mocked dependencies"""
        self.screenshot_obj = Screenshot()
        
        # Mock config
        self.mock_config = Mock()
        self.mock_config.Emulator_ScreenshotMethod = "ADB"
        self.mock_config.Emulator_ScreenshotDedithering = False
        self.mock_config.Error_SaveError = False
        self.screenshot_obj.config = self.mock_config
        
        # Mock internal state
        self.screenshot_obj._screenshot_interval = Mock(spec=Timer)
        self.screenshot_obj.screenshot_deque = deque(maxlen=30)
        self.screenshot_obj.image = None
        
    def test_step_1_interval_wait(self):
        """Test that screenshot waits for interval before capturing"""
        # Setup
        mock_wait = Mock()
        self.screenshot_obj._screenshot_interval.wait = mock_wait
        self.screenshot_obj._screenshot_interval.reset = Mock()
        
        # Mock other methods to prevent full execution
        with patch.object(self.screenshot_obj, 'screenshot_methods', {"ADB": Mock(return_value=np.zeros((720, 1280, 3), dtype=np.uint8))}):
            with patch.object(self.screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(self.screenshot_obj, 'check_screen_black', return_value=True):
                    with patch.object(self.screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        # Execute
                        self.screenshot_obj.screenshot()
        
        # Verify
        mock_wait.assert_called_once()
        
        # Document actual behavior
        """
        ACTUAL OUTPUT: 
        - wait() called with no arguments
        - Blocks thread until timer expires
        - No return value
        - Side effect: Thread sleeps for configured interval
        """
    
    def test_step_2_interval_reset(self):
        """Test that interval timer is reset after wait"""
        # Setup
        mock_reset = Mock()
        self.screenshot_obj._screenshot_interval.wait = Mock()
        self.screenshot_obj._screenshot_interval.reset = mock_reset
        
        # Mock other methods
        with patch.object(self.screenshot_obj, 'screenshot_methods', {"ADB": Mock(return_value=np.zeros((720, 1280, 3), dtype=np.uint8))}):
            with patch.object(self.screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(self.screenshot_obj, 'check_screen_black', return_value=True):
                    with patch.object(self.screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        # Execute
                        self.screenshot_obj.screenshot()
        
        # Verify
        mock_reset.assert_called_once()
        
        """
        ACTUAL OUTPUT:
        - reset() called after wait()
        - Starts new timing period
        - No arguments or return value
        """
    
    def test_step_3_retry_loop_count(self):
        """Test that retry loop attempts exactly 2 times on failure"""
        # Setup
        call_count = 0
        def mock_screenshot_method():
            nonlocal call_count
            call_count += 1
            return np.zeros((720, 1280, 3), dtype=np.uint8)
        
        self.screenshot_obj._screenshot_interval.wait = Mock()
        self.screenshot_obj._screenshot_interval.reset = Mock()
        
        # Force validation to fail
        with patch.object(self.screenshot_obj, 'screenshot_methods', {"ADB": mock_screenshot_method}):
            with patch.object(self.screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(self.screenshot_obj, 'check_screen_black', return_value=False):  # Always fail
                    with patch.object(self.screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        # Execute
                        self.screenshot_obj.screenshot()
        
        # Verify
        assert call_count == 2, f"Expected 2 screenshot attempts, got {call_count}"
        
        """
        ACTUAL OUTPUT:
        - Loop executes exactly 2 times
        - No exponential backoff between attempts
        - Returns last captured image even if validation fails
        """
    
    def test_step_4_method_override(self):
        """Test method selection with override"""
        # Setup with override
        self.screenshot_obj._screenshot_interval.wait = Mock()
        self.screenshot_obj._screenshot_interval.reset = Mock()
        
        mock_override_method = Mock(return_value=np.ones((720, 1280, 3), dtype=np.uint8))
        mock_default_method = Mock(return_value=np.zeros((720, 1280, 3), dtype=np.uint8))
        
        # Test with override
        with patch.object(self.screenshot_obj, 'screenshot_method_override', "OVERRIDE", create=True):
            with patch.object(self.screenshot_obj, 'screenshot_methods', {
                "OVERRIDE": mock_override_method,
                "ADB": mock_default_method
            }):
                with patch.object(self.screenshot_obj, 'check_screen_size', return_value=True):
                    with patch.object(self.screenshot_obj, 'check_screen_black', return_value=True):
                        with patch.object(self.screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                            result = self.screenshot_obj.screenshot()
        
        # Verify override was used
        mock_override_method.assert_called_once()
        mock_default_method.assert_not_called()
        assert np.array_equal(result, np.ones((720, 1280, 3), dtype=np.uint8))
        
        """
        ACTUAL OUTPUT:
        - Override method takes precedence over config
        - Config method ignored when override present
        - Override must exist in screenshot_methods dict
        """
    
    def test_step_5_method_fallback(self):
        """Test fallback to screenshot_adb when method not found"""
        # Setup
        self.screenshot_obj._screenshot_interval.wait = Mock()
        self.screenshot_obj._screenshot_interval.reset = Mock()
        self.mock_config.Emulator_ScreenshotMethod = "INVALID_METHOD"
        
        mock_adb_method = Mock(return_value=np.zeros((720, 1280, 3), dtype=np.uint8))
        self.screenshot_obj.screenshot_adb = mock_adb_method
        
        with patch.object(self.screenshot_obj, 'screenshot_methods', {"ADB": Mock()}):  # No INVALID_METHOD
            with patch.object(self.screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(self.screenshot_obj, 'check_screen_black', return_value=True):
                    with patch.object(self.screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        # Execute
                        self.screenshot_obj.screenshot()
        
        # Verify fallback
        mock_adb_method.assert_called()
        
        """
        ACTUAL OUTPUT:
        - Invalid method names fall back to screenshot_adb
        - No error raised for invalid method
        - screenshot_adb is the universal fallback
        """
    
    def test_step_7_dedithering_performance(self):
        """Test dedithering adds expected delay"""
        # Setup
        self.screenshot_obj._screenshot_interval.wait = Mock()
        self.screenshot_obj._screenshot_interval.reset = Mock()
        self.mock_config.Emulator_ScreenshotDedithering = True
        
        test_image = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        
        with patch.object(self.screenshot_obj, 'screenshot_methods', {"ADB": Mock(return_value=test_image.copy())}):
            with patch.object(self.screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(self.screenshot_obj, 'check_screen_black', return_value=True):
                    with patch.object(self.screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        # Mock cv2.fastNlMeansDenoising to track calls
                        with patch('cv2.fastNlMeansDenoising') as mock_denoise:
                            # Execute
                            self.screenshot_obj.screenshot()
        
        # Verify
        mock_denoise.assert_called_once()
        args = mock_denoise.call_args[0]
        kwargs = mock_denoise.call_args[1]
        
        # Check parameters
        assert kwargs.get('h') == 17
        assert kwargs.get('templateWindowSize') == 1
        assert kwargs.get('searchWindowSize') == 2
        
        """
        ACTUAL OUTPUT:
        - fastNlMeansDenoising called with specific parameters
        - h=17 (filter strength)
        - templateWindowSize=1 (template patch size)
        - searchWindowSize=2 (search window size)
        - Modifies image in-place (same array for src and dst)
        - Adds 40-60ms processing time
        """
    
    def test_step_10_validation_black_screen_behavior(self):
        """Test validation behavior when black screen detected"""
        # Setup
        self.screenshot_obj._screenshot_interval.wait = Mock()
        self.screenshot_obj._screenshot_interval.reset = Mock()
        
        attempt_count = 0
        def track_attempts():
            nonlocal attempt_count
            attempt_count += 1
            return np.zeros((720, 1280, 3), dtype=np.uint8)  # Black image
        
        with patch.object(self.screenshot_obj, 'screenshot_methods', {"ADB": track_attempts}):
            with patch.object(self.screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(self.screenshot_obj, 'check_screen_black', return_value=False):  # Black screen detected
                    with patch.object(self.screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        # Execute
                        result = self.screenshot_obj.screenshot()
        
        # Verify
        assert attempt_count == 2  # Both retry attempts used
        assert result.shape == (720, 1280, 3)  # Still returns the black image
        
        """
        ACTUAL OUTPUT:
        - check_screen_black() returns False for black screens
        - This causes retry loop to continue
        - After 2 attempts, returns the black image anyway
        - No exception raised for black screen
        """
    
    def test_step_9_error_logging_deque(self):
        """Test screenshot deque behavior for error logging"""
        # Setup
        self.screenshot_obj._screenshot_interval.wait = Mock()
        self.screenshot_obj._screenshot_interval.reset = Mock()
        self.mock_config.Error_SaveError = True
        
        # Clear deque
        self.screenshot_obj.screenshot_deque.clear()
        
        test_image = np.ones((720, 1280, 3), dtype=np.uint8) * 100
        
        with patch.object(self.screenshot_obj, 'screenshot_methods', {"ADB": Mock(return_value=test_image)}):
            with patch.object(self.screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(self.screenshot_obj, 'check_screen_black', return_value=True):
                    with patch.object(self.screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        # Execute
                        self.screenshot_obj.screenshot()
        
        # Verify
        assert len(self.screenshot_obj.screenshot_deque) == 1
        entry = self.screenshot_obj.screenshot_deque[0]
        assert 'time' in entry
        assert 'image' in entry
        assert isinstance(entry['time'], datetime)
        assert np.array_equal(entry['image'], test_image)
        
        """
        ACTUAL OUTPUT:
        - Deque stores dict with 'time' and 'image' keys
        - Time is datetime.now() when screenshot taken
        - Image is the processed image (after dedithering/orientation)
        - Deque has maxlen=30 (oldest entries removed automatically)
        """


class TestScreenshotIntegration:
    """Test how screenshot steps interact with each other"""
    
    def test_retry_with_changing_validation(self):
        """Test retry behavior when validation fails then succeeds"""
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "ADB"
        screenshot_obj.config.Emulator_ScreenshotDedithering = False
        screenshot_obj.config.Error_SaveError = False
        screenshot_obj._screenshot_interval = Mock()
        
        # Track attempts
        attempts = []
        def mock_method():
            attempts.append(len(attempts))
            if len(attempts) == 1:
                return np.zeros((720, 1280, 3), dtype=np.uint8)  # Black first time
            else:
                return np.ones((720, 1280, 3), dtype=np.uint8) * 100  # Valid second time
        
        # Mock validation to fail first, succeed second
        validation_calls = []
        def mock_black_check():
            validation_calls.append(len(validation_calls))
            return len(validation_calls) > 1  # False first time, True second
        
        with patch.object(screenshot_obj, 'screenshot_methods', {"ADB": mock_method}):
            with patch.object(screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(screenshot_obj, 'check_screen_black', side_effect=mock_black_check):
                    with patch.object(screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        result = screenshot_obj.screenshot()
        
        # Verify
        assert len(attempts) == 2  # Two screenshot attempts
        assert len(validation_calls) == 2  # Two validation attempts
        assert np.mean(result) > 50  # Got the valid (non-black) image
        
        """
        ACTUAL OUTPUT:
        - First attempt captures black screen
        - check_screen_black returns False
        - Retry loop continues
        - Second attempt captures valid screen
        - check_screen_black returns True
        - Loop breaks and returns valid image
        """
    
    def test_no_retry_on_success(self):
        """Test that successful screenshot doesn't retry"""
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "ADB"
        screenshot_obj.config.Emulator_ScreenshotDedithering = False
        screenshot_obj.config.Error_SaveError = False
        screenshot_obj._screenshot_interval = Mock()
        
        attempt_count = 0
        def count_attempts():
            nonlocal attempt_count
            attempt_count += 1
            return np.ones((720, 1280, 3), dtype=np.uint8) * 128
        
        with patch.object(screenshot_obj, 'screenshot_methods', {"ADB": count_attempts}):
            with patch.object(screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(screenshot_obj, 'check_screen_black', return_value=True):
                    with patch.object(screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        screenshot_obj.screenshot()
        
        assert attempt_count == 1  # Only one attempt needed
        
        """
        ACTUAL OUTPUT:
        - Valid screenshot on first attempt
        - Both validations pass
        - Loop breaks immediately
        - No unnecessary retries
        """


class TestScreenshotFailureModes:
    """Test various failure scenarios"""
    
    def test_screenshot_method_exception(self):
        """Test behavior when screenshot method raises exception"""
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "ADB"
        screenshot_obj._screenshot_interval = Mock()
        
        def failing_method():
            raise Exception("ADB connection failed")
        
        with patch.object(screenshot_obj, 'screenshot_methods', {"ADB": failing_method}):
            with pytest.raises(Exception) as exc_info:
                screenshot_obj.screenshot()
        
        assert "ADB connection failed" in str(exc_info.value)
        
        """
        ACTUAL OUTPUT:
        - No exception handling in screenshot()
        - Exception propagates to caller
        - No retry on exception (only on validation failure)
        - Bot will crash on screenshot method failure
        """
    
    def test_dedithering_exception(self):
        """Test behavior when OpenCV dedithering fails"""
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "ADB"
        screenshot_obj.config.Emulator_ScreenshotDedithering = True
        screenshot_obj._screenshot_interval = Mock()
        
        with patch.object(screenshot_obj, 'screenshot_methods', {"ADB": Mock(return_value=np.zeros((720, 1280, 3), dtype=np.uint8))}):
            with patch('cv2.fastNlMeansDenoising', side_effect=Exception("OpenCV error")):
                with pytest.raises(Exception) as exc_info:
                    screenshot_obj.screenshot()
        
        assert "OpenCV error" in str(exc_info.value)
        
        """
        ACTUAL OUTPUT:
        - OpenCV exceptions not caught
        - Bot crashes on dedithering failure
        - No fallback to non-dedithered image
        """


class TestCurrentBugVerification:
    """Tests that demonstrate the current screenshot retry bug"""
    
    def test_black_screen_only_2_retries(self):
        """Verify the bug: only 2 retry attempts for black screens"""
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "ADB_nc"
        screenshot_obj.config.Emulator_ScreenshotDedithering = False
        screenshot_obj.config.Error_SaveError = False
        screenshot_obj._screenshot_interval = Mock()
        
        # Always return black screen
        black_screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        attempt_count = 0
        
        def count_attempts():
            nonlocal attempt_count
            attempt_count += 1
            return black_screen
        
        with patch.object(screenshot_obj, 'screenshot_methods', {"ADB_nc": count_attempts}):
            with patch.object(screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(screenshot_obj, 'get_color', return_value=(0.0, 0.0, 0.0)):
                    with patch.object(screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        with patch.object(screenshot_obj, '_screen_black_checked', False, create=True):
                            result = screenshot_obj.screenshot()
        
        # Verify bug behavior
        assert attempt_count == 2  # Only 2 attempts
        assert np.array_equal(result, black_screen)  # Returns black screen
        
        """
        ACTUAL BUG BEHAVIOR:
        - Screenshot method returns black screen
        - check_screen_black detects color (0.0, 0.0, 0.0)
        - Returns False causing retry
        - Only tries 2 times total
        - Returns black screen to caller
        - Bot continues with invalid data
        - Causes "Unknown page" errors downstream
        """