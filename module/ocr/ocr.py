import time
import os
import json
import re
from datetime import timedelta, datetime
from typing import TYPE_CHECKING

import cv2
import module.config.server as server
from module.base.button import Button
from module.base.decorator import cached_property
from module.base.utils import *
from module.logger import logger
from module.ocr.rpc import ModelProxyFactory
from module.webui.setting import State
from module.base.error_handler import OCR_ERROR_COUNTER
# OCR backend with PaddleOCR interface compatibility
try:
    from paddleocr import PaddleOCR
    # Check if we have the newer PaddleOCR 3.x with predict method
    try:
        # Try PaddleOCR 3.x initialization (no use_gpu parameter)
        _test_ocr = PaddleOCR(lang='en')
        has_predict = hasattr(_test_ocr, 'predict')
    except:
        # Fallback to PaddleOCR 2.x initialization
        _test_ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False, use_gpu=False)
        has_predict = False
    
    if has_predict:
        # PaddleOCR 3.x with new API
        OCR_MODEL = _test_ocr
        
        # Wrap the predict method to match the old ocr() interface
        def ocr_wrapper(images, cls=True):
            results = []
            if not isinstance(images, list):
                images = [images]
            
            for img in images:
                # Use predict() for PaddleOCR 3.x
                predict_results = OCR_MODEL.predict(img)
                if predict_results and len(predict_results) > 0:
                    # Convert new format to old format
                    formatted_result = []
                    res_dict = predict_results[0]
                    texts = res_dict.get('rec_texts', [])
                    scores = res_dict.get('rec_scores', [])
                    polys = res_dict.get('rec_polys', [])
                    
                    # Match the old ocr() output format: list of [bbox, (text, score)]
                    for i in range(len(texts)):
                        if i < len(polys) and i < len(scores):
                            bbox = polys[i].tolist() if hasattr(polys[i], 'tolist') else polys[i]
                            formatted_result.append([bbox, (texts[i], scores[i])])
                    
                    results.append(formatted_result if formatted_result else None)
                else:
                    results.append(None)
            
            return results
        
        # Replace ocr method with wrapper
        OCR_MODEL.ocr = ocr_wrapper
        # Add close method for compatibility
        if not hasattr(OCR_MODEL, 'close'):
            OCR_MODEL.close = lambda: None
        logger.info('Using PaddleOCR 3.x with compatibility wrapper.')
    else:
        # PaddleOCR 2.x - use original ocr() method
        OCR_MODEL = _test_ocr
        logger.info('Using PaddleOCR 2.x backend.')
except ImportError:
    # Fallback: Create PaddleOCR-compatible wrapper around EasyOCR
    logger.info('PaddleOCR not available, creating EasyOCR compatibility wrapper.')
    
    try:
        import easyocr
        
        class PaddleOCRCompatWrapper:
            """EasyOCR wrapper that mimics PaddleOCR interface for ALAS compatibility."""
            
            def __init__(self):
                self.reader = easyocr.Reader(['en'], gpu=False, verbose=False)
                self.name = 'EasyOCR-PaddleOCR-Compat'
            
            def ocr(self, images, cls=True, **kwargs):
                """
                OCR with PaddleOCR-compatible interface.
                
                Args:
                    images: Single image or list of images (numpy arrays)
                    cls: Angle classification (ignored for EasyOCR compatibility)
                    
                Returns:
                    List in PaddleOCR format: [result_per_image, ...]
                    Each result_per_image: [[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, confidence)]
                """
                # Handle single image
                if not isinstance(images, list):
                    images = [images]
                
                results = []
                for image in images:
                    try:
                        # EasyOCR returns: [[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], text, confidence]
                        easyocr_results = self.reader.readtext(image, detail=1)
                        
                        # Convert to PaddleOCR format: [[[box]], (text, confidence)]
                        paddleocr_format = []
                        for detection in easyocr_results:
                            box, text, confidence = detection
                            paddleocr_format.append([box, (text, confidence)])
                        
                        results.append(paddleocr_format if paddleocr_format else None)
                    except Exception as e:
                        logger.warning(f"EasyOCR processing failed: {e}")
                        results.append(None)
                
                return results
            
            def close(self):
                """Close method for compatibility with PaddleOCR interface."""
                pass
        
        OCR_MODEL = PaddleOCRCompatWrapper()
        logger.info('Using EasyOCR with PaddleOCR compatibility wrapper.')
        
    except ImportError:
        # Final fallback: Minimal OCR that returns PaddleOCR-compatible empty results
        class MinimalPaddleOCR:
            def ocr(self, images, cls=True, **kwargs):
                if not isinstance(images, list):
                    images = [images]
                return [None] * len(images)  # PaddleOCR returns None for no text found
            
            def close(self):
                pass
        
        OCR_MODEL = MinimalPaddleOCR()
        logger.warning('No OCR backend available - using minimal PaddleOCR-compatible fallback.')


