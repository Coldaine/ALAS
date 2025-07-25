"""
PaddleOCR 3.x wrapper with backward compatibility for ALAS
"""
import numpy as np
from typing import List, Optional, Tuple, Union
from module.logger import logger

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logger.warning("PaddleOCR not available")


class PaddleOCRv3:
    """
    Wrapper for PaddleOCR 3.x that provides backward compatibility
    with the old ocr() method interface expected by ALAS.
    """
    
    def __init__(self, **kwargs):
        if not PADDLEOCR_AVAILABLE:
            raise ImportError("PaddleOCR is not installed")
            
        # Filter out deprecated parameters
        valid_params = {
            'lang': kwargs.get('lang', 'en'),
            'ocr_version': kwargs.get('ocr_version', None),
        }
        
        # Remove None values
        valid_params = {k: v for k, v in valid_params.items() if v is not None}
        
        logger.info(f"Initializing PaddleOCR 3.x with params: {valid_params}")
        self.ocr_engine = PaddleOCR(**valid_params)
        self.name = "PaddleOCR_v3"
        
    def ocr(self, images, cls=True):
        """
        Backward compatible ocr() method that mimics PaddleOCR 2.x interface.
        
        Args:
            images: Single image path, numpy array, or list of images
            cls: Whether to use text angle classification (ignored in v3)
            
        Returns:
            List of results in the old format:
            [[[bbox], (text, confidence)], ...]
        """
        # Ensure images is a list
        if not isinstance(images, list):
            images = [images]
            single_image = True
        else:
            single_image = False
            
        all_results = []
        
        for img in images:
            try:
                # Call the new predict() method
                result = self.ocr_engine.predict(img)
                
                if not result:
                    all_results.append([])
                    continue
                    
                # Convert new format to old format
                image_results = []
                
                # Handle the complex result structure
                if isinstance(result, list) and len(result) > 0:
                    res_dict = result[0]
                    
                    # Extract text and bounding boxes
                    texts = res_dict.get('rec_texts', [])
                    scores = res_dict.get('rec_scores', [])
                    polys = res_dict.get('rec_polys', [])
                    
                    # Combine into old format
                    for i in range(len(texts)):
                        if i < len(polys) and i < len(scores):
                            bbox = polys[i]
                            text = texts[i]
                            score = scores[i]
                            
                            # Convert numpy array to list if needed
                            if hasattr(bbox, 'tolist'):
                                bbox = bbox.tolist()
                            
                            # Old format: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]], (text, score)
                            # The polys are already in the right format for points
                            if len(bbox) >= 4:
                                # PaddleOCR 3.x may return bbox as flat coordinates
                                # Check if it's already point format or needs conversion
                                if len(bbox) == 4 and not isinstance(bbox[0], (list, tuple)):
                                    # Convert [x1, y1, x2, y2] to points
                                    formatted_bbox = [
                                        [bbox[0], bbox[1]], 
                                        [bbox[2], bbox[1]], 
                                        [bbox[2], bbox[3]], 
                                        [bbox[0], bbox[3]]
                                    ]
                                else:
                                    # Already in point format
                                    formatted_bbox = bbox
                                
                                image_results.append([formatted_bbox, (text, float(score))])
                
                all_results.append(image_results)
                
            except Exception as e:
                logger.error(f"Error processing image with PaddleOCR 3.x: {e}")
                all_results.append([])
        
        # Return single result if single image was provided
        if single_image and all_results:
            return all_results[0]
        return all_results
    
    def close(self):
        """Compatibility method - no cleanup needed in v3"""
        pass


# Singleton instance
_ocr_instance = None


def get_paddleocr_v3(**kwargs):
    """Get or create singleton PaddleOCR instance"""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = PaddleOCRv3(**kwargs)
    return _ocr_instance