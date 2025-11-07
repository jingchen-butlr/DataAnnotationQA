#!/usr/bin/env python3
"""
Example Training Pipeline with PyTorch Custom DataLoader

This script demonstrates how to use the ThermalAnnotationDataset for deep learning training.
It fetches thermal data directly from TDengine into memory (no disk files needed).

Reference: https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html
"""

import logging
import torch
from src.data_pipeline import ThermalAnnotationDataset, create_dataloader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """
    Example 1: Basic usage with custom Dataset
    """
    logger.info("=" * 70)
    logger.info("Example 1: Basic Dataset Usage")
    logger.info("=" * 70)
    
    # Create dataset
    dataset = ThermalAnnotationDataset(
        annotation_file='Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json',
        mac_address='02:00:1a:62:51:67',
        cache_frames=True
    )
    
    # Get dataset info
    logger.info(f"\nDataset info:")
    logger.info(f"  Total samples: {len(dataset)}")
    logger.info(f"  Categories: {list(dataset.category_to_id.keys())}")
    
    # Get a single sample (fetches from TDengine)
    logger.info(f"\nFetching sample 0 from TDengine...")
    frame, target = dataset[0]
    
    logger.info(f"\nSample 0:")
    logger.info(f"  Frame shape: {frame.shape}")  # (1, H, W)
    logger.info(f"  Frame dtype: {frame.dtype}")
    logger.info(f"  Temperature range: {frame.min():.1f}°C to {frame.max():.1f}°C")
    logger.info(f"  Num objects: {target['num_objects']}")
    logger.info(f"  Boxes shape: {target['boxes'].shape}")  # (N, 4)
    logger.info(f"  Labels shape: {target['labels'].shape}")  # (N,)
    logger.info(f"  Timestamp: {target['timestamp']}")
    
    # Print object details
    for i, (box, label_id) in enumerate(zip(target['boxes'], target['labels'])):
        category_name = dataset.get_category_name(label_id.item())
        logger.info(f"    Object {i}: {category_name}, bbox: {box.tolist()}")


def example_prefetch_all():
    """
    Example 2: Prefetch all frames for faster training
    """
    logger.info("\n" + "=" * 70)
    logger.info("Example 2: Prefetch All Frames (Recommended for Training)")
    logger.info("=" * 70)
    
    # Create dataset
    dataset = ThermalAnnotationDataset(
        annotation_file='Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json',
        mac_address='02:00:1a:62:51:67',
        cache_frames=True
    )
    
    # Prefetch all frames into memory (batch query)
    logger.info("\nPrefetching all frames from TDengine...")
    dataset.prefetch_all_frames()
    
    # Now accessing samples is fast (from cache)
    logger.info("\nAccessing samples from cache:")
    for i in range(3):
        frame, target = dataset[i]
        logger.info(f"  Sample {i}: {frame.shape}, {target['num_objects']} objects (from cache)")


def example_with_dataloader():
    """
    Example 3: Using with PyTorch DataLoader for training
    """
    logger.info("\n" + "=" * 70)
    logger.info("Example 3: PyTorch DataLoader for Training")
    logger.info("=" * 70)
    
    # Create DataLoader (automatically prefetches if requested)
    dataloader = create_dataloader(
        annotation_file='Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json',
        mac_address='02:00:1a:62:51:67',
        batch_size=8,
        shuffle=True,
        prefetch=True  # Prefetch all frames before training
    )
    
    logger.info(f"\nDataLoader created:")
    logger.info(f"  Total batches: {len(dataloader)}")
    logger.info(f"  Batch size: {dataloader.batch_size}")
    
    # Iterate through batches (like in training loop)
    logger.info(f"\nIterating through first 3 batches:")
    for batch_idx, (frames, targets) in enumerate(dataloader):
        logger.info(f"\n  Batch {batch_idx}:")
        logger.info(f"    Frames shape: {frames.shape}")  # (batch_size, 1, H, W)
        logger.info(f"    Batch size: {len(targets)}")
        
        # Show details of first sample in batch
        logger.info(f"    First sample in batch:")
        logger.info(f"      Num objects: {targets[0]['num_objects']}")
        logger.info(f"      Boxes: {targets[0]['boxes'].shape}")
        logger.info(f"      Labels: {targets[0]['labels'].shape}")
        
        if batch_idx >= 2:  # Only show first 3 batches
            break
    
    logger.info(f"\n  ... ({len(dataloader) - 3} more batches)")


