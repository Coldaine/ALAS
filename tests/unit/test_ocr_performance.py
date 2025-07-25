"""
Performance and benchmark tests for ALAS OCR system.
Tests response times, memory usage, and concurrent operations.
"""
import numpy as np
import pytest
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add ALAS root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.performance
class TestOCRPerformance:
    """Performance tests for OCR operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        from module.ocr.ocr import OCR_MODEL
        from module.ocr.al_ocr import AlOcr
        
        self.ocr_model = OCR_MODEL
        self.alocr = AlOcr()
        
        # Standard test images
        self.small_image = np.ones((50, 100, 3), dtype=np.uint8) * 255
        self.medium_image = np.ones((100, 200, 3), dtype=np.uint8) * 255
        self.large_image = np.ones((200, 400, 3), dtype=np.uint8) * 255
    
    def test_single_ocr_performance(self):
        """Test performance of single OCR operation."""
        start_time = time.time()
        result = self.ocr_model.ocr([self.medium_image], cls=True)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"Single OCR operation took: {duration:.3f} seconds")
        
        # Should complete within reasonable time (allow for EasyOCR initialization)
        assert duration < 15.0, f"OCR took too long: {duration:.3f}s"
        assert isinstance(result, list)
    
    def test_multiple_ocr_performance(self):
        """Test performance of multiple sequential OCR operations."""
        num_operations = 5
        durations = []
        
        for i in range(num_operations):
            start_time = time.time()
            result = self.alocr.ocr(self.small_image)
            end_time = time.time()
            
            duration = end_time - start_time
            durations.append(duration)
            assert isinstance(result, str)
        
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        
        print(f"Average OCR duration: {avg_duration:.3f}s")
        print(f"Maximum OCR duration: {max_duration:.3f}s")
        
        # After first call, subsequent calls should be faster (models loaded)
        assert max_duration < 5.0, f"Individual OCR too slow: {max_duration:.3f}s"
        assert avg_duration < 2.0, f"Average OCR too slow: {avg_duration:.3f}s"
    
    def test_batch_ocr_performance(self):
        """Test performance of batch OCR operations."""
        images = [self.small_image] * 3
        
        start_time = time.time()
        result = self.ocr_model.ocr(images, cls=True)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"Batch OCR (3 images) took: {duration:.3f} seconds")
        
        assert duration < 10.0, f"Batch OCR took too long: {duration:.3f}s"
        assert isinstance(result, list)
        assert len(result) == 3
    
    def test_different_image_sizes(self):
        """Test performance with different image sizes."""
        test_cases = [
            ("Small (50x100)", self.small_image),
            ("Medium (100x200)", self.medium_image),
            ("Large (200x400)", self.large_image),
        ]
        
        for name, image in test_cases:
            start_time = time.time()
            result = self.alocr.ocr(image)
            end_time = time.time()
            
            duration = end_time - start_time
            print(f"{name} image OCR took: {duration:.3f} seconds")
            
            # Larger images may take longer but should still be reasonable
            max_time = 5.0 if "Large" in name else 3.0
            assert duration < max_time, f"{name} OCR too slow: {duration:.3f}s"
            assert isinstance(result, str)
    
    @pytest.mark.slow
    def test_concurrent_ocr_operations(self):
        """Test concurrent OCR operations."""
        def ocr_task(task_id):
            """Single OCR task for concurrent execution."""
            start_time = time.time()
            result = self.alocr.ocr(self.small_image)
            end_time = time.time()
            return task_id, end_time - start_time, result
        
        num_workers = 3
        num_tasks = 6
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(ocr_task, i) for i in range(num_tasks)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        print(f"Concurrent OCR ({num_tasks} tasks, {num_workers} workers) took: {total_duration:.3f} seconds")
        
        # Check all tasks completed
        assert len(results) == num_tasks
        
        # Check individual task performance
        task_durations = [duration for _, duration, _ in results]
        avg_task_duration = sum(task_durations) / len(task_durations)
        max_task_duration = max(task_durations)
        
        print(f"Average task duration: {avg_task_duration:.3f}s")
        print(f"Maximum task duration: {max_task_duration:.3f}s")
        
        # Concurrent operations should not be dramatically slower
        assert max_task_duration < 8.0, f"Concurrent task too slow: {max_task_duration:.3f}s"
        assert total_duration < 15.0, f"Total concurrent time too long: {total_duration:.3f}s"
    
    def test_memory_usage_stability(self):
        """Test that OCR operations don't cause memory leaks."""
        import psutil
        import gc
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform many OCR operations
        for i in range(10):
            result = self.alocr.ocr(self.medium_image)
            assert isinstance(result, str)
            
            # Force garbage collection
            gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Initial memory: {initial_memory:.1f} MB")
        print(f"Final memory: {final_memory:.1f} MB")
        print(f"Memory increase: {memory_increase:.1f} MB")
        
        # Allow for some memory increase but not excessive
        assert memory_increase < 100.0, f"Excessive memory increase: {memory_increase:.1f} MB"


@pytest.mark.performance
class TestAlOcrPerformance:
    """Performance tests specific to AlOcr methods."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        from module.ocr.al_ocr import AlOcr
        self.ocr = AlOcr()
        self.test_image = np.ones((100, 200, 3), dtype=np.uint8) * 255
        self.test_images = [self.test_image] * 3
    
    def test_ocr_for_single_lines_performance(self):
        """Test performance of ocr_for_single_lines method."""
        start_time = time.time()
        results = self.ocr.ocr_for_single_lines(self.test_images)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"ocr_for_single_lines (3 images) took: {duration:.3f} seconds")
        
        assert duration < 8.0, f"ocr_for_single_lines too slow: {duration:.3f}s"
        assert isinstance(results, list)
        assert len(results) == 3
        assert all(isinstance(r, str) for r in results)
    
    def test_atomic_ocr_performance(self):
        """Test performance of atomic OCR methods."""
        start_time = time.time()
        results = self.ocr.atomic_ocr_for_single_lines(self.test_images)
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"atomic_ocr_for_single_lines (3 images) took: {duration:.3f} seconds")
        
        assert duration < 8.0, f"atomic_ocr_for_single_lines too slow: {duration:.3f}s"
        assert isinstance(results, list)
        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)  # Character lists
    
    def test_legacy_method_performance_comparison(self):
        """Compare performance of different AlOcr methods."""
        methods = [
            ("ocr", lambda: self.ocr.ocr(self.test_image)),
            ("ocr_for_single_line", lambda: self.ocr.ocr_for_single_line(self.test_image)),
            ("atomic_ocr", lambda: self.ocr.atomic_ocr(self.test_image)),
            ("atomic_ocr_for_single_line", lambda: self.ocr.atomic_ocr_for_single_line(self.test_image)),
        ]
        
        performance_results = {}
        
        for method_name, method_func in methods:
            start_time = time.time()
            result = method_func()
            end_time = time.time()
            
            duration = end_time - start_time
            performance_results[method_name] = duration
            
            print(f"{method_name} took: {duration:.3f} seconds")
            assert isinstance(result, str)
            assert duration < 5.0, f"{method_name} too slow: {duration:.3f}s"
        
        # All methods should have similar performance (they use the same backend)
        durations = list(performance_results.values())
        max_duration = max(durations)
        min_duration = min(durations)
        
        # Allow for some variance but not dramatic differences
        assert max_duration / min_duration < 3.0, "Large performance variance between methods"


if __name__ == '__main__':
    # Run performance tests when script is executed directly
    pytest.main([__file__, '-v', '-m', 'performance'])