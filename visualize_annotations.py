#!/usr/bin/env python3
"""
Visualize thermal data annotations in YOLO format.
"""

import json
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from src.thermal_data_processing.data_loader import ThermalDataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnnotationConverter:
    """Convert annotations to YOLO format."""
    
    def __init__(self):
        """Initialize annotation converter."""
        self.category_to_id = {}
        self.id_to_category = {}
        self.next_id = 0
    
    def yolo_to_corner(self, yolo_bbox: List[float]) -> List[float]:
        """
        Convert YOLO format [cx, cy, width, height] to corner format [x, y, width, height].
        Note: The annotation bbox is already in YOLO format (center_x, center_y, width, height).
        
        Args:
            yolo_bbox: [center_x, center_y, width, height] in YOLO format
            
        Returns:
            [x, y, width, height] where x, y is top-left corner
        """
        cx, cy, w, h = yolo_bbox
        x = cx - w / 2.0
        y = cy - h / 2.0
        return [x, y, w, h]
    
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
    
    def get_annotation_for_yolo(self, annotation: Dict) -> Tuple[int, List[float]]:
        """
        Get annotation data for YOLO export.
        Note: bbox is already in YOLO format (center_x, center_y, width, height).
        
        Args:
            annotation: Annotation dictionary
            
        Returns:
            Tuple of (class_id, yolo_bbox)
        """
        bbox = annotation['bbox']  # Already in YOLO format!
        category = annotation['category']
        subcategory = annotation['subcategory']
        
        class_id = self.get_category_id(category, subcategory)
        
        return class_id, bbox
    
    def format_yolo_line(self, class_id: int, yolo_bbox: List[float]) -> str:
        """
        Format YOLO annotation line.
        
        Args:
            class_id: Class ID
            yolo_bbox: YOLO format bbox [cx, cy, w, h]
            
        Returns:
            YOLO format string
        """
        cx, cy, w, h = yolo_bbox
        return f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}"


