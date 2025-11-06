#!/usr/bin/env python3
"""
Create annotated video from thermal data and annotations.

This script uses the src/visualize_annotations module to:
1. Load thermal image frames and annotations
2. Overlay bounding boxes and labels on each frame
3. Export a video showing all frames sequentially with annotations
"""

import argparse
import logging
from pathlib import Path
from src.visualize_annotations import VideoExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Create annotated video from thermal data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create video with default settings
  python create_annotation_video.py
  
  # Create video with custom paths
  python create_annotation_video.py \
      --data Data/Gen3_Annotated_Data_MVP/Raw/SL18_R2.txt \
      --annotation Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R2_annotation.json \
      --output output/videos/SL18_R2_annotated.mp4
  
  # Create video for specific frame range
  python create_annotation_video.py --start-frame 0 --num-frames 100
  
  # Export as individual images instead of video
  python create_annotation_video.py --export-images --output-dir output/frames
        """
    )
    
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
        '--output',
        type=str,
        default='output/videos/annotated_thermal.mp4',
        help='Output video file path'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output/annotated_frames',
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
    parser.add_argument(
        '--create-summary',
        action='store_true',
        help='Create a summary report of the dataset'
    )
    
    args = parser.parse_args()
    
    # Validate paths
    data_path = Path(args.data)
    annotation_path = Path(args.annotation)
    
    if not data_path.exists():
        logger.error(f"Thermal data file not found: {data_path}")
        return 1
    
    if not annotation_path.exists():
        logger.error(f"Annotation file not found: {annotation_path}")
        return 1
    
    # Create exporter
    logger.info("Initializing video exporter...")
    exporter = VideoExporter(fps=args.fps, scale_factor=args.scale)
    
    # Load data
    logger.info("Loading thermal data and annotations...")
    exporter.load_data(str(data_path), str(annotation_path))
    
    # Export based on mode
    if args.export_images:
        # Export as images
        logger.info("Exporting annotated frames as images...")
        output_dir = exporter.export_frames_as_images(
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
        logger.info("Creating annotated video...")
        output_file = exporter.export_video(
            args.output,
            start_frame=args.start_frame,
            num_frames=args.num_frames,
            codec=args.codec
        )
        logger.info(f"\n{'='*60}")
        logger.info(f"SUCCESS: Video created at {output_file}")
        logger.info(f"{'='*60}\n")
    
    # Create summary if requested
    if args.create_summary:
        summary_path = Path(args.output).parent / "dataset_summary.txt"
        exporter.create_summary_report(str(summary_path))
        logger.info(f"Summary report created: {summary_path}")
    
    return 0


if __name__ == '__main__':
    exit(main())

