"""
PaddleOCR 3.x wrapper with improved error handling, type safety, and thread safety.
"""
import traceback
from threading import Lock
from typing import List, Optional, Tuple, Union, Any
import numpy as np
import numpy.typing as npt
from module.logger import logger

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    logger.warning("PaddleOCR not available")


# Type aliases for clarity
BoundingBox = List[List[float]]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
OCRResult = Tuple[BoundingBox, Tuple[str, float]]  # (bbox, (text, confidence))
ImageInput = Union[str, npt.NDArray[Any]]


class PaddleOCRv3:
    """
    Thread-safe wrapper for PaddleOCR 3.x with backward compatibility.
    
    This wrapper provides:
    - Backward compatibility with PaddleOCR 2.x API
    - Proper error handling and validation
    - Thread-safe singleton pattern
    - Resource management
    """
    
    def __init__(self, **kwargs):
        """
        Initialize PaddleOCR wrapper.
        
        Args:
            **kwargs: Parameters to pass to PaddleOCR
                lang: Language code (default: 'en')
                ocr_version: OCR model version (e.g., 'PP-OCRv3', 'PP-OCRv4')
                use_gpu: Whether to use GPU (default: False)
                
        Raises:
            ImportError: If PaddleOCR is not installed
            ValueError: If invalid parameters are provided
        """
        if not PADDLEOCR_AVAILABLE:
            raise ImportError("PaddleOCR is not installed. Please install with: pip install paddleocr")
        
        # Validate and filter parameters
        valid_params = self._validate_params(kwargs)
        
        logger.info(f"Initializing PaddleOCR 3.x with params: {valid_params}")
        
        try:
            self.ocr_engine = PaddleOCR(**valid_params)
            self.name = "PaddleOCR_v3"
            self._closed = False
        except Exception as e:
            logger.exception("Failed to initialize PaddleOCR")
            raise RuntimeError(f"PaddleOCR initialization failed: {str(e)}") from e
    
    def _validate_params(self, params: dict) -> dict:
        """Validate and filter initialization parameters."""
        # Known valid parameters for PaddleOCR 3.x
        valid_keys = {
            'lang', 'ocr_version', 'use_gpu', 'show_log',
            'det_model_dir', 'rec_model_dir', 'cls_model_dir',
            'use_angle_cls', 'use_space_char', 'use_mp',
            'total_process_num', 'process_id'
        }
        
        # Filter out unknown parameters
        filtered = {k: v for k, v in params.items() if k in valid_keys and v is not None}
        
        # Validate specific parameters
        if 'lang' in filtered and not isinstance(filtered['lang'], str):
            raise ValueError(f"lang must be a string, got {type(filtered['lang'])}")
            
        if 'ocr_version' in filtered:
            valid_versions = {'PP-OCRv3', 'PP-OCRv4', 'PP-OCRv5'}
            if filtered['ocr_version'] not in valid_versions:
                logger.warning(f"Unknown ocr_version: {filtered['ocr_version']}")
        
        return filtered
    
    def _validate_image_input(self, image: ImageInput) -> ImageInput:
        """Validate single image input."""
        if isinstance(image, str):
            # File path or URL
            return image
        elif isinstance(image, np.ndarray):
            # Numpy array
            if image.ndim not in (2, 3):
                raise ValueError(f"Image array must be 2D or 3D, got {image.ndim}D")
            return image
        else:
            raise TypeError(f"Image must be string path or numpy array, got {type(image)}")
    
    def ocr(self, images: Union[ImageInput, List[ImageInput]], cls: bool = True) -> Union[List[OCRResult], List[List[OCRResult]]]:
        """
        Perform OCR with backward compatible interface.
        
        Args:
            images: Single image or list of images (file paths or numpy arrays)
            cls: Whether to use text angle classification (kept for compatibility)
            
        Returns:
            OCR results in PaddleOCR 2.x format:
            - Single image: List[OCRResult] where OCRResult = (bbox, (text, confidence))
            - Multiple images: List[List[OCRResult]]
            
        Raises:
            TypeError: If images parameter has invalid type
            RuntimeError: If OCR processing fails
            ValueError: If the wrapper has been closed
        """
        if self._closed:
            raise ValueError("PaddleOCRv3 instance has been closed")
        
        # Input validation
        if images is None:
            raise TypeError("images cannot be None")
            
        # Handle single vs multiple images
        if not isinstance(images, list):
            images_list = [images]
            single_image = True
        else:
            images_list = images
            single_image = False
        
        # Validate each image
        validated_images = []
        for i, img in enumerate(images_list):
            try:
                validated_images.append(self._validate_image_input(img))
            except (TypeError, ValueError) as e:
                raise ValueError(f"Invalid image at index {i}: {str(e)}") from e
        
        # Process images
        all_results = []
        for i, img in enumerate(validated_images):
            try:
                result = self._process_single_image(img)
                all_results.append(result)
            except Exception as e:
                logger.error(f"Failed to process image {i}: {str(e)}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                # Append empty result for failed image
                all_results.append([])
        
        # Return appropriate format
        return all_results[0] if single_image else all_results
    
    def _process_single_image(self, img: ImageInput) -> List[OCRResult]:
        """Process a single image and return results in old format."""
        try:
            # Call PaddleOCR 3.x predict method
            result = self.ocr_engine.predict(img)
            
            if not result:
                return []
            
            # Validate result structure
            if not isinstance(result, list) or len(result) == 0:
                logger.warning(f"Unexpected result format: {type(result)}")
                return []
            
            # Extract first result (PaddleOCR returns list with single dict)
            res_dict = result[0]
            if not isinstance(res_dict, dict):
                logger.warning(f"Unexpected result[0] format: {type(res_dict)}")
                return []
            
            # Convert to old format
            return self._convert_result_format(res_dict)
            
        except Exception as e:
            logger.exception(f"Error in PaddleOCR prediction")
            raise RuntimeError(f"OCR prediction failed: {str(e)}") from e
    
    def _convert_result_format(self, res_dict: dict) -> List[OCRResult]:
        """Convert PaddleOCR 3.x result to 2.x format."""
        image_results = []
        
        # Extract required fields with validation
        texts = res_dict.get('rec_texts', [])
        scores = res_dict.get('rec_scores', [])
        polys = res_dict.get('rec_polys', [])
        
        # Validate field lengths
        min_len = min(len(texts), len(scores), len(polys))
        if min_len == 0:
            return []
        
        if len(texts) != len(scores) or len(texts) != len(polys):
            logger.warning(f"Mismatched result lengths: texts={len(texts)}, scores={len(scores)}, polys={len(polys)}")
        
        # Process each detection
        for i in range(min_len):
            bbox = self._convert_bbox(polys[i])
            text = str(texts[i]) if texts[i] is not None else ""
            score = float(scores[i]) if scores[i] is not None else 0.0
            
            if bbox:
                image_results.append([bbox, (text, score)])
        
        return image_results
    
    def _convert_bbox(self, poly: Any) -> Optional[BoundingBox]:
        """Convert polygon to standard bbox format."""
        try:
            # Convert to list if numpy array
            if hasattr(poly, 'tolist'):
                bbox = poly.tolist()
            else:
                bbox = poly
            
            # Validate bbox structure
            if not isinstance(bbox, list) or len(bbox) < 4:
                return None
            
            # Check if already in point format [[x,y], ...]
            if isinstance(bbox[0], (list, tuple)) and len(bbox[0]) == 2:
                return bbox[:4]  # Take first 4 points
            
            # Convert flat array [x1,y1,x2,y2] to points
            if len(bbox) == 4 and all(isinstance(x, (int, float)) for x in bbox):
                return [
                    [bbox[0], bbox[1]], 
                    [bbox[2], bbox[1]], 
                    [bbox[2], bbox[3]], 
                    [bbox[0], bbox[3]]
                ]
            
            # Unknown format
            logger.warning(f"Unknown bbox format: {bbox}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to convert bbox: {e}")
            return None
    
    def close(self) -> None:
        """Clean up resources."""
        if not self._closed:
            self._closed = True
            # PaddleOCR might have internal resources to clean
            if hasattr(self.ocr_engine, 'close'):
                self.ocr_engine.close()
            logger.debug("PaddleOCRv3 instance closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.close()


class PaddleOCRv3Manager:
    """Thread-safe singleton manager for PaddleOCRv3 instances."""
    
    _instances: dict = {}
    _lock = Lock()
    
    @classmethod
    def get_instance(cls, **kwargs) -> PaddleOCRv3:
        """
        Get or create a PaddleOCRv3 instance.
        
        Args:
            **kwargs: Parameters for PaddleOCRv3 initialization
            
        Returns:
            PaddleOCRv3 instance
        """
        # Create a key from kwargs for caching
        key = tuple(sorted(kwargs.items()))
        
        with cls._lock:
            if key not in cls._instances or cls._instances[key]._closed:
                cls._instances[key] = PaddleOCRv3(**kwargs)
            return cls._instances[key]
    
    @classmethod
    def close_all(cls) -> None:
        """Close all managed instances."""
        with cls._lock:
            for instance in cls._instances.values():
                instance.close()
            cls._instances.clear()


def get_paddleocr_v3(**kwargs) -> PaddleOCRv3:
    """
    Get thread-safe PaddleOCR instance.
    
    This is the recommended way to get a PaddleOCRv3 instance,
    as it ensures proper resource management and thread safety.
    """
    return PaddleOCRv3Manager.get_instance(**kwargs)