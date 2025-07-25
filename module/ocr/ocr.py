import time
from datetime import timedelta
from typing import TYPE_CHECKING

import module.config.server as server
from module.base.button import Button
from module.base.decorator import cached_property
from module.base.utils import *
from module.logger import logger
from module.ocr.rpc import ModelProxyFactory
from module.webui.setting import State
# OCR backend with PaddleOCR interface compatibility
try:
    from paddleocr import PaddleOCR
    # Initialize PaddleOCR with optimized settings for ALAS
    OCR_MODEL = PaddleOCR(use_angle_cls=True, lang='en', show_log=False, use_gpu=False)
    logger.info('Using PaddleOCR backend for OCR functionality.')
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
            np.ndarray: Shape (width, height)
        """
        image = extract_letters(image, letter=self.letter, threshold=self.threshold)

        return image.astype(np.uint8)

    def after_process(self, result):
        """
        Args:
            result (str): '第二行'

        Returns:
            str:
        """
        return result

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

        result_list = []
        try:
            # Pre-process
            if not direct_ocr:
                image_list = [self.pre_process(img) for img in image_list]

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


class Digit(Ocr):
    pass


class DigitCounter(Digit):
    pass


class OcrYuv(Ocr):
    """Base class for YUV-based OCR (deprecated)"""

    pass


class DigitYuv(Digit, OcrYuv):
    pass


class DigitCounterYuv(DigitCounter, OcrYuv):
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
        result = re.search(r"(\d{1,2}):?(\d{2}):?(\d{2})", string)
        if result:
            result = [int(s) for s in result.groups()]
            return timedelta(hours=result[0], minutes=result[1], seconds=result[2])
        else:
            logger.warning(f"Invalid duration: {string}")
            return timedelta(hours=0, minutes=0, seconds=0)


class DurationYuv(Duration, OcrYuv):
    pass