class AnnotationVisualizer:
    """Visualize thermal data with annotations."""
    
    def __init__(self, data_path: str, annotation_path: str):
        """
        Initialize visualizer.
        
        Args:
            data_path: Path to thermal data file
            annotation_path: Path to annotation file
        """
        self.data_path = Path(data_path)
        self.annotation_path = Path(annotation_path)
        self.loader = ThermalDataLoader()
        self.converter = AnnotationConverter()
        
        # Load data
        logger.info(f"Loading thermal data from {self.data_path}")
        self.frames, self.timestamps = self.loader.load_from_text_file(str(self.data_path))
        
        # Convert Kelvin to Celsius for visualization
        self.frames_celsius = self.frames - 273.15
        
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
    
    def _match_frame_to_annotation(self, frame_idx: int) -> Optional[Dict]:
        """
        Match a frame to its annotation by timestamp.
        
        Args:
            frame_idx: Frame index
            
        Returns:
            Annotation dictionary or None if no match
        """
        if frame_idx >= len(self.timestamps):
            return None
        
        frame_timestamp = self.timestamps[frame_idx]
        # Annotation timestamps are in milliseconds
        frame_timestamp_ms = int(frame_timestamp * 1000)
        
        # Find closest annotation
        best_match = None
        min_diff = float('inf')
        
        for annotation in self.annotations:
            ann_timestamp = annotation['data_time']
            diff = abs(ann_timestamp - frame_timestamp_ms)
            
            if diff < min_diff:
                min_diff = diff
                best_match = annotation
        
        # Only return if difference is less than 100ms
        if min_diff < 100:
            return best_match
        
        return None
    
    def visualize_frame(self, frame_idx: int, save_path: Optional[str] = None,
                       show_yolo_format: bool = True):
        """
        Visualize a single frame with annotations.
        
        Args:
            frame_idx: Frame index to visualize
            save_path: Optional path to save figure
            show_yolo_format: Whether to print YOLO format annotations
        """
        if frame_idx >= len(self.frames):
            logger.error(f"Frame index {frame_idx} out of range (max: {len(self.frames)-1})")
            return
        
        frame = self.frames_celsius[frame_idx]
        annotation = self._match_frame_to_annotation(frame_idx)
        
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Display frame
        im = ax.imshow(frame, cmap='gray', aspect='auto')
        ax.set_title(f"Frame {frame_idx} - Timestamp: {self.timestamps[frame_idx]:.3f}s")
        ax.set_xlabel("Width (pixels)")
        ax.set_ylabel("Height (pixels)")
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Temperature (°C)', rotation=270, labelpad=15)
        
        # Colors for different categories
        color_map = {
            'person': 'red',
            'furniture': 'blue',
            'object': 'green',
            'building': 'yellow',
            'environment': 'cyan',
            'appliance': 'magenta'
        }
        
        yolo_lines = []
        
        if annotation:
            logger.info(f"Frame {frame_idx} has {len(annotation['annotations'])} annotations")
            
            height, width = frame.shape
            
            for ann in annotation['annotations']:
                bbox = ann['bbox']  # [x, y, w, h] normalized
                category = ann['category']
                subcategory = ann['subcategory']
                object_id = ann['object_id']
                
                # Get YOLO format (already in YOLO format in the annotation)
                class_id, yolo_bbox = self.converter.get_annotation_for_yolo(ann)
                yolo_line = self.converter.format_yolo_line(class_id, yolo_bbox)
                yolo_lines.append(yolo_line)
                
                # Convert YOLO format (center) to pixel coordinates
                cx_norm, cy_norm, w_norm, h_norm = bbox
                
                # Convert center to top-left corner
                x_norm = cx_norm - w_norm / 2.0
                y_norm = cy_norm - h_norm / 2.0
                
                # Convert to pixel coordinates
                x_pixel = x_norm * width
                y_pixel = y_norm * height
                w_pixel = w_norm * width
                h_pixel = h_norm * height
                
                # Draw bounding box
                color = color_map.get(category, 'white')
                rect = patches.Rectangle(
                    (x_pixel, y_pixel), w_pixel, h_pixel,
                    linewidth=2, edgecolor=color, facecolor='none'
                )
                ax.add_patch(rect)
                
                # Add label
                label = f"{category}/{subcategory}\nID:{object_id}"
                ax.text(
                    x_pixel, y_pixel - 2,
                    label,
                    color=color,
                    fontsize=8,
                    verticalalignment='bottom',
                    bbox=dict(boxstyle='round', facecolor='black', alpha=0.7)
                )
        else:
            logger.warning(f"No annotation found for frame {frame_idx}")
        
        # Print YOLO format
        if show_yolo_format and yolo_lines:
            logger.info("\n" + "="*60)
            logger.info("YOLO Format Annotations:")
            logger.info("="*60)
            for line in yolo_lines:
                logger.info(line)
            logger.info("="*60)
            logger.info("\nClass ID Mapping:")
            for class_id, category in sorted(self.converter.id_to_category.items()):
                logger.info(f"  {class_id}: {category}")
            logger.info("="*60)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            logger.info(f"Saved visualization to {save_path}")
        
        plt.show()
    
    def visualize_multiple_frames(self, start_idx: int = 0, num_frames: int = 5,
                                  output_dir: Optional[str] = None):
        """
        Visualize multiple frames with annotations.
        
        Args:
            start_idx: Starting frame index
            num_frames: Number of frames to visualize
            output_dir: Optional directory to save visualizations
        """
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        
        for i in range(start_idx, min(start_idx + num_frames, len(self.frames))):
            save_path = None
            if output_dir:
                save_path = output_path / f"frame_{i:04d}.png"
            
            self.visualize_frame(i, save_path=save_path, show_yolo_format=(i == start_idx))


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Visualize thermal data annotations in YOLO format')
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
        '--frame',
        type=int,
        default=0,
        help='Frame index to visualize'
    )
    parser.add_argument(
        '--num-frames',
        type=int,
        default=1,
        help='Number of frames to visualize'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory to save visualizations'
    )
    
    args = parser.parse_args()
    
    # Create visualizer
    visualizer = AnnotationVisualizer(args.data, args.annotation)
    
    # Visualize frames
    if args.num_frames == 1:
        visualizer.visualize_frame(args.frame, show_yolo_format=True)
    else:
        visualizer.visualize_multiple_frames(
            start_idx=args.frame,
            num_frames=args.num_frames,
            output_dir=args.output_dir
        )


if __name__ == '__main__':
    main()