def example_training_loop():
    """
    Example 4: Complete training loop skeleton
    """
    logger.info("\n" + "=" * 70)
    logger.info("Example 4: Training Loop Skeleton")
    logger.info("=" * 70)
    
    # Create DataLoader
    dataloader = create_dataloader(
        annotation_file='Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json',
        mac_address='02:00:1a:62:51:67',
        batch_size=4,
        shuffle=True,
        prefetch=True
    )
    
    # Pseudo training loop
    logger.info("\nTraining loop skeleton:")
    logger.info("```python")
    logger.info("# Setup model (example)")
    logger.info("model = YourModel()")
    logger.info("optimizer = torch.optim.Adam(model.parameters())")
    logger.info("criterion = YourLossFunction()")
    logger.info("")
    logger.info("# Training loop")
    logger.info("for epoch in range(num_epochs):")
    logger.info("    for frames, targets in dataloader:")
    logger.info("        # frames: (batch_size, 1, 40, 60)")
    logger.info("        # targets: list of dicts with boxes and labels")
    logger.info("        ")
    logger.info("        optimizer.zero_grad()")
    logger.info("        ")
    logger.info("        # Forward pass")
    logger.info("        predictions = model(frames)")
    logger.info("        ")
    logger.info("        # Calculate loss")
    logger.info("        loss = criterion(predictions, targets)")
    logger.info("        ")
    logger.info("        # Backward pass")
    logger.info("        loss.backward()")
    logger.info("        optimizer.step()")
    logger.info("```")
    
    # Show actual iteration
    logger.info(f"\n\nActual iteration (first batch):")
    frames, targets = next(iter(dataloader))
    logger.info(f"  Frames: {frames.shape}")
    logger.info(f"  Targets: {len(targets)} samples")
    logger.info(f"  Ready for model.forward(frames)")


def example_custom_transforms():
    """
    Example 5: Using custom transforms
    """
    logger.info("\n" + "=" * 70)
    logger.info("Example 5: Custom Transforms")
    logger.info("=" * 70)
    
    # Define custom transform
    def normalize_temperature(frame_tensor):
        """Normalize temperature to [0, 1] range."""
        min_temp = 10.0  # °C
        max_temp = 30.0  # °C
        normalized = (frame_tensor - min_temp) / (max_temp - min_temp)
        return torch.clamp(normalized, 0.0, 1.0)
    
    # Create dataset with transform
    dataset = ThermalAnnotationDataset(
        annotation_file='Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json',
        mac_address='02:00:1a:62:51:67',
        transform=normalize_temperature,
        cache_frames=True
    )
    
    # Prefetch
    dataset.prefetch_all_frames()
    
    # Get sample with transform applied
    frame, target = dataset[0]
    
    logger.info(f"\nWith temperature normalization transform:")
    logger.info(f"  Frame range: {frame.min():.3f} to {frame.max():.3f} (normalized)")
    logger.info(f"  Original was in Celsius, now normalized to [0, 1]")


def main():
    """Run all examples."""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " PyTorch Custom DataLoader Examples".center(68) + "║")
    logger.info("║" + " Thermal Sensor Data with Annotations".center(68) + "║")
    logger.info("╚" + "=" * 68 + "╝")
    logger.info("\n")
    
    try:
        # Run examples
        example_basic_usage()
        example_prefetch_all()
        example_with_dataloader()
        example_training_loop()
        example_custom_transforms()
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ All examples completed successfully!")
        logger.info("=" * 70)
        logger.info("\n📚 Key Features:")
        logger.info("  ✓ No disk files needed - data fetched into memory")
        logger.info("  ✓ Automatic timestamp matching")
        logger.info("  ✓ In-memory caching for performance")
        logger.info("  ✓ Batch prefetching for efficient training")
        logger.info("  ✓ Custom transforms supported")
        logger.info("  ✓ Standard PyTorch Dataset/DataLoader API")
        logger.info("\n🚀 Ready for deep learning training!")
        logger.info("\n")
        
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        logger.error("\nMake sure TDengine server is accessible and has data for the specified MAC/timestamps.")
        logger.error("Run: uv run python diagnose_tdengine.py")


if __name__ == '__main__':
    main()

