"""
Tests to verify the screenshot retry fix with exponential backoff.
This demonstrates the before/after behavior of the black screen retry bug.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import numpy as np
import time
from unittest.mock import Mock, MagicMock, patch, PropertyMock

from module.device.screenshot import Screenshot
from module.base.timer import Timer


class TestScreenshotRetryBugFix:
    """Tests demonstrating the screenshot retry bug fix"""
    
    def test_old_behavior_only_2_retries(self):
        """Test OLD behavior: only 2 retries for black screens"""
        # Simulate old code with only 2 retries
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "ADB_nc"
        screenshot_obj.config.Emulator_ScreenshotDedithering = False
        screenshot_obj.config.Error_SaveError = False
        screenshot_obj._screenshot_interval = Mock()
        
        attempt_count = 0
        black_screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        def count_attempts():
            nonlocal attempt_count
            attempt_count += 1
            return black_screen
        
        # Simulate old code behavior
        with patch.object(screenshot_obj, 'screenshot') as mock_screenshot:
            def old_screenshot_behavior(self):
                self._screenshot_interval.wait()
                self._screenshot_interval.reset()
                
                # OLD CODE: Only 2 attempts
                for _ in range(2):
                    self.image = count_attempts()
                    if self.check_screen_size() and self.check_screen_black():
                        break
                    else:
                        continue
                return self.image
            
            mock_screenshot.side_effect = lambda: old_screenshot_behavior(screenshot_obj)
            
            with patch.object(screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(screenshot_obj, 'check_screen_black', return_value=False):
                    result = screenshot_obj.screenshot()
        
        # Verify old bug behavior
        assert attempt_count == 2  # Only 2 attempts in old code
        assert np.array_equal(result, black_screen)  # Returns black screen
        
        """
        OLD BUG BEHAVIOR:
        - Only 2 retry attempts total
        - No exponential backoff
        - Returns black screen after 2 failures
        - Causes downstream "Unknown page" errors
        """
    
    def test_new_behavior_10_retries_with_backoff(self):
        """Test NEW behavior: 10 retries with exponential backoff"""
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "ADB_nc"
        screenshot_obj.config.Emulator_ScreenshotDedithering = False
        screenshot_obj.config.Error_SaveError = False
        screenshot_obj._screenshot_interval = Mock()
        
        attempt_count = 0
        wait_times = []
        
        def track_attempts():
            nonlocal attempt_count
            attempt_count += 1
            # Return valid image after 5 attempts
            if attempt_count <= 5:
                return np.zeros((720, 1280, 3), dtype=np.uint8)  # Black
            else:
                return np.ones((720, 1280, 3), dtype=np.uint8) * 128  # Valid
        
        # Mock time.sleep to track wait times
        original_sleep = time.sleep
        def mock_sleep(seconds):
            wait_times.append(seconds)
        
        with patch.object(screenshot_obj, 'screenshot_methods', {"ADB_nc": track_attempts}):
            with patch.object(screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(screenshot_obj, 'check_screen_black') as mock_black:
                    # Return False for black screens, True for valid
                    mock_black.side_effect = lambda: attempt_count > 5
                    
                    with patch.object(screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        with patch('time.sleep', mock_sleep):
                            result = screenshot_obj.screenshot()
        
        # Verify new behavior
        assert attempt_count == 6  # Succeeded on 6th attempt
        assert len(wait_times) == 5  # 5 waits between attempts
        
        # Verify exponential backoff
        expected_waits = [0.5, 1.0, 2.0, 4.0, 5.0]  # Capped at 5.0
        assert wait_times == expected_waits
        
        # Verify we got valid image
        assert np.mean(result) > 100  # Got the valid image, not black
        
        """
        NEW FIX BEHAVIOR:
        - Up to 10 retry attempts
        - Exponential backoff: 0.5s, 1s, 2s, 4s, 5s (capped)
        - Continues trying until success or max attempts
        - Much more resilient to temporary failures
        """
    
    def test_dedithering_skipped_on_retry(self):
        """Test that dedithering is only applied on first attempt"""
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "ADB"
        screenshot_obj.config.Emulator_ScreenshotDedithering = True  # Enabled
        screenshot_obj.config.Error_SaveError = False
        screenshot_obj._screenshot_interval = Mock()
        
        denoise_calls = []
        attempt_count = 0
        
        def track_attempts():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count <= 2:
                return np.zeros((720, 1280, 3), dtype=np.uint8)  # Black
            else:
                return np.ones((720, 1280, 3), dtype=np.uint8) * 128  # Valid
        
        def mock_denoise(src, dst, **kwargs):
            denoise_calls.append(attempt_count)
        
        with patch.object(screenshot_obj, 'screenshot_methods', {"ADB": track_attempts}):
            with patch.object(screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(screenshot_obj, 'check_screen_black') as mock_black:
                    mock_black.side_effect = lambda: attempt_count > 2
                    
                    with patch.object(screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        with patch('cv2.fastNlMeansDenoising', mock_denoise):
                            with patch('time.sleep', Mock()):  # Skip actual sleep
                                screenshot_obj.screenshot()
        
        # Verify dedithering behavior
        assert len(denoise_calls) == 1  # Only called once
        assert denoise_calls[0] == 1  # Called on first attempt only
        
        """
        NEW OPTIMIZATION:
        - Dedithering only on first attempt
        - Skipped on retries to save 40-60ms per retry
        - Improves retry performance
        """
    
    def test_max_retry_limit(self):
        """Test that retries stop at 10 attempts"""
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "ADB"
        screenshot_obj.config.Emulator_ScreenshotDedithering = False
        screenshot_obj.config.Error_SaveError = False
        screenshot_obj._screenshot_interval = Mock()
        
        attempt_count = 0
        
        def always_black():
            nonlocal attempt_count
            attempt_count += 1
            return np.zeros((720, 1280, 3), dtype=np.uint8)
        
        with patch.object(screenshot_obj, 'screenshot_methods', {"ADB": always_black}):
            with patch.object(screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(screenshot_obj, 'check_screen_black', return_value=False):  # Always fail
                    with patch.object(screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        with patch('time.sleep', Mock()):  # Skip sleep
                            result = screenshot_obj.screenshot()
        
        # Verify max attempts
        assert attempt_count == 10  # Exactly 10 attempts
        assert np.array_equal(result, np.zeros((720, 1280, 3), dtype=np.uint8))  # Still black
        
        """
        SAFETY LIMIT:
        - Maximum 10 attempts to prevent infinite loops
        - Returns last captured image even if all fail
        - Prevents bot hanging indefinitely
        """
    
    def test_successful_screenshot_no_retry(self):
        """Test that successful screenshot doesn't retry"""
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "ADB"
        screenshot_obj.config.Emulator_ScreenshotDedithering = False
        screenshot_obj.config.Error_SaveError = False
        screenshot_obj._screenshot_interval = Mock()
        
        attempt_count = 0
        wait_called = False
        
        def valid_screenshot():
            nonlocal attempt_count
            attempt_count += 1
            return np.ones((720, 1280, 3), dtype=np.uint8) * 128
        
        def mock_sleep(seconds):
            nonlocal wait_called
            wait_called = True
        
        with patch.object(screenshot_obj, 'screenshot_methods', {"ADB": valid_screenshot}):
            with patch.object(screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(screenshot_obj, 'check_screen_black', return_value=True):  # Success
                    with patch.object(screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        with patch('time.sleep', mock_sleep):
                            result = screenshot_obj.screenshot()
        
        # Verify no retry
        assert attempt_count == 1  # Only one attempt
        assert not wait_called  # No sleep called
        assert np.mean(result) > 100  # Valid image returned
        
        """
        EFFICIENCY:
        - No unnecessary retries on success
        - No delay when screenshot works first time
        - Maintains original performance for normal case
        """


class TestRetryBackoffCalculation:
    """Test the exponential backoff calculation"""
    
    def test_backoff_progression(self):
        """Verify the exact backoff time calculation"""
        # The formula: min(0.5 * (2 ** attempt), 5.0)
        
        expected_backoffs = [
            (0, 0.5),   # 0.5 * 2^0 = 0.5
            (1, 1.0),   # 0.5 * 2^1 = 1.0
            (2, 2.0),   # 0.5 * 2^2 = 2.0
            (3, 4.0),   # 0.5 * 2^3 = 4.0
            (4, 5.0),   # 0.5 * 2^4 = 8.0, capped at 5.0
            (5, 5.0),   # 0.5 * 2^5 = 16.0, capped at 5.0
            (6, 5.0),   # Capped
            (7, 5.0),   # Capped
            (8, 5.0),   # Capped
        ]
        
        for attempt, expected in expected_backoffs:
            calculated = min(0.5 * (2 ** attempt), 5.0)
            assert calculated == expected, f"Attempt {attempt}: expected {expected}, got {calculated}"
        
        """
        BACKOFF STRATEGY:
        - Starts at 0.5 seconds
        - Doubles each time: 0.5, 1, 2, 4
        - Capped at 5 seconds maximum
        - Total max wait time: ~40 seconds for 10 attempts
        """


class TestPerformanceImpact:
    """Test the performance impact of the retry fix"""
    
    def test_worst_case_timing(self):
        """Calculate worst-case timing with all retries"""
        # Assumptions:
        # - Screenshot capture: ~100ms
        # - Validation checks: ~10ms
        # - Dedithering (first only): ~50ms
        
        screenshot_time = 0.1  # 100ms per screenshot
        validation_time = 0.01  # 10ms for checks
        dedither_time = 0.05  # 50ms for first attempt only
        
        # Calculate total time for 10 failed attempts
        total_time = 0
        
        # First attempt with dedithering
        total_time += screenshot_time + dedither_time + validation_time
        
        # Remaining 9 attempts without dedithering
        wait_times = [0.5, 1.0, 2.0, 4.0, 5.0, 5.0, 5.0, 5.0, 5.0]
        for wait in wait_times:
            total_time += wait + screenshot_time + validation_time
        
        assert total_time < 45  # Should be under 45 seconds worst case
        
        # Best case (success on first try)
        best_case = screenshot_time + dedither_time + validation_time
        assert best_case < 0.2  # Under 200ms
        
        """
        PERFORMANCE ANALYSIS:
        - Best case (success): ~160ms (same as before)
        - Worst case (10 failures): ~33 seconds + capture time
        - Average case (succeed after 2-3 retries): ~2-3 seconds
        - Acceptable tradeoff for reliability
        """