class Ocr:
    SHOW_LOG = True
    SHOW_REVISE_WARNING = False
    
    # OCR debug screenshot settings
    OCR_DEBUG_DIR = './log/ocr_debug'
    OCR_DEBUG_MAX_FILES = 10
    _ocr_debug_counter = 0

    def __init__(self, buttons, letter=(255, 255, 255), threshold=128, alphabet=None, name=None):
        """
        Args:
            buttons (Button, tuple, list[Button], list[tuple]): OCR area.
            letter (tuple(int)): Letter RGB.
            threshold (int):
            alphabet: Alphabet white list.
            name (str):
        """
        self.name = str(buttons) if isinstance(buttons, Button) else name
        self._buttons = buttons
        self.letter = letter
        self.threshold = threshold
        self.alphabet = alphabet

    @property
    def buttons(self):
        buttons = self._buttons
        buttons = buttons if isinstance(buttons, list) else [buttons]
        buttons = [button.area if isinstance(button, Button) else button for button in buttons]
        return buttons

    @buttons.setter
    def buttons(self, value):
        self._buttons = value

    def pre_process(self, image):
        """
        Args:
            image (np.ndarray): Shape (height, width, channel)

        Returns:
            np.ndarray: Shape (height, width) or (height, width, 3) for PaddleOCR
        """
        image = extract_letters(image, letter=self.letter, threshold=self.threshold)
        image = image.astype(np.uint8)
        
        # PaddleOCR expects RGB images, convert grayscale to RGB
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        return image

    def after_process(self, result):
        """
        Args:
            result (str): '第二行'

        Returns:
            str:
        """
        return result
    
    def save_ocr_debug_screenshot(self, image, button_area, ocr_result):
        """
        Save OCR debug screenshot with rotating filenames
        
        Args:
            image (np.ndarray): The image being OCR'd
            button_area (tuple): The area coordinates (x1, y1, x2, y2)
            ocr_result (str): The OCR result text
        """
        # Check if debug screenshots are enabled (default to True if no config available)
        enabled = True
        try:
            # Try to get config from module.config.config if available
            from module.config.config import Config
            if hasattr(Config, 'Error_SaveOcrDebugScreenshots'):
                enabled = Config.Error_SaveOcrDebugScreenshots
        except:
            pass
            
        if not enabled:
            return
            
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.OCR_DEBUG_DIR, exist_ok=True)
            
            # Get current counter and increment
            counter = Ocr._ocr_debug_counter
            Ocr._ocr_debug_counter = (Ocr._ocr_debug_counter + 1) % self.OCR_DEBUG_MAX_FILES
            
            # Create filenames
            image_filename = os.path.join(self.OCR_DEBUG_DIR, f'ocr_{counter}.png')
            metadata_filename = os.path.join(self.OCR_DEBUG_DIR, f'ocr_{counter}.json')
            
            # Save image
            cv2.imwrite(image_filename, image)
            
            # Save metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'button_name': self.name,
                'button_area': button_area,
                'ocr_result': ocr_result,
                'success': bool(ocr_result and ocr_result.strip())
            }
            
            with open(metadata_filename, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            logger.debug(f'Saved OCR debug screenshot: {image_filename}')
            
        except Exception as e:
            logger.warning(f'Failed to save OCR debug screenshot: {e}')

    def ocr(self, image, direct_ocr=False):
        """
        Args:
            image (np.ndarray, list[np.ndarray]):
            direct_ocr (bool): True to skip preprocess.

        Returns:
            str, list[str]:
        """
        if image is None:
            return '' if not isinstance(self._buttons, list) or len(self._buttons) <= 1 else []

        image_list = image if isinstance(image, list) else [image]
        if not image_list:
            return []

        # Check device connection first (cost protection)
        device_connected = False
        try:
            from adbutils import AdbClient
            client = AdbClient(host="127.0.0.1", port=5037)
            devices = client.device_list()
            device_connected = len(devices) > 0
        except Exception as e:
            logger.debug(f"Device connection check failed: {e}")
            device_connected = False
            
        # Use vision OCR if device is connected and API is available
        if device_connected:
            try:
                # Vision OCR needs the full screenshot, not cropped images
                # Pass the original image (full screenshot) to vision OCR
                return self._vision_ocr(image)
            except Exception as e:
                logger.warning(f"Vision OCR failed, falling back to traditional: {e}")
                # Fall through to traditional OCR

        result_list = []
        try:
            # For traditional OCR, we need to crop each button area from the full image
            cropped_images = []
            for button in self.buttons:
                x1, y1, x2, y2 = button
                cropped = image[y1:y2, x1:x2] if isinstance(image, np.ndarray) else image
                cropped_images.append(cropped)
            
            # Pre-process
            preprocessed_images = []
            if not direct_ocr:
                for img in cropped_images:
                    preprocessed = self.pre_process(img)
                    preprocessed_images.append(preprocessed)
                image_list = preprocessed_images
            else:
                image_list = cropped_images

            # PaddleOCR returns a list of results, one for each image.
            # Each result is a list of [box, (text, score)].
            results = OCR_MODEL.ocr(image_list, cls=True)
            result_list = []
            for result_per_image in results:
                if result_per_image:
                    # Concat all text found in one image
                    text = ' '.join([line[1][0] for line in result_per_image])
                    result_list.append(text)
                else:
                    # No text found
                    result_list.append('')

            # Post-process
            result_list = [self.after_process(res) for res in result_list]
            
            # Save debug screenshots
            for idx, (img, res, button) in enumerate(zip(image_list, result_list, self.buttons)):
                self.save_ocr_debug_screenshot(img, button, res)

            if self.SHOW_LOG:
                for res, button in zip(result_list, self.buttons):
                    logger.info(f'OCR {self.name}@{button}: {res}')

        except Exception as e:
            logger.exception(e)
            # Return empty results matching the expected output shape
            result_list = ['' for _ in image_list]

        # Return single result if single image was passed
        if len(self.buttons) == 1 and isinstance(image, np.ndarray):
            return result_list[0]
        else:
            return result_list

    def _vision_ocr(self, full_screenshot):
        """Use Gemini vision to read text directly from full screenshot with button context"""
        try:
            import google.generativeai as genai
            from config.vision_llm_config import GOOGLE_API_KEY, GEMINI_MODEL
            from PIL import Image
            import numpy as np
            
            if not GOOGLE_API_KEY:
                logger.warning("No Google API key, falling back to OCR")
                raise ImportError("No API key")
                
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel(GEMINI_MODEL)
            
            # Convert full screenshot to PIL
            if isinstance(full_screenshot, np.ndarray):
                pil_screenshot = Image.fromarray(full_screenshot)
            else:
                pil_screenshot = full_screenshot
            
            results = []
            buttons = self._buttons if isinstance(self._buttons, list) else [self._buttons]
            
            for idx, button in enumerate(buttons):
                button_name = button.name if hasattr(button, 'name') else 'unknown'
                button_area = button.area if hasattr(button, 'area') else button
                
                # Get appropriate prompt based on button name and area
                prompt = self._get_vision_prompt_with_area(button_name, button_area, idx, len(buttons))
                
                try:
                    # Check cache with button area as part of key
                    cache_key = f"{button_name}_{button_area}_{hash(full_screenshot.tobytes() if isinstance(full_screenshot, np.ndarray) else id(full_screenshot))}"
                    if hasattr(self, '_vision_cache') and cache_key in self._vision_cache:
                        age = time.time() - self._vision_cache_time.get(cache_key, 0)
                        if age < 30:  # 30 second cache
                            results.append(self._vision_cache[cache_key])
                            continue
                    
                    # Call Gemini with full screenshot
                    response = model.generate_content([prompt, pil_screenshot])
                    text = response.text.strip()
                    
                    # Cache result
                    if not hasattr(self, '_vision_cache'):
                        self._vision_cache = {}
                        self._vision_cache_time = {}
                    self._vision_cache[cache_key] = text
                    self._vision_cache_time[cache_key] = time.time()
                    
                    results.append(text)
                except Exception as e:
                    logger.error(f"Vision OCR failed for {button_name}: {e}")
                    results.append("")
                    
            return results[0] if len(results) == 1 else results
            
        except ImportError:
            logger.warning("Google AI not available")
            raise
            
    def _traditional_ocr(self, image_list):
        """Fallback to traditional OCR"""
        # Use the existing OCR logic from the main ocr method
        result_list = []
        try:
            # Pre-process
            preprocessed_images = []
            for img in image_list:
                preprocessed = self.pre_process(img)
                preprocessed_images.append(preprocessed)

            # PaddleOCR returns a list of results, one for each image.
            # Each result is a list of [box, (text, score)].
            results = OCR_MODEL.ocr(preprocessed_images, cls=True)
            result_list = []
            for result_per_image in results:
                if result_per_image:
                    # Concat all text found in one image
                    text = ' '.join([line[1][0] for line in result_per_image])
                    result_list.append(text)
                else:
                    # No text found
                    result_list.append('')

            # Post-process
            result_list = [self.after_process(res) for res in result_list]

        except Exception as e:
            logger.exception(e)
            # Return empty results matching the expected output shape
            result_list = ['' for _ in image_list]

        return result_list

    def _get_vision_prompt(self, button_name):
        """Get appropriate prompt based on button context"""
        prompts = {
            'COMMISSION_TIME': "Read the time from this Azur Lane commission timer. Return format: HH:MM:SS",
            'RESEARCH_PROJECT': "Read the research project code. Format: X-NNN-XX",
            'SHOP_PRICE': "Read the medal price shown. Return only the number.",
            'FLEET_POWER': "Read the fleet power number. No commas.",
            'DORM_FOOD': "Read the food counter. Format: CURRENT/MAXIMUM",
            'OCR_DORM_FOOD': "Read the food amount number shown. Return only the number, no text.",
            'SOS_CHAPTER': "Read the chapter number (3-10). Return only the number.",
            'STAGE_NAME': "Read the stage name. Examples: 7-2, D3, SP3",
        }
        
        # Check if button name contains any key
        for key, prompt in prompts.items():
            if key in button_name.upper():
                return prompt
                
        # Default prompt
        return "Read any text in this image from Azur Lane. Return only the text, no explanation."
    
    def _get_vision_prompt_with_area(self, button_name, button_area, idx=0, total=1):
        """Get appropriate prompt based on OCR context"""
        # Different prompts for different OCR use cases
        if 'DORM_FOOD' in button_name:
            # For dorm food, specify which food item (1-indexed for clarity)
            position = idx + 1
            return f"""Looking at this Azur Lane dorm feeding screen, there are {total} food items in a row.
Read the amount number for food item #{position} (counting from left to right).
Return ONLY the numeric value. Examples: 0, 5, 100, 1000, 5000
If empty or no number visible, return: 0"""
        
        elif 'DORM_FILL' in button_name or 'OCR_FILL' in button_name:
            return """Looking at this Azur Lane dorm screen, read the happiness/fill counter shown as CURRENT/MAXIMUM.
Return in format: NUMBER/NUMBER
Example: 119/119 or 50/150"""
        
        elif 'DORM_SLOT' in button_name or 'OCR_SLOT' in button_name:
            return """Looking at this Azur Lane dorm screen, read the ship slot counter shown as CURRENT/MAXIMUM.
Return in format: NUMBER/NUMBER
Example: 2/6 or 5/6"""
        
        elif 'COMMISSION' in button_name or 'TIMER' in button_name:
            return """Looking at this Azur Lane screen, read the timer displayed.
Return in format: HH:MM:SS
Example: 02:45:30 or 00:15:45"""
        
        elif 'RESEARCH' in button_name:
            return """Looking at this Azur Lane research screen, read the research project code.
Return the code exactly as shown.
Example: Q-289-MI or S-486-MI"""
        
        elif 'PRICE' in button_name or 'COIN' in button_name:
            return """Looking at this Azur Lane screen, read the price or coin amount.
Return ONLY the number, no currency symbols.
Example: 500 or 15000"""
        
        elif 'STAGE' in button_name:
            return """Looking at this Azur Lane screen, read the stage name.
Return the stage identifier.
Examples: 7-2, D3, SP3, 13-4"""
        
        else:
            # Generic prompt for other cases
            return """Looking at this Azur Lane screen, read the text or number displayed.
Return ONLY what you see, no explanations."""


class Digit(Ocr):
    def ocr(self, image, direct_ocr=False):
        """
        Do OCR on a digit/number and return parsed integer values.
        
        Returns:
            For single button: int
            For multiple buttons: list[int]
        """
        result = super().ocr(image, direct_ocr=direct_ocr)
        
        # Handle single result
        if isinstance(result, str):
            return self._parse_digit(result)
        
        # Handle multiple results
        if isinstance(result, list):
            return [self._parse_digit(r) for r in result]
        
        # Fallback
        return 0
    
    def _parse_digit(self, text):
        """
        Parse text into integer, handling common OCR errors.
        """
        if not text:
            logger.warning(f"Digit: Empty text, returning 0")
            return 0
        
        # Clean the text - keep only digits
        cleaned = re.sub(r'[^0-9]', '', str(text))
        
        if not cleaned:
            logger.warning(f"Digit: No digits found in '{text}', returning 0")
            return 0
        
        try:
            return int(cleaned)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Digit: Failed to parse '{text}' -> '{cleaned}': {e}")
            return 0


class DigitCounter(Digit):
    """OCR class for counters like '3/6' that returns parsed values"""
    
    def ocr(self, image, direct_ocr=False):
        """
        Do OCR on a counter format like '3/6' and return parsed values.
        
        Returns:
            For single button: tuple of (current, _, total)
            For multiple buttons: list of tuples
        """
        result = super().ocr(image, direct_ocr=direct_ocr)
        
        # Handle single result
        if isinstance(result, str):
            return self._parse_counter(result)
        
        # Handle multiple results
        if isinstance(result, list):
            return [self._parse_counter(r) for r in result]
        
        # Fallback
        return (0, 0, 0)
    
    def _parse_counter(self, text):
        """
        Parse counter text like '3/6' into (current, 0, total) format.
        The middle value is always 0 for compatibility.
        """
        if not text:
            logger.warning(f"DigitCounter: Empty text")
            return (0, 0, 0)
            
        # First, try to find a pattern like "X/Y" anywhere in the text
        import re
        match = re.search(r'(\d+)\s*/\s*(\d+)', str(text))
        if match:
            try:
                current = int(match.group(1))
                total = int(match.group(2))
                return (current, 0, total)
            except (ValueError, AttributeError) as e:
                logger.warning(f"DigitCounter: Failed to parse matched pattern from '{text}': {e}")
                return (0, 0, 0)
        
        # If no slash pattern found, log a shorter version of the text
        text_preview = str(text)[:100] + '...' if len(str(text)) > 100 else str(text)
        logger.warning(f"DigitCounter: No X/Y pattern found in '{text_preview}'")
        return (0, 0, 0)


class OcrYuv(Ocr):
    """Base class for YUV-based OCR (deprecated)"""

    pass


class DigitYuv(Digit, OcrYuv):
    pass


class DigitCounterYuv(DigitCounter, OcrYuv):
    """YUV version of DigitCounter"""
    pass


class Duration(Ocr):
    def __init__(self, buttons, letter=(255, 255, 255), threshold=128, alphabet="0123456789:IDSB", name=None):
        super().__init__(buttons, letter=letter, threshold=threshold, alphabet=alphabet, name=name)

    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace("I", "1").replace("D", "0").replace("S", "5")
        result = result.replace("B", "8")
        return result

    def ocr(self, image, direct_ocr=False):
        """
        Do OCR on a duration, such as `01:30:00`.

        Args:
            image:
            direct_ocr:

        Returns:
            list, datetime.timedelta: timedelta object, or a list of it.
        """
        result_list = super().ocr(image, direct_ocr=direct_ocr)
        if not isinstance(result_list, list):
            result_list = [result_list]
        result_list = [self.parse_time(result) for result in result_list]
        if len(self.buttons) == 1:
            result_list = result_list[0]
        return result_list

    @staticmethod
    def parse_time(string):
        """
        Args:
            string (str): `01:30:00`

        Returns:
            datetime.timedelta:
        """
        # Log what we're trying to parse for debugging
        logger.info(f"Duration.parse_time() received: '{string[:50]}...' (length: {len(string)})")
        
        # Try to find any time-like patterns in the string
        all_matches = re.findall(r"(\d{1,2}):(\d{2}):?(\d{2})", string)
        if all_matches:
            logger.info(f"Found time patterns: {all_matches}")
            # Use the first valid match
            result = [int(s) for s in all_matches[0]]
            # Record success - reset error counter
            if OCR_ERROR_COUNTER:
                OCR_ERROR_COUNTER.record_success("ocr_duration")
            return timedelta(hours=result[0], minutes=result[1], seconds=result[2])
        
        # Also try patterns with dots or other separators
        alt_matches = re.findall(r"(\d{1,2})[.:,](\d{2})[.:,]?(\d{2})", string)
        if alt_matches:
            logger.info(f"Found alternative time patterns: {alt_matches}")
            result = [int(s) for s in alt_matches[0]]
            # Record success - reset error counter
            if OCR_ERROR_COUNTER:
                OCR_ERROR_COUNTER.record_success("ocr_duration")
            return timedelta(hours=result[0], minutes=result[1], seconds=result[2])
            
        # No valid time pattern found - record error
        error_msg = f"No time pattern found in OCR result: {string[:100]}..."
        try:
            if OCR_ERROR_COUNTER:
                OCR_ERROR_COUNTER.record_error("ocr_duration", error_msg)
            # If we're still under the threshold, return zero duration
            logger.warning(f"Invalid duration - returning zero timedelta")
            return timedelta(hours=0, minutes=0, seconds=0)
        except Exception as e:
            # Max errors exceeded - stop the bot
            logger.error("Maximum OCR parsing failures exceeded - stopping bot")
            raise


class DurationYuv(Duration, OcrYuv):
    pass
