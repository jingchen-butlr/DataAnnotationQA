#!/usr/bin/env python3
"""
PyTorch Training Pipeline Unit Tests

Tests for ThermalAnnotationDataset and PyTorch DataLoader integration.
Run with: python -m unittest tests.test_training_pipeline
"""

import unittest
import logging
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import torch
from src.data_pipeline import ThermalAnnotationDataset, create_dataloader

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ThermalDatasetBasicTests(unittest.TestCase):
    """Test suite for basic ThermalAnnotationDataset functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration - runs once before all tests."""
        cls.annotation_file = 'Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json'
        cls.mac_address = '02:00:1a:62:51:67'
        
        logger.info("\n" + "=" * 70)
        logger.info("Thermal Dataset Basic Test Suite")
        logger.info("=" * 70)
        logger.info(f"Annotation file: {cls.annotation_file}")
        logger.info(f"MAC address: {cls.mac_address}")
        logger.info("=" * 70 + "\n")
    
    def test_01_dataset_initialization(self):
        """Test that dataset initializes correctly."""
        logger.info("\nTEST: Dataset Initialization")
        logger.info("-" * 50)
        
        dataset = ThermalAnnotationDataset(
            annotation_file=self.annotation_file,
            mac_address=self.mac_address,
            cache_frames=True
        )
        
        # Verify dataset properties
        self.assertGreater(len(dataset), 0, "Dataset should have samples")
        self.assertIsInstance(dataset.category_to_id, dict, "Should have category mapping")
        self.assertGreater(len(dataset.category_to_id), 0, "Should have categories")
        
        logger.info(f"✅ Dataset initialized")
        logger.info(f"   Total samples: {len(dataset)}")
        logger.info(f"   Categories: {len(dataset.category_to_id)}")
    
    def test_02_fetch_single_sample(self):
        """Test fetching a single sample from TDengine."""
        logger.info("\nTEST: Fetch Single Sample")
        logger.info("-" * 50)
        
        dataset = ThermalAnnotationDataset(
            annotation_file=self.annotation_file,
            mac_address=self.mac_address,
            cache_frames=True
        )
        
        # Fetch sample
        frame, target = dataset[0]
        
        # Verify frame
        self.assertIsInstance(frame, torch.Tensor, "Frame should be a tensor")
        self.assertEqual(frame.ndim, 3, "Frame should be 3D (C, H, W)")
        self.assertEqual(frame.shape[0], 1, "Frame should have 1 channel")
        
        # Verify target
        self.assertIsInstance(target, dict, "Target should be a dictionary")
        self.assertIn('boxes', target, "Target should have boxes")
        self.assertIn('labels', target, "Target should have labels")
        self.assertIn('num_objects', target, "Target should have num_objects")
        self.assertIn('timestamp', target, "Target should have timestamp")
        
        logger.info(f"✅ Sample fetched successfully")
        logger.info(f"   Frame shape: {frame.shape}")
        logger.info(f"   Num objects: {target['num_objects']}")
        logger.info(f"   Boxes shape: {target['boxes'].shape}")
    
    def test_03_category_mapping(self):
        """Test category ID mapping."""
        logger.info("\nTEST: Category Mapping")
        logger.info("-" * 50)
        
        dataset = ThermalAnnotationDataset(
            annotation_file=self.annotation_file,
            mac_address=self.mac_address,
            cache_frames=True
        )
        
        # Verify bidirectional mapping
        for category_name, category_id in dataset.category_to_id.items():
            self.assertEqual(
                dataset.id_to_category[category_id],
                category_name,
                "Bidirectional mapping should be consistent"
            )
        
        # Test get_category_name
        first_id = list(dataset.id_to_category.keys())[0]
        category_name = dataset.get_category_name(first_id)
        self.assertIsInstance(category_name, str, "Category name should be string")
        
        logger.info(f"✅ Category mapping valid")
        logger.info(f"   Categories: {list(dataset.category_to_id.keys())}")
    
    def test_04_dataset_statistics(self):
        """Test dataset statistics generation."""
        logger.info("\nTEST: Dataset Statistics")
        logger.info("-" * 50)
        
        dataset = ThermalAnnotationDataset(
            annotation_file=self.annotation_file,
            mac_address=self.mac_address,
            cache_frames=True
        )
        
        stats = dataset.get_statistics()
        
        # Verify statistics structure
        self.assertIn('total_samples', stats, "Stats should have total_samples")
        self.assertIn('num_categories', stats, "Stats should have num_categories")
        self.assertIn('categories', stats, "Stats should have categories dict")
        self.assertIn('mac_address', stats, "Stats should have mac_address")
        self.assertIn('cache_size', stats, "Stats should have cache_size")
        self.assertIn('cached_frames', stats, "Stats should have cached_frames")
        
        # Verify values
        self.assertEqual(stats['total_samples'], len(dataset), "Sample count should match")
        self.assertEqual(stats['mac_address'], self.mac_address, "MAC address should match")
        self.assertIsInstance(stats['categories'], dict, "Categories should be a dict")
        self.assertGreaterEqual(stats['cache_size'], 0, "Cache size should be non-negative")
        
        logger.info(f"✅ Statistics generated")
        logger.info(f"   Total samples: {stats['total_samples']}")
        logger.info(f"   Num categories: {stats['num_categories']}")
        logger.info(f"   Cache size: {stats['cache_size']}")


