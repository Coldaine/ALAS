"""
This file is part of ALAS (Azur Lane Auto Script).

ALAS is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

ALAS is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ALAS.  If not, see <https://www.gnu.org/licenses/>.
"""
"""
AlOcr implementation using the main OCR system.
This provides a simple interface to the underlying OCR backends.
"""
from module.base.decorator import cached_property
from module.logger import logger

# Use the main OCR system
try:
    from module.ocr.ocr import OCR_MODEL
except ImportError:
    # This should not happen if the main OCR system is properly implemented
    logger.error("Cannot import main OCR system - AlOcr will not function")
    OCR_MODEL = None


class AlOcr:
    """Simple OCR interface using main OCR backend."""
    
    def __init__(self, name='azur_lane', **kwargs):
        """
        Args:
            name (str): Model name (azur_lane, jp, tw, cnocr, etc.)
            **kwargs: Legacy parameters for compatibility
        """
        self.name = name
        self._ocr_model = OCR_MODEL
        
        if OCR_MODEL is None:
            logger.error(f"AlOcr({name}) initialized but no OCR backend available")
    
    def ocr(self, image):
        """
        Perform OCR on image.
        
        Args:
            image (np.ndarray): Input image
            
        Returns:
            str: Recognized text
        """
        if self._ocr_model is None:
            return ""
        
        try:
            # Use the main OCR system with PaddleOCR interface
            results = self._ocr_model.ocr([image], cls=True)
            
            if results and results[0]:
                # Extract text from PaddleOCR format: [[[box], (text, score)], ...]
                text_parts = []
                for detection in results[0]:
                    if len(detection) >= 2 and len(detection[1]) >= 1:
                        text = detection[1][0]  # Get text from (text, score) tuple
                        text_parts.append(text)
                
                return ' '.join(text_parts) if text_parts else ""
            else:
                return ""
                
        except Exception as e:
            logger.warning(f"AlOcr.ocr failed: {e}")
            return ""
    
    def ocr_for_single_line(self, image):
        """OCR optimized for single line text."""
        return self.ocr(image)
    
    def ocr_for_single_lines(self, images):
        """OCR for multiple single-line images."""
        return [self.ocr(img) for img in images]
    
    def atomic_ocr_for_single_lines(self, images, alphabet=None):
        """
        Atomic OCR returning character lists.
        
        Args:
            images: List of images
            alphabet: Character whitelist (ignored for compatibility)
            
        Returns:
            List of character lists
        """
        results = self.ocr_for_single_lines(images)
        return [list(text) for text in results]
    
    def set_cand_alphabet(self, alphabet):
        """Set character whitelist (no-op for compatibility)."""
        pass
    
    def atomic_ocr(self, image, alphabet=None):
        """Atomic OCR with alphabet."""
        return self.ocr(image)
    
    def atomic_ocr_for_single_line(self, image, alphabet=None):
        """Atomic single-line OCR."""
        return self.ocr(image)
    
    def debug(self, images):
        """Debug OCR results."""
        logger.info(f"AlOcr debug: Processing {len(images)} images")
        for i, img in enumerate(images):
            result = self.ocr(img)
            logger.info(f"  Image {i}: '{result}'")