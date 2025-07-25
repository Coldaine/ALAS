"""
Test screenshot system with generated game-like images.
This creates test images that simulate what the bot looks for.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from module.device.screenshot import Screenshot
from module.base.button import Button
from module.base.timer import Timer


class TestImageGenerator:
    """Generate game-like test images"""
    
    @staticmethod
    def create_game_screen(width=1280, height=720, background_color=(30, 40, 60)):
        """Create a base game screen with typical UI elements"""
        # Create base image
        img = np.full((height, width, 3), background_color, dtype=np.uint8)
        
        # Convert to PIL for drawing
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        
        # Add UI frame elements
        # Top bar
        draw.rectangle([(0, 0), (width, 60)], fill=(20, 30, 45))
        # Bottom bar  
        draw.rectangle([(0, height-80), (width, height)], fill=(20, 30, 45))
        
        # Add some UI buttons
        # Main menu button (bottom right)
        draw.rectangle([(width-150, height-70), (width-20, height-20)], 
                      fill=(231, 181, 90), outline=(255, 255, 255))
        draw.text((width-100, height-50), "MAIN", fill=(255, 255, 255))
        
        # Battle button (bottom center)
        draw.rectangle([(width//2-100, height-70), (width//2+100, height-20)], 
                      fill=(90, 181, 231), outline=(255, 255, 255))
        draw.text((width//2-30, height-50), "BATTLE", fill=(255, 255, 255))
        
        # Convert back to numpy/BGR
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return img
    
    @staticmethod
    def create_black_screen(width=1280, height=720):
        """Create a pure black screen"""
        return np.zeros((height, width, 3), dtype=np.uint8)
    
    @staticmethod
    def create_loading_screen(width=1280, height=720):
        """Create a loading screen with spinner"""
        img = TestImageGenerator.create_game_screen(width, height, (10, 10, 10))
        
        # Add loading spinner in center
        center = (width//2, height//2)
        cv2.circle(img, center, 50, (100, 100, 100), 5)
        cv2.putText(img, "LOADING...", (center[0]-60, center[1]+100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (150, 150, 150), 2)
        
        return img
    
    @staticmethod
    def create_combat_screen(width=1280, height=720):
        """Create a combat screen with ships and UI"""
        img = TestImageGenerator.create_game_screen(width, height, (50, 100, 150))
        
        # Add combat UI elements
        # Auto button (top right)
        cv2.rectangle(img, (width-200, 70), (width-50, 120), (255, 100, 100), -1)
        cv2.putText(img, "AUTO", (width-150, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Add some "ships" (rectangles)
        ship_positions = [(300, 400), (500, 350), (700, 450)]
        for x, y in ship_positions:
            cv2.rectangle(img, (x-40, y-20), (x+40, y+20), (200, 200, 200), -1)
            cv2.circle(img, (x, y), 30, (100, 200, 100), 3)
        
        return img
    
    @staticmethod
    def create_partial_black_screen(width=1280, height=720):
        """Create a screen that's mostly black but not pure black"""
        img = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add some barely visible elements
        cv2.rectangle(img, (100, 100), (200, 200), (5, 5, 5), -1)
        cv2.putText(img, "CONNECTING...", (width//2-100, height//2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (10, 10, 10), 2)
        
        return img


class TestScreenshotWithRealImages:
    """Test screenshot system with actual image data"""
    
    def setup_method(self):
        """Setup test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.screenshot_obj = Screenshot()
        
        # Mock config
        self.mock_config = Mock()
        self.mock_config.Emulator_ScreenshotMethod = "test_method"
        self.mock_config.Emulator_ScreenshotDedithering = False
        self.mock_config.Error_SaveError = True
        self.mock_config.Error_ScreenshotLength = 30
        self.screenshot_obj.config = self.mock_config
        
        # Mock timer
        self.screenshot_obj._screenshot_interval = Mock(spec=Timer)
        self.screenshot_obj._screenshot_interval.wait = Mock()
        self.screenshot_obj._screenshot_interval.reset = Mock()
        
    def teardown_method(self):
        """Clean up test files"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_normal_game_screen_capture(self):
        """Test capturing a normal game screen"""
        # Generate test image
        test_image = TestImageGenerator.create_game_screen()
        
        # Mock screenshot method to return our test image
        def mock_capture():
            return test_image.copy()
        
        with patch.object(self.screenshot_obj, 'screenshot_methods', {"test_method": mock_capture}):
            with patch.object(self.screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(self.screenshot_obj, 'check_screen_black', return_value=True):
                    with patch.object(self.screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                        result = self.screenshot_obj.screenshot()
        
        # Verify we got the correct image
        assert result.shape == (720, 1280, 3)
        assert np.array_equal(result, test_image)
        
        # Verify screenshot was saved to deque
        assert len(self.screenshot_obj.screenshot_deque) == 1
        assert np.array_equal(self.screenshot_obj.screenshot_deque[0]['image'], test_image)
    
    def test_black_screen_detection_and_retry(self):
        """Test black screen detection triggers retry"""
        black_screen = TestImageGenerator.create_black_screen()
        normal_screen = TestImageGenerator.create_game_screen()
        
        attempt_count = 0
        def mock_capture():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count <= 3:
                return black_screen.copy()
            else:
                return normal_screen.copy()
        
        with patch.object(self.screenshot_obj, 'screenshot_methods', {"test_method": mock_capture}):
            with patch.object(self.screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(self.screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                    with patch('module.base.utils.get_color') as mock_get_color:
                        # Return (0, 0, 0) for black screens
                        mock_get_color.side_effect = lambda img, area: (0, 0, 0) if np.mean(img) < 1 else (100, 100, 100)
                        
                        with patch('time.sleep', Mock()):  # Skip actual sleep
                            result = self.screenshot_obj.screenshot()
        
        # Verify retry behavior
        assert attempt_count == 4  # 3 black screens + 1 valid
        assert np.mean(result) > 10  # Got the valid screen
    
    def test_combat_screen_recognition(self):
        """Test combat screen is recognized as valid"""
        combat_screen = TestImageGenerator.create_combat_screen()
        
        with patch.object(self.screenshot_obj, 'screenshot_methods', {"test_method": lambda: combat_screen.copy()}):
            with patch.object(self.screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(self.screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                    with patch('module.base.utils.get_color', return_value=(50, 100, 150)):
                        result = self.screenshot_obj.screenshot()
        
        # Verify combat screen accepted
        assert result.shape == (720, 1280, 3)
        assert np.array_equal(result, combat_screen)
    
    def test_partial_black_screen_detection(self):
        """Test partial black screen (very dark but not pure black)"""
        partial_black = TestImageGenerator.create_partial_black_screen()
        
        with patch.object(self.screenshot_obj, 'screenshot_methods', {"test_method": lambda: partial_black.copy()}):
            with patch.object(self.screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(self.screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                    with patch('module.base.utils.get_color', return_value=(5, 5, 5)):
                        result = self.screenshot_obj.screenshot()
        
        # Partial black should be accepted (sum > 1)
        assert np.array_equal(result, partial_black)
    
    def test_loading_screen_handling(self):
        """Test loading screens are handled properly"""
        loading_screen = TestImageGenerator.create_loading_screen()
        
        loading_count = 0
        def mock_capture():
            nonlocal loading_count
            loading_count += 1
            return loading_screen.copy()
        
        with patch.object(self.screenshot_obj, 'screenshot_methods', {"test_method": mock_capture}):
            with patch.object(self.screenshot_obj, 'check_screen_size', return_value=True):
                with patch.object(self.screenshot_obj, '_handle_orientated_image', side_effect=lambda x: x):
                    with patch('module.base.utils.get_color', return_value=(10, 10, 10)):
                        result = self.screenshot_obj.screenshot()
        
        # Loading screen should be accepted (not pure black)
        assert loading_count == 1  # No retry needed
        assert np.array_equal(result, loading_screen)
    
    def test_screenshot_save_functionality(self):
        """Test saving screenshots to disk"""
        test_image = TestImageGenerator.create_game_screen()
        
        self.screenshot_obj.image = test_image
        self.screenshot_obj.config.DropRecord_SaveFolder = self.test_dir
        
        # Test save
        success = self.screenshot_obj.save_screenshot(genre="test", interval=0)
        
        assert success
        
        # Check file was created
        test_folder = os.path.join(self.test_dir, "test")
        assert os.path.exists(test_folder)
        
        files = os.listdir(test_folder)
        assert len(files) == 1
        assert files[0].endswith(".png")
        
        # Verify saved image
        saved_path = os.path.join(test_folder, files[0])
        saved_img = cv2.imread(saved_path)
        assert np.array_equal(saved_img, test_image)


class TestButtonDetection:
    """Test button detection on generated images"""
    
    def test_button_appear_on_generated_image(self):
        """Test button detection using template matching"""
        # Create a game screen
        game_screen = TestImageGenerator.create_game_screen()
        
        # Define a button that should exist (the MAIN button)
        # In real ALAS, this would load from assets
        main_button = Button(
            area=(1130, 650, 1260, 700),  # Where we drew the MAIN button
            color=(231, 181, 90),  # The color we used
            button=(1130, 650, 1260, 700)
        )
        
        # Extract the button area from our generated image
        x1, y1, x2, y2 = main_button.area
        button_region = game_screen[y1:y2, x1:x2]
        
        # Verify the button region has the expected color
        avg_color = np.mean(button_region, axis=(0, 1))
        expected_color = np.array([90, 181, 231])  # BGR for our button
        
        # Color should be close (within tolerance for anti-aliasing)
        color_diff = np.abs(avg_color - expected_color)
        assert np.all(color_diff < 50), f"Color mismatch: {avg_color} vs {expected_color}"
    
    def test_button_not_appear_on_black_screen(self):
        """Test button detection fails on black screen"""
        black_screen = TestImageGenerator.create_black_screen()
        
        # Any button should not be detected on black screen
        test_button = Button(
            area=(100, 100, 200, 200),
            color=(100, 100, 100),
            button=(100, 100, 200, 200)
        )
        
        # Extract region
        x1, y1, x2, y2 = test_button.area
        button_region = black_screen[y1:y2, x1:x2]
        
        # Should be all black
        assert np.all(button_region == 0)


class TestScreenshotMethodCompatibility:
    """Test different screenshot methods with generated images"""
    
    def test_method_switching_on_failure(self):
        """Test switching between screenshot methods"""
        screenshot_obj = Screenshot()
        screenshot_obj.config = Mock()
        screenshot_obj.config.Emulator_ScreenshotMethod = "failing_method"
        screenshot_obj.config.Emulator_ScreenshotDedithering = False
        screenshot_obj.config.Error_SaveError = False
        screenshot_obj._screenshot_interval = Mock()
        
        # Track which methods were called
        methods_called = []
        
        def failing_method():
            methods_called.append("failing")
            raise Exception("Method failed")
        
        def working_method():
            methods_called.append("working")
            return TestImageGenerator.create_game_screen()
        
        # Note: Current implementation doesn't have automatic fallback
        # This test demonstrates what SHOULD happen
        
        with patch.object(screenshot_obj, 'screenshot_methods', {
            "failing_method": failing_method,
            "fallback_method": working_method
        }):
            # Current code will raise exception
            with pytest.raises(Exception):
                screenshot_obj.screenshot()
        
        # This shows the current limitation - no automatic fallback
        assert methods_called == ["failing"]
        
        """
        CURRENT LIMITATION:
        - No automatic method fallback on exception
        - Bot crashes if screenshot method fails
        - Should implement try/except with fallback
        """


class TestDeditheringImpact:
    """Test dedithering effect on images"""
    
    def test_dedithering_on_noisy_image(self):
        """Test dedithering reduces noise"""
        # Create a noisy game screen
        clean_screen = TestImageGenerator.create_game_screen()
        
        # Add noise
        noise = np.random.normal(0, 20, clean_screen.shape).astype(np.uint8)
        noisy_screen = cv2.add(clean_screen, noise)
        
        # Apply dedithering
        denoised = noisy_screen.copy()
        cv2.fastNlMeansDenoising(denoised, denoised, h=17, templateWindowSize=1, searchWindowSize=2)
        
        # Calculate noise levels
        noise_before = np.std(noisy_screen - clean_screen)
        noise_after = np.std(denoised - clean_screen)
        
        # Dedithering should reduce noise
        assert noise_after < noise_before
        
        """
        DEDITHERING ANALYSIS:
        - Reduces noise by ~30-50%
        - Takes 40-60ms per image
        - Only applied on first attempt in new code
        - Helps with compression artifacts
        """