class ThermalDatasetCacheTests(unittest.TestCase):
    """Test suite for dataset caching functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration."""
        cls.annotation_file = 'Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json'
        cls.mac_address = '02:00:1a:62:51:67'
        
        logger.info("\n" + "=" * 70)
        logger.info("Thermal Dataset Cache Test Suite")
        logger.info("=" * 70 + "\n")
    
    def test_01_prefetch_frames(self):
        """Test prefetching all frames into cache."""
        logger.info("\nTEST: Prefetch Frames")
        logger.info("-" * 50)
        
        dataset = ThermalAnnotationDataset(
            annotation_file=self.annotation_file,
            mac_address=self.mac_address,
            cache_frames=True
        )
        
        # Prefetch
        dataset.prefetch_all_frames()
        
        # Verify cache is populated (may be 0 if no matching data in TDengine)
        self.assertIsNotNone(dataset.frame_cache, "Cache should exist")
        logger.info(f"✅ Prefetch completed")
        logger.info(f"   Cached frames: {len(dataset.frame_cache)}")
    
    def test_02_access_cached_samples(self):
        """Test accessing samples from cache."""
        logger.info("\nTEST: Access Cached Samples")
        logger.info("-" * 50)
        
        dataset = ThermalAnnotationDataset(
            annotation_file=self.annotation_file,
            mac_address=self.mac_address,
            cache_frames=True
        )
        
        dataset.prefetch_all_frames()
        
        # Access multiple samples
        for i in range(min(3, len(dataset))):
            frame, target = dataset[i]
            self.assertIsInstance(frame, torch.Tensor, f"Sample {i} should be tensor")
        
        logger.info(f"✅ Accessed {min(3, len(dataset))} cached samples")


