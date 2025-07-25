"""
Comprehensive test suite for ALAS OCR system.
Tests PaddleOCR interface compatibility, backend fallbacks, and integration.
"""
import numpy as np
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add ALAS root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestOCRBackendDetection:
    """Test OCR backend detection and initialization."""
    
    def test_import_ocr_model(self):
        """Test that OCR_MODEL can be imported successfully."""
        from module.ocr.ocr import OCR_MODEL
        assert OCR_MODEL is not None
        assert hasattr(OCR_MODEL, 'ocr')
        assert hasattr(OCR_MODEL, 'close')
    
    def test_ocr_model_type(self):
        """Test the type of OCR_MODEL based on available backends."""
        from module.ocr.ocr import OCR_MODEL
        
        # Should be either PaddleOCR or PaddleOCRCompatWrapper or MinimalPaddleOCR
        valid_types = ['PaddleOCR', 'PaddleOCRCompatWrapper', 'MinimalPaddleOCR']
        assert type(OCR_MODEL).__name__ in valid_types
    
    @patch('module.ocr.ocr.PaddleOCR', side_effect=ImportError())
    @patch('module.ocr.ocr.easyocr')
    def test_easyocr_fallback(self, mock_easyocr):
        """Test fallback to EasyOCR when PaddleOCR is not available."""
        # Mock EasyOCR Reader
        mock_reader = Mock()
        mock_easyocr.Reader.return_value = mock_reader
        
        # Re-import to trigger fallback logic
        import importlib
        import module.ocr.ocr
        importlib.reload(module.ocr.ocr)
        
        assert type(module.ocr.ocr.OCR_MODEL).__name__ == 'PaddleOCRCompatWrapper'
    
    @patch('module.ocr.ocr.PaddleOCR', side_effect=ImportError())
    @patch('module.ocr.ocr.easyocr', side_effect=ImportError())
    def test_minimal_fallback(self):
        """Test fallback to minimal OCR when both PaddleOCR and EasyOCR are unavailable."""
        # Re-import to trigger minimal fallback
        import importlib
        import module.ocr.ocr
        importlib.reload(module.ocr.ocr)
        
        assert type(module.ocr.ocr.OCR_MODEL).__name__ == 'MinimalPaddleOCR'


class TestPaddleOCRInterface:
    """Test PaddleOCR interface compatibility."""
    
    def setUp(self):
        from module.ocr.ocr import OCR_MODEL
        self.ocr = OCR_MODEL
    
    def test_ocr_method_signature(self):
        """Test that OCR method accepts PaddleOCR parameters."""
        from module.ocr.ocr import OCR_MODEL
        
        # Create test image
        test_image = np.ones((50, 100, 3), dtype=np.uint8) * 255
        
        # Test single image
        result = OCR_MODEL.ocr(test_image, cls=True)
        assert isinstance(result, list)
        
        # Test image list
        result = OCR_MODEL.ocr([test_image], cls=True)
        assert isinstance(result, list)
        assert len(result) == 1
    
    def test_ocr_return_format(self):
        """Test that OCR returns PaddleOCR-compatible format."""
        from module.ocr.ocr import OCR_MODEL
        
        test_image = np.ones((50, 100, 3), dtype=np.uint8) * 255
        result = OCR_MODEL.ocr([test_image], cls=True)
        
        # Should return list of results, one per image
        assert isinstance(result, list)
        assert len(result) == 1
        
        # Each result should be None (no text) or list of detections
        image_result = result[0]
        assert image_result is None or isinstance(image_result, list)
        
        # If detections exist, each should be [box, (text, confidence)]
        if image_result:
            for detection in image_result:
                assert len(detection) == 2
                box, text_info = detection
                assert isinstance(box, list)  # Bounding box coordinates
                assert isinstance(text_info, tuple) and len(text_info) == 2  # (text, confidence)
    
    def test_close_method(self):
        """Test that close method exists and works."""
        from module.ocr.ocr import OCR_MODEL
        
        # Should not raise an exception
        OCR_MODEL.close()
    
    def test_ocr_with_different_image_sizes(self):
        """Test OCR with various image sizes."""
        from module.ocr.ocr import OCR_MODEL
        
        # Test different image sizes
        test_cases = [
            (50, 100, 3),    # Small image
            (100, 200, 3),   # Medium image
            (20, 20, 3),     # Tiny image
        ]
        
        for height, width, channels in test_cases:
            test_image = np.ones((height, width, channels), dtype=np.uint8) * 255
            result = OCR_MODEL.ocr([test_image], cls=True)
            assert isinstance(result, list)
            assert len(result) == 1


class TestAlOcrIntegration:
    """Test AlOcr class functionality."""
    
    def test_alocr_import(self):
        """Test that AlOcr can be imported."""
        from module.ocr.al_ocr import AlOcr
        assert AlOcr is not None
    
    def test_alocr_initialization(self):
        """Test AlOcr initialization with different parameters."""
        from module.ocr.al_ocr import AlOcr
        
        # Test default initialization
        ocr = AlOcr()
        assert ocr.name == 'azur_lane'
        
        # Test with custom name
        ocr = AlOcr(name='test_model')
        assert ocr.name == 'test_model'
    
    def test_alocr_ocr_method(self):
        """Test AlOcr ocr method."""
        from module.ocr.al_ocr import AlOcr
        
        ocr = AlOcr()
        test_image = np.ones((50, 100, 3), dtype=np.uint8) * 255
        
        result = ocr.ocr(test_image)
        assert isinstance(result, str)
    
    def test_alocr_legacy_methods(self):
        """Test AlOcr legacy method compatibility."""
        from module.ocr.al_ocr import AlOcr
        
        ocr = AlOcr()
        test_image = np.ones((50, 100, 3), dtype=np.uint8) * 255
        test_images = [test_image, test_image]
        
        # Test ocr_for_single_line
        result = ocr.ocr_for_single_line(test_image)
        assert isinstance(result, str)
        
        # Test ocr_for_single_lines
        results = ocr.ocr_for_single_lines(test_images)
        assert isinstance(results, list)
        assert len(results) == 2
        
        # Test atomic_ocr_for_single_lines
        results = ocr.atomic_ocr_for_single_lines(test_images)
        assert isinstance(results, list)
        assert len(results) == 2
        assert all(isinstance(r, list) for r in results)  # Should be character lists
        
        # Test set_cand_alphabet (should not crash)
        ocr.set_cand_alphabet("ABC123")
        
        # Test atomic_ocr
        result = ocr.atomic_ocr(test_image)
        assert isinstance(result, str)
        
        # Test debug (should not crash)
        ocr.debug(test_images)


