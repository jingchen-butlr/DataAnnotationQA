#!/usr/bin/env python3
"""
Export thermal data annotations to YOLO format.
"""

import json
import logging
import argparse
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from src.thermal_data_processing.data_loader import ThermalDataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class YOLOExporter:
    """Export annotations to YOLO format."""
    
    def __init__(self, data_path: str, annotation_path: str, output_dir: str):
        """
        Initialize YOLO exporter.
        
        Args:
            data_path: Path to thermal data file
            annotation_path: Path to annotation file
            output_dir: Output directory for YOLO format files
        """
        self.data_path = Path(data_path)
        self.annotation_path = Path(annotation_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.loader = ThermalDataLoader()
        self.category_to_id = {}
        self.id_to_category = {}
        self.next_id = 0
        
        # Load data
        logger.info(f"Loading thermal data from {self.data_path}")
        self.frames, self.timestamps = self.loader.load_from_text_file(str(self.data_path))
        logger.info(f"Loaded {len(self.frames)} frames")
        
        # Load annotations
        logger.info(f"Loading annotations from {self.annotation_path}")
        self.annotations = self._load_annotations()
        logger.info(f"Loaded {len(self.annotations)} annotations")
    
    def _load_annotations(self) -> List[Dict]:
        """Load annotations from JSON file."""
        annotations = []
        with open(self.annotation_path, 'r') as f:
            for line in f:
                if line.strip():
                    annotations.append(json.loads(line.strip()))
        return annotations
    
    def get_category_id(self, category: str, subcategory: str) -> int:
        """
        Get or create category ID for YOLO format.
        
        Args:
            category: Main category
            subcategory: Subcategory
            
        Returns:
            Category ID
        """
        full_category = f"{category}/{subcategory}"
        
        if full_category not in self.category_to_id:
            self.category_to_id[full_category] = self.next_id
            self.id_to_category[self.next_id] = full_category
            self.next_id += 1
        
        return self.category_to_id[full_category]
    
    
    def export_annotations(self):
        """Export all annotations to YOLO format."""
        # Create directory structure
        labels_dir = self.output_dir / "labels"
        labels_dir.mkdir(exist_ok=True)
        
        # Export annotations
        exported_count = 0
        
        for annotation in self.annotations:
            data_time = annotation['data_time']
            data_id = annotation['data_id']
            
            # Find matching frame
            frame_idx = self._find_frame_by_timestamp(data_time)
            
            if frame_idx is None:
                logger.warning(f"No matching frame found for annotation at {data_time}")
                continue
            
            # Create YOLO format annotation file
            label_file = labels_dir / f"{data_id}_frame_{frame_idx:04d}.txt"
            
            with open(label_file, 'w') as f:
                for ann in annotation['annotations']:
                    bbox = ann['bbox']  # Already in YOLO format!
                    category = ann['category']
                    subcategory = ann['subcategory']
                    
                    class_id = self.get_category_id(category, subcategory)
                    
                    # bbox is already [center_x, center_y, width, height]
                    cx, cy, w, h = bbox
                    f.write(f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
            
            exported_count += 1
        
        logger.info(f"Exported {exported_count} annotation files to {labels_dir}")
        
        # Export class mapping
        self._export_class_mapping()
        
        # Export dataset info
        self._export_dataset_info()
    
    def _find_frame_by_timestamp(self, annotation_timestamp_ms: int) -> int:
        """
        Find frame index by timestamp.
        
        Args:
            annotation_timestamp_ms: Annotation timestamp in milliseconds
            
        Returns:
            Frame index or None if no match
        """
        best_idx = None
        min_diff = float('inf')
        
        for idx, frame_timestamp in enumerate(self.timestamps):
            frame_timestamp_ms = int(frame_timestamp * 1000)
            diff = abs(frame_timestamp_ms - annotation_timestamp_ms)
            
            if diff < min_diff:
                min_diff = diff
                best_idx = idx
        
        # Only return if difference is less than 100ms
        if min_diff < 100:
            return best_idx
        
        return None
    
    def _export_class_mapping(self):
        """Export class ID to category mapping."""
        mapping_file = self.output_dir / "classes.txt"
        
        with open(mapping_file, 'w') as f:
            for class_id in sorted(self.id_to_category.keys()):
                category = self.id_to_category[class_id]
                f.write(f"{category}\n")
        
        logger.info(f"Exported class mapping to {mapping_file}")
        logger.info("\nClass Mapping:")
        for class_id in sorted(self.id_to_category.keys()):
            logger.info(f"  {class_id}: {self.id_to_category[class_id]}")
    
    def _export_dataset_info(self):
        """Export dataset information."""
        info_file = self.output_dir / "dataset.yaml"
        
        with open(info_file, 'w') as f:
            f.write(f"# YOLO Dataset Configuration\n")
            f.write(f"# Generated from {self.annotation_path.name}\n\n")
            f.write(f"path: {self.output_dir.absolute()}\n")
            f.write(f"train: labels\n")
            f.write(f"val: labels\n\n")
            f.write(f"# Classes\n")
            f.write(f"nc: {len(self.id_to_category)}  # number of classes\n")
            f.write(f"names:\n")
            for class_id in sorted(self.id_to_category.keys()):
                category = self.id_to_category[class_id]
                f.write(f"  {class_id}: {category}\n")
        
        logger.info(f"Exported dataset info to {info_file}")
    
    def export_frames_as_images(self, output_format: str = 'npy'):
        """
        Export thermal frames as images.
        
        Args:
            output_format: Format to export ('npy', 'png')
        """
        images_dir = self.output_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Convert to Celsius
        frames_celsius = self.frames - 273.15
        
        if output_format == 'npy':
            # Export as numpy arrays
            for idx, frame in enumerate(frames_celsius):
                output_file = images_dir / f"frame_{idx:04d}.npy"
                np.save(output_file, frame)
            logger.info(f"Exported {len(frames_celsius)} frames as .npy to {images_dir}")
        
        elif output_format == 'png':
            # Export as PNG images
            import matplotlib.pyplot as plt
            
            for idx, frame in enumerate(frames_celsius):
                output_file = images_dir / f"frame_{idx:04d}.png"
                
                # Normalize to 0-255
                frame_normalized = ((frame - frame.min()) / (frame.max() - frame.min()) * 255).astype(np.uint8)
                
                plt.imsave(output_file, frame_normalized, cmap='gray')
            
            logger.info(f"Exported {len(frames_celsius)} frames as .png to {images_dir}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Export thermal data annotations to YOLO format')
    parser.add_argument(
        '--data',
        type=str,
        default='Data/Gen3_Annotated_Data_MVP/Raw/SL18_R1.txt',
        help='Path to thermal data file'
    )
    parser.add_argument(
        '--annotation',
        type=str,
        default='Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json',
        help='Path to annotation file'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output/yolo_format',
        help='Output directory for YOLO format files'
    )
    parser.add_argument(
        '--export-images',
        action='store_true',
        help='Export thermal frames as images'
    )
    parser.add_argument(
        '--image-format',
        type=str,
        choices=['npy', 'png'],
        default='npy',
        help='Format for exported images'
    )
    
    args = parser.parse_args()
    
    # Create exporter
    exporter = YOLOExporter(args.data, args.annotation, args.output_dir)
    
    # Export annotations
    exporter.export_annotations()
    
    # Export images if requested
    if args.export_images:
        exporter.export_frames_as_images(output_format=args.image_format)
    
    logger.info("\n" + "="*60)
    logger.info("Export completed successfully!")
    logger.info("="*60)


if __name__ == '__main__':
    main()