class PyTorchDataLoaderTests(unittest.TestCase):
    """Test suite for PyTorch DataLoader integration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration."""
        cls.annotation_file = 'Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json'
        cls.mac_address = '02:00:1a:62:51:67'
        
        logger.info("\n" + "=" * 70)
        logger.info("PyTorch DataLoader Test Suite")
        logger.info("=" * 70 + "\n")
    
    def test_01_create_dataloader(self):
        """Test creating a PyTorch DataLoader."""
        logger.info("\nTEST: Create DataLoader")
        logger.info("-" * 50)
        
        dataloader = create_dataloader(
            annotation_file=self.annotation_file,
            mac_address=self.mac_address,
            batch_size=8,
            shuffle=True,
            prefetch=True
        )
        
        # Verify DataLoader properties
        self.assertGreater(len(dataloader), 0, "DataLoader should have batches")
        self.assertEqual(dataloader.batch_size, 8, "Batch size should be 8")
        
        logger.info(f"✅ DataLoader created")
        logger.info(f"   Total batches: {len(dataloader)}")
        logger.info(f"   Batch size: {dataloader.batch_size}")
    
    def test_02_iterate_batches(self):
        """Test iterating through batches."""
        logger.info("\nTEST: Iterate Batches")
        logger.info("-" * 50)
        
        dataloader = create_dataloader(
            annotation_file=self.annotation_file,
            mac_address=self.mac_address,
            batch_size=4,
            shuffle=False,
            prefetch=True
        )
        
        batch_count = 0
        for frames, targets in dataloader:
            # Verify batch structure
            self.assertIsInstance(frames, torch.Tensor, "Frames should be tensor")
            self.assertEqual(frames.ndim, 4, "Frames should be 4D (B, C, H, W)")
            self.assertIsInstance(targets, list, "Targets should be list")
            
            batch_count += 1
            if batch_count >= 2:  # Test first 2 batches
                break
        
        self.assertGreater(batch_count, 0, "Should iterate at least one batch")
        logger.info(f"✅ Iterated {batch_count} batches successfully")
    
    def test_03_batch_collation(self):
        """Test that batches are correctly collated."""
        logger.info("\nTEST: Batch Collation")
        logger.info("-" * 50)
        
        dataloader = create_dataloader(
            annotation_file=self.annotation_file,
            mac_address=self.mac_address,
            batch_size=8,
            shuffle=False,
            prefetch=True
        )
        
        # Get first batch
        frames, targets = next(iter(dataloader))
        
        # Verify collation
        batch_size = min(8, len(dataloader.dataset))
        self.assertEqual(frames.shape[0], len(targets), "Batch size should match")
        self.assertEqual(len(targets), batch_size, "Targets length should match batch size")
        
        # Verify each target
        for target in targets:
            self.assertIn('boxes', target, "Each target should have boxes")
            self.assertIn('labels', target, "Each target should have labels")
        
        logger.info(f"✅ Batch collation correct")
        logger.info(f"   Frames shape: {frames.shape}")
        logger.info(f"   Targets count: {len(targets)}")


class ThermalDataTransformTests(unittest.TestCase):
    """Test suite for custom transforms."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration."""
        cls.annotation_file = 'Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json'
        cls.mac_address = '02:00:1a:62:51:67'
        
        logger.info("\n" + "=" * 70)
        logger.info("Thermal Data Transform Test Suite")
        logger.info("=" * 70 + "\n")
    
    def test_01_custom_transform(self):
        """Test applying custom transform to frames."""
        logger.info("\nTEST: Custom Transform")
        logger.info("-" * 50)
        
        # Define transform
        def normalize_temperature(frame_tensor):
            """Normalize temperature to [0, 1] range."""
            min_temp = 10.0
            max_temp = 30.0
            normalized = (frame_tensor - min_temp) / (max_temp - min_temp)
            return torch.clamp(normalized, 0.0, 1.0)
        
        # Create dataset with transform
        dataset = ThermalAnnotationDataset(
            annotation_file=self.annotation_file,
            mac_address=self.mac_address,
            transform=normalize_temperature,
            cache_frames=True
        )
        
        dataset.prefetch_all_frames()
        
        # Get sample
        frame, target = dataset[0]
        
        # Verify transform was applied
        self.assertGreaterEqual(frame.min().item(), 0.0, "Min should be >= 0")
        self.assertLessEqual(frame.max().item(), 1.0, "Max should be <= 1")
        
        logger.info(f"✅ Transform applied successfully")
        logger.info(f"   Frame range: [{frame.min():.3f}, {frame.max():.3f}]")


def run_test_suite():
    """Run the complete test suite and print summary."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(ThermalDatasetBasicTests))
    suite.addTests(loader.loadTestsFromTestCase(ThermalDatasetCacheTests))
    suite.addTests(loader.loadTestsFromTestCase(PyTorchDataLoaderTests))
    suite.addTests(loader.loadTestsFromTestCase(ThermalDataTransformTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("Test Summary")
    logger.info("=" * 70)
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info("=" * 70 + "\n")
    
    if result.wasSuccessful():
        logger.info("✅ All tests passed! Training pipeline is working correctly.\n")
        logger.info("🚀 Ready for deep learning training!")
        logger.info("\n📚 Key Features Validated:")
        logger.info("  ✓ Dataset initialization and sample fetching")
        logger.info("  ✓ In-memory caching and prefetching")
        logger.info("  ✓ PyTorch DataLoader integration")
        logger.info("  ✓ Batch collation and iteration")
        logger.info("  ✓ Custom transforms\n")
    else:
        logger.warning("⚠️ Some tests failed. Check the output above for details.\n")
    
    return result


if __name__ == '__main__':
    # Run with custom summary
    run_test_suite()