class TestModelsFactory:
    """Test OCR models factory pattern."""
    
    def test_models_import(self):
        """Test that models can be imported."""
        from module.ocr.models import OCR_MODEL
        assert OCR_MODEL is not None
    
    def test_factory_methods(self):
        """Test that factory creates AlOcr instances."""
        from module.ocr.models import OCR_MODEL
        
        # Test different model types
        models_to_test = ['azur_lane', 'azur_lane_jp', 'cnocr', 'jp', 'tw']
        
        for model_name in models_to_test:
            model = getattr(OCR_MODEL, model_name)
            assert model is not None
            assert hasattr(model, 'ocr')
            assert model.name == model_name


class TestErrorHandling:
    """Test error handling and graceful degradation."""
    
    def test_ocr_with_invalid_input(self):
        """Test OCR behavior with invalid inputs."""
        from module.ocr.ocr import OCR_MODEL
        
        # Test with None input
        result = OCR_MODEL.ocr(None, cls=True)
        assert isinstance(result, list)
        
        # Test with empty list
        result = OCR_MODEL.ocr([], cls=True)
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_alocr_with_invalid_input(self):
        """Test AlOcr behavior with invalid inputs."""
        from module.ocr.al_ocr import AlOcr
        
        ocr = AlOcr()
        
        # Test with None input
        result = ocr.ocr(None)
        assert isinstance(result, str)
        
        # Test with invalid image
        result = ocr.ocr(np.array([]))
        assert isinstance(result, str)
    
    def test_backend_failure_handling(self):
        """Test handling of backend failures."""
        from module.ocr.al_ocr import AlOcr
        
        ocr = AlOcr()
        
        # Mock a failure in the backend
        with patch.object(ocr, '_ocr_model') as mock_model:
            mock_model.ocr.side_effect = Exception("Backend failure")
            
            test_image = np.ones((50, 100, 3), dtype=np.uint8) * 255
            result = ocr.ocr(test_image)
            
            # Should return empty string on failure
            assert result == ""


class TestALASIntegration:
    """Integration tests with ALAS modules."""
    
    def test_duration_ocr_import(self):
        """Test that Duration OCR class can be imported and used."""
        from module.ocr.ocr import Duration, Ocr
        
        # Create a Duration OCR instance (like research timers use)
        test_button = (100, 100, 200, 150)  # Mock button area
        duration_ocr = Duration(test_button)
        
        assert hasattr(duration_ocr, 'ocr')
        assert hasattr(duration_ocr, 'parse_time')
    
    def test_digit_ocr_import(self):
        """Test that Digit OCR classes can be imported."""
        from module.ocr.ocr import Digit, DigitCounter
        
        test_button = (100, 100, 200, 150)
        
        digit_ocr = Digit(test_button)
        assert hasattr(digit_ocr, 'ocr')
        
        counter_ocr = DigitCounter(test_button)
        assert hasattr(counter_ocr, 'ocr')
    
    def test_resource_import(self):
        """Test that resource module can import OCR_MODEL."""
        # This tests the import that was causing the original crash
        try:
            from module.base.resource import release_resources
            # Should not raise ImportError
            assert True
        except ImportError as e:
            pytest.fail(f"Resource module import failed: {e}")
    
    def test_research_project_import(self):
        """Test that research project can import OCR classes."""
        try:
            from module.research.project import OCR_RESEARCH
            # Should not raise ImportError
            assert True
        except ImportError as e:
            pytest.fail(f"Research project import failed: {e}")


# Performance and benchmark tests
class TestPerformance:
    """Performance tests for OCR system."""
    
    def test_ocr_performance(self):
        """Basic performance test for OCR operations."""
        from module.ocr.ocr import OCR_MODEL
        import time
        
        test_image = np.ones((100, 200, 3), dtype=np.uint8) * 255
        
        # Time a single OCR operation
        start_time = time.time()
        result = OCR_MODEL.ocr([test_image], cls=True)
        end_time = time.time()
        
        # Should complete within reasonable time (5 seconds for EasyOCR initialization + processing)
        assert end_time - start_time < 10.0
        assert isinstance(result, list)
    
    def test_multiple_ocr_calls(self):
        """Test performance of multiple OCR calls."""
        from module.ocr.al_ocr import AlOcr
        
        ocr = AlOcr()
        test_image = np.ones((50, 100, 3), dtype=np.uint8) * 255
        
        # Multiple calls should not crash and should be reasonably fast
        for i in range(3):
            result = ocr.ocr(test_image)
            assert isinstance(result, str)


if __name__ == '__main__':
    # Run tests when script is executed directly
    pytest.main([__file__, '-v'])