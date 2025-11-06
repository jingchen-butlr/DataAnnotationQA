"""
Video export functionality.
"""

import logging
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from tqdm import tqdm

from .loader import ThermalDataLoader, AnnotationLoader
from .visualizer import AnnotationVisualizer

logger = logging.getLogger(__name__)


class VideoExporter:
    """Export annotated thermal data as video."""
    
    def __init__(self, fps: int = 10, scale_factor: int = 8):
        """
        Initialize video exporter.
        
        Args:
            fps: Frames per second for output video
            scale_factor: Scale factor to upscale thermal frames
        """
        self.fps = fps
        self.scale_factor = scale_factor
        self.thermal_loader = ThermalDataLoader()
        self.annotation_loader = AnnotationLoader()
        self.visualizer = AnnotationVisualizer(scale_factor=scale_factor)
    
    def load_data(self, data_path: str, annotation_path: str):
        """
        Load thermal data and annotations.
        
        Args:
            data_path: Path to thermal data file
            annotation_path: Path to annotation file
        """
        self.thermal_loader.load(data_path)
        self.annotation_loader.load(annotation_path)
        logger.info("Data loading complete")
    
    def export_video(self, output_path: str, 
                    start_frame: int = 0,
                    num_frames: Optional[int] = None,
                    codec: str = 'mp4v') -> str:
        """
        Export annotated frames as video.
        
        Args:
            output_path: Path for output video file
            start_frame: Starting frame index
            num_frames: Number of frames to export (None = all)
            codec: Video codec fourcc code
            
        Returns:
            Path to created video file
        """
        logger.info(f"Exporting video to {output_path}")
        
        # Determine frame range
        total_frames = len(self.thermal_loader.frames_celsius)
        if num_frames is None:
            num_frames = total_frames - start_frame
        end_frame = min(start_frame + num_frames, total_frames)
        
        logger.info(f"Exporting frames {start_frame} to {end_frame-1} ({end_frame-start_frame} frames)")
        
        # Calculate global temperature range for consistent visualization
        vmin, vmax = self._calculate_temperature_range(start_frame, end_frame)
        logger.info(f"Temperature range: {vmin:.1f}°C to {vmax:.1f}°C")
        
        # Get first frame to determine dimensions (visualizer handles scaling internally)
        first_frame = self.thermal_loader.get_frame(start_frame)
        first_annotation = self.annotation_loader.match_frame_to_annotation(
            start_frame, self.thermal_loader.timestamps
        )
        first_viz = self.visualizer.visualize_frame(
            first_frame, first_annotation, 
            self.thermal_loader.get_timestamp(start_frame),
            start_frame, vmin, vmax
        )
        
        # Get dimensions from scaled frame
        height, width = first_viz.shape[:2]
        
        logger.info(f"Video dimensions: {width}x{height}")
        
        # Create video writer
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            self.fps,
            (width, height)
        )
        
        if not writer.isOpened():
            raise RuntimeError(f"Failed to create video writer for {output_path}")
        
        # Process and write frames
        logger.info("Processing frames...")
        for frame_idx in tqdm(range(start_frame, end_frame), desc="Creating video"):
            frame = self.thermal_loader.get_frame(frame_idx)
            timestamp = self.thermal_loader.get_timestamp(frame_idx)
            annotation = self.annotation_loader.match_frame_to_annotation(
                frame_idx, self.thermal_loader.timestamps
            )
            
            # Visualize frame (scaling is handled inside visualizer)
            viz_frame = self.visualizer.visualize_frame(
                frame, annotation, timestamp, frame_idx, vmin, vmax
            )
            
            # Write frame directly (already scaled by visualizer)
            writer.write(viz_frame)
        
        writer.release()
        
        logger.info(f"Video exported successfully to {output_path}")
        logger.info(f"Video stats: {end_frame - start_frame} frames, {self.fps} fps, "
                   f"{(end_frame - start_frame) / self.fps:.1f} seconds")
        
        return str(output_path)
    
    def export_frames_as_images(self, output_dir: str,
                               start_frame: int = 0,
                               num_frames: Optional[int] = None,
                               image_format: str = 'png') -> str:
        """
        Export annotated frames as individual images.
        
        Args:
            output_dir: Directory for output images
            start_frame: Starting frame index
            num_frames: Number of frames to export (None = all)
            image_format: Image format (png, jpg)
            
        Returns:
            Path to output directory
        """
        logger.info(f"Exporting frames to {output_dir}")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Determine frame range
        total_frames = len(self.thermal_loader.frames_celsius)
        if num_frames is None:
            num_frames = total_frames - start_frame
        end_frame = min(start_frame + num_frames, total_frames)
        
        # Calculate global temperature range
        vmin, vmax = self._calculate_temperature_range(start_frame, end_frame)
        
        # Process and save frames
        logger.info(f"Processing {end_frame - start_frame} frames...")
        for frame_idx in tqdm(range(start_frame, end_frame), desc="Exporting frames"):
            frame = self.thermal_loader.get_frame(frame_idx)
            timestamp = self.thermal_loader.get_timestamp(frame_idx)
            annotation = self.annotation_loader.match_frame_to_annotation(
                frame_idx, self.thermal_loader.timestamps
            )
            
            # Visualize frame (scaling is handled inside visualizer)
            viz_frame = self.visualizer.visualize_frame(
                frame, annotation, timestamp, frame_idx, vmin, vmax
            )
            
            # Save frame directly (already scaled by visualizer)
            output_file = output_path / f"frame_{frame_idx:04d}.{image_format}"
            cv2.imwrite(str(output_file), viz_frame)
        
        logger.info(f"Frames exported to {output_dir}")
        return str(output_dir)
    
    def _calculate_temperature_range(self, start_frame: int, 
                                     end_frame: int) -> Tuple[float, float]:
        """
        Calculate temperature range for normalization.
        
        Args:
            start_frame: Starting frame index
            end_frame: Ending frame index
            
        Returns:
            Tuple of (vmin, vmax)
        """
        frames = self.thermal_loader.frames_celsius[start_frame:end_frame]
        
        # Calculate range with some margin
        vmin = np.percentile(frames, 1)  # 1st percentile
        vmax = np.percentile(frames, 99)  # 99th percentile
        
        # Add small margin
        margin = (vmax - vmin) * 0.05
        vmin -= margin
        vmax += margin
        
        return vmin, vmax
    
    def create_summary_report(self, output_path: str):
        """
        Create a summary report of the dataset.
        
        Args:
            output_path: Path for summary text file
        """
        logger.info(f"Creating summary report: {output_path}")
        
        with open(output_path, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("THERMAL DATA ANNOTATION SUMMARY\n")
            f.write("=" * 60 + "\n\n")
            
            # Dataset info
            f.write(f"Total Frames: {len(self.thermal_loader.frames_celsius)}\n")
            f.write(f"Annotated Frames: {len(self.annotation_loader.annotations)}\n")
            f.write(f"Temperature Range: {np.min(self.thermal_loader.frames_celsius):.1f}°C to "
                   f"{np.max(self.thermal_loader.frames_celsius):.1f}°C\n")
            f.write(f"Duration: {self.thermal_loader.timestamps[-1] - self.thermal_loader.timestamps[0]:.1f} seconds\n\n")
            
            # Category statistics
            f.write("Categories Found:\n")
            f.write("-" * 60 + "\n")
            for class_id, category in sorted(self.annotation_loader.id_to_category.items()):
                count = sum(
                    1 for ann in self.annotation_loader.annotations
                    for obj in ann.get('annotations', [])
                    if f"{obj.get('category')}/{obj.get('subcategory')}" == category
                )
                f.write(f"  {class_id}: {category:<40} ({count} instances)\n")
            
            f.write("\n" + "=" * 60 + "\n")
        
        logger.info(f"Summary report created: {output_path}")

