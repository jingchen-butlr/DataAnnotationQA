#!/usr/bin/env python3
"""
Visualize raw thermal data without annotations.
Creates a video showing thermal frames with temperature colormap.
"""

import argparse
import logging
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from tqdm import tqdm
from src.thermal_data_processing.data_loader import ThermalDataLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RawThermalVisualizer:
    """Visualize raw thermal data without annotations."""
    
    def __init__(self, fps: int = 10, scale_factor: int = 8):
        """
        Initialize visualizer.
        
        Args:
            fps: Frames per second for output video
            scale_factor: Scale factor to upscale thermal frames
        """
        self.fps = fps
        self.scale_factor = scale_factor
        self.loader = ThermalDataLoader()
        self.frames = None
        self.timestamps = None
        self.frames_celsius = None
    
    def load_data(self, data_path: str):
        """
        Load thermal data.
        
        Args:
            data_path: Path to thermal data file
        """
        logger.info(f"Loading thermal data from {data_path}")
        self.frames, self.timestamps = self.loader.load_from_text_file(data_path)
        
        # Convert Kelvin to Celsius for visualization
        self.frames_celsius = self.frames - 273.15
        
        logger.info(f"Loaded {len(self.frames)} frames")
        logger.info(f"Temperature range: {np.min(self.frames_celsius):.1f}°C to {np.max(self.frames_celsius):.1f}°C")
        
        if len(self.timestamps) > 0:
            duration = self.timestamps[-1] - self.timestamps[0]
            logger.info(f"Duration: {duration:.1f} seconds")
    
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
        frames = self.frames_celsius[start_frame:end_frame]
        
        # Calculate range with some margin
        vmin = np.percentile(frames, 1)  # 1st percentile
        vmax = np.percentile(frames, 99)  # 99th percentile
        
        # Add small margin
        margin = (vmax - vmin) * 0.05
        vmin -= margin
        vmax += margin
        
        return vmin, vmax
    
    def _visualize_frame(self, frame_idx: int, vmin: float, vmax: float) -> np.ndarray:
        """
        Visualize a single thermal frame.
        
        Args:
            frame_idx: Frame index
            vmin: Minimum temperature for colormap
            vmax: Maximum temperature for colormap
            
        Returns:
            BGR image for video output
        """
        frame_celsius = self.frames_celsius[frame_idx]
        timestamp = self.timestamps[frame_idx] if frame_idx < len(self.timestamps) else 0
        
        # Normalize to 0-255 range
        frame_norm = np.clip((frame_celsius - vmin) / (vmax - vmin), 0, 1)
        frame_uint8 = (frame_norm * 255).astype(np.uint8)
        
        # Apply colormap (TURBO is good for thermal data)
        frame_colored = cv2.applyColorMap(frame_uint8, cv2.COLORMAP_TURBO)
        
        # Upscale frame
        height, width = frame_colored.shape[:2]
        new_height = height * self.scale_factor
        new_width = width * self.scale_factor
        frame_scaled = cv2.resize(
            frame_colored, 
            (new_width, new_height), 
            interpolation=cv2.INTER_NEAREST
        )
        
        # Add text information
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.8
        font_thickness = 2
        text_color = (255, 255, 255)  # White
        bg_color = (0, 0, 0)  # Black background
        
        # Frame info
        frame_text = f"Frame: {frame_idx}"
        time_text = f"Time: {timestamp:.3f}s"
        temp_text = f"Temp Range: {vmin:.1f}C to {vmax:.1f}C"
        
        # Add text with black background for readability
        texts = [frame_text, time_text, temp_text]
        y_position = 30
        
        for text in texts:
            # Get text size for background
            (text_width, text_height), baseline = cv2.getTextSize(
                text, font, font_scale, font_thickness
            )
            
            # Draw black background
            cv2.rectangle(
                frame_scaled,
                (10, y_position - text_height - 5),
                (10 + text_width + 10, y_position + baseline + 5),
                bg_color,
                -1
            )
            
            # Draw text
            cv2.putText(
                frame_scaled,
                text,
                (15, y_position),
                font,
                font_scale,
                text_color,
                font_thickness,
                cv2.LINE_AA
            )
            
            y_position += text_height + 15
        
        # Add colorbar legend
        colorbar_width = 30
        colorbar_height = new_height - 100
        colorbar = np.linspace(255, 0, colorbar_height, dtype=np.uint8).reshape(-1, 1)
        colorbar = np.repeat(colorbar, colorbar_width, axis=1)
        colorbar_colored = cv2.applyColorMap(colorbar, cv2.COLORMAP_TURBO)
        
        # Position colorbar on the right side
        x_start = new_width - colorbar_width - 20
        y_start = 50
        frame_scaled[y_start:y_start+colorbar_height, x_start:x_start+colorbar_width] = colorbar_colored
        
        # Add temperature labels on colorbar
        for i, temp_val in enumerate(np.linspace(vmax, vmin, 5)):
            y_pos = y_start + int(i * colorbar_height / 4)
            temp_label = f"{temp_val:.1f}C"
            
            # Background for label
            (label_width, label_height), _ = cv2.getTextSize(
                temp_label, font, 0.5, 1
            )
            cv2.rectangle(
                frame_scaled,
                (x_start + colorbar_width + 5, y_pos - label_height - 2),
                (x_start + colorbar_width + label_width + 15, y_pos + 5),
                bg_color,
                -1
            )
            
            # Label text
            cv2.putText(
                frame_scaled,
                temp_label,
                (x_start + colorbar_width + 10, y_pos),
                font,
                0.5,
                text_color,
                1,
                cv2.LINE_AA
            )
        
        return frame_scaled
    
    def export_video(self, output_path: str,
                    start_frame: int = 0,
                    num_frames: Optional[int] = None,
                    codec: str = 'mp4v') -> str:
        """
        Export thermal frames as video.
        
        Args:
            output_path: Path for output video file
            start_frame: Starting frame index
            num_frames: Number of frames to export (None = all)
            codec: Video codec fourcc code
            
        Returns:
            Path to created video file
        """
        if self.frames is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        logger.info(f"Exporting video to {output_path}")
        
        # Determine frame range
        total_frames = len(self.frames)
        if num_frames is None:
            num_frames = total_frames - start_frame
        end_frame = min(start_frame + num_frames, total_frames)
        
        logger.info(f"Exporting frames {start_frame} to {end_frame-1} ({end_frame-start_frame} frames)")
        
        # Calculate global temperature range for consistent visualization
        vmin, vmax = self._calculate_temperature_range(start_frame, end_frame)
        logger.info(f"Temperature range: {vmin:.1f}°C to {vmax:.1f}°C")
        
        # Get first frame to determine dimensions
        first_frame = self._visualize_frame(start_frame, vmin, vmax)
        height, width = first_frame.shape[:2]
        
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
            viz_frame = self._visualize_frame(frame_idx, vmin, vmax)
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
        Export thermal frames as individual images.
        
        Args:
            output_dir: Directory for output images
            start_frame: Starting frame index
            num_frames: Number of frames to export (None = all)
            image_format: Image format (png, jpg)
            
        Returns:
            Path to output directory
        """
        if self.frames is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        logger.info(f"Exporting frames to {output_dir}")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Determine frame range
        total_frames = len(self.frames)
        if num_frames is None:
            num_frames = total_frames - start_frame
        end_frame = min(start_frame + num_frames, total_frames)
        
        # Calculate global temperature range
        vmin, vmax = self._calculate_temperature_range(start_frame, end_frame)
        
        # Process and save frames
        logger.info(f"Processing {end_frame - start_frame} frames...")
        for frame_idx in tqdm(range(start_frame, end_frame), desc="Exporting frames"):
            viz_frame = self._visualize_frame(frame_idx, vmin, vmax)
            
            # Save frame
            output_file = output_path / f"frame_{frame_idx:04d}.{image_format}"
            cv2.imwrite(str(output_file), viz_frame)
        
        logger.info(f"Frames exported to {output_dir}")
        return str(output_dir)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Visualize raw thermal data without annotations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create video from raw thermal data
  python visualize_raw_thermal.py --data Data/Gen3_Annotated_Data_MVP/Raw/SL14_R4.txt
  
  # Create video with custom output path
  python visualize_raw_thermal.py \
      --data Data/Gen3_Annotated_Data_MVP/Raw/SL14_R4.txt \
      --output output/videos/SL14_R4_thermal.mp4
  
  # Create video for specific frame range
  python visualize_raw_thermal.py --data Data/Gen3_Annotated_Data_MVP/Raw/SL14_R4.txt \
      --start-frame 0 --num-frames 100
  
  # Export as individual images instead of video
  python visualize_raw_thermal.py --data Data/Gen3_Annotated_Data_MVP/Raw/SL14_R4.txt \
      --export-images --output-dir output/raw_frames
        """
    )
    
    parser.add_argument(
        '--data',
        type=str,
        required=True,
        help='Path to thermal data file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='output/videos/raw_thermal.mp4',
        help='Output video file path'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output/raw_frames',
        help='Output directory for image frames (when using --export-images)'
    )
    parser.add_argument(
        '--start-frame',
        type=int,
        default=0,
        help='Starting frame index'
    )
    parser.add_argument(
        '--num-frames',
        type=int,
        default=None,
        help='Number of frames to process (default: all frames)'
    )
    parser.add_argument(
        '--fps',
        type=int,
        default=10,
        help='Frames per second for output video (default: 10)'
    )
    parser.add_argument(
        '--scale',
        type=int,
        default=8,
        help='Scale factor for upscaling frames (default: 8)'
    )
    parser.add_argument(
        '--codec',
        type=str,
        default='mp4v',
        choices=['mp4v', 'avc1', 'XVID', 'MJPG'],
        help='Video codec (default: mp4v)'
    )
    parser.add_argument(
        '--export-images',
        action='store_true',
        help='Export as individual images instead of video'
    )
    parser.add_argument(
        '--image-format',
        type=str,
        default='png',
        choices=['png', 'jpg'],
        help='Image format for frame export (default: png)'
    )
    
    args = parser.parse_args()
    
    # Validate data path
    data_path = Path(args.data)
    if not data_path.exists():
        logger.error(f"Thermal data file not found: {data_path}")
        return 1
    
    # Create visualizer
    logger.info("Initializing thermal data visualizer...")
    visualizer = RawThermalVisualizer(fps=args.fps, scale_factor=args.scale)
    
    # Load data
    logger.info("Loading thermal data...")
    visualizer.load_data(str(data_path))
    
    # Export based on mode
    if args.export_images:
        # Export as images
        logger.info("Exporting frames as images...")
        output_dir = visualizer.export_frames_as_images(
            args.output_dir,
            start_frame=args.start_frame,
            num_frames=args.num_frames,
            image_format=args.image_format
        )
        logger.info(f"\n{'='*60}")
        logger.info(f"SUCCESS: Frames exported to {output_dir}")
        logger.info(f"{'='*60}\n")
    else:
        # Export as video
        logger.info("Creating video...")
        output_file = visualizer.export_video(
            args.output,
            start_frame=args.start_frame,
            num_frames=args.num_frames,
            codec=args.codec
        )
        logger.info(f"\n{'='*60}")
        logger.info(f"SUCCESS: Video created at {output_file}")
        logger.info(f"{'='*60}\n")
    
    return 0


if __name__ == '__main__':
    exit(main())

