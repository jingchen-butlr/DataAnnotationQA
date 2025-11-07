#!/usr/bin/env python3
"""
Prepare Training Data Pipeline

This script reads annotation JSON files and automatically fetches matching
raw thermal data from TDengine for deep learning model training.

Features:
- Read annotation JSON files
- Extract data_time and calculate time ranges
- Fetch raw thermal data from TDengine using MAC address
- Match annotations with thermal frames
- Export in training-ready format (YOLO, images, etc.)
"""

import json
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrainingDataPipeline:
    """Automated pipeline to prepare training data from annotations and TDengine."""
    
    def __init__(self, mac_address: str, timezone: str = "LA"):
        """
        Initialize training data pipeline.
        
        Args:
            mac_address: Sensor MAC address for TDengine queries
            timezone: Timezone for time conversion (LA, NY, UTC)
        """
        self.mac_address = mac_address
        self.timezone = timezone
        self.annotations = []
        self.time_range = None
        
    def read_annotation_file(self, annotation_path: str) -> List[Dict]:
        """
        Read annotation JSON file and extract timestamps.
        
        Args:
            annotation_path: Path to annotation JSON file
            
        Returns:
            List of annotation dictionaries
        """
        logger.info(f"Reading annotations from: {annotation_path}")
        
        annotations = []
        with open(annotation_path, 'r') as f:
            for line in f:
                if line.strip():
                    ann = json.loads(line.strip())
                    annotations.append(ann)
        
        logger.info(f"Loaded {len(annotations)} annotations")
        self.annotations = annotations
        return annotations
    
    def extract_time_range(self, buffer_seconds: int = 5) -> Tuple[str, str]:
        """
        Extract time range from annotations with buffer.
        
        Args:
            buffer_seconds: Buffer time in seconds to add on each side
            
        Returns:
            Tuple of (start_time, end_time) in "YYYY-MM-DD HH:MM:SS" format
        """
        if not self.annotations:
            raise ValueError("No annotations loaded. Call read_annotation_file() first.")
        
        # Extract all data_time values (in milliseconds)
        timestamps_ms = [ann['data_time'] for ann in self.annotations]
        
        # Convert to seconds
        min_ts = min(timestamps_ms) / 1000.0
        max_ts = max(timestamps_ms) / 1000.0
        
        # Add buffer
        start_ts = min_ts - buffer_seconds
        end_ts = max_ts + buffer_seconds
        
        # Convert to datetime
        start_dt = datetime.fromtimestamp(start_ts)
        end_dt = datetime.fromtimestamp(end_ts)
        
        # Format for TDengine query (local time)
        start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info(f"Time range extracted:")
        logger.info(f"  Annotations: {len(timestamps_ms)}")
        logger.info(f"  First: {datetime.fromtimestamp(min_ts).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        logger.info(f"  Last: {datetime.fromtimestamp(max_ts).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        logger.info(f"  Duration: {(max_ts - min_ts):.1f} seconds")
        logger.info(f"  With buffer ({buffer_seconds}s): {start_str} to {end_str}")
        
        self.time_range = (start_str, end_str)
        return start_str, end_str
    
    def fetch_thermal_data_from_tdengine(self, output_path: str) -> str:
        """
        Fetch raw thermal data from TDengine.
        
        Args:
            output_path: Path for output thermal data file
            
        Returns:
            Path to exported thermal data file
        """
        if not self.time_range:
            raise ValueError("Time range not set. Call extract_time_range() first.")
        
        start_time, end_time = self.time_range
        
        logger.info("=" * 60)
        logger.info("Fetching thermal data from TDengine")
        logger.info("=" * 60)
        logger.info(f"MAC: {self.mac_address}")
        logger.info(f"Time: {start_time} to {end_time} ({self.timezone})")
        logger.info(f"Output: {output_path}")
        
        # Prepare output directory
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert timezone to UTC for TDengine query
        import pytz
        from datetime import datetime
        
        if self.timezone.upper() == "UTC":
            start_utc = start_time
            end_utc = end_time
        elif self.timezone.upper() == "LA":
            tz = pytz.timezone('America/Los_Angeles')
            utc = pytz.UTC
            
            start_local = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_local = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            
            start_local = tz.localize(start_local)
            end_local = tz.localize(end_local)
            
            start_utc = start_local.astimezone(utc).strftime("%Y-%m-%d %H:%M:%S")
            end_utc = end_local.astimezone(utc).strftime("%Y-%m-%d %H:%M:%S")
        elif self.timezone.upper() == "NY":
            tz = pytz.timezone('America/New_York')
            utc = pytz.UTC
            
            start_local = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_local = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            
            start_local = tz.localize(start_local)
            end_local = tz.localize(end_local)
            
            start_utc = start_local.astimezone(utc).strftime("%Y-%m-%d %H:%M:%S")
            end_utc = end_local.astimezone(utc).strftime("%Y-%m-%d %H:%M:%S")
        else:
            raise ValueError(f"Unsupported timezone: {self.timezone}")
        
        logger.info(f"UTC query: {start_utc} to {end_utc}")
        
        # Call TDengine export tool
        export_script = "dependent_tools/tdengine_export/tools/export_tool/export_thermal_data.py"
        
        if not Path(export_script).exists():
            raise FileNotFoundError(f"TDengine export tool not found: {export_script}")
        
        # Run export
        cmd = [
            "uv", "run", "python",
            export_script,
            "--mac", self.mac_address,
            "--start", start_utc,
            "--end", end_utc,
            "--output-multi", str(output_file)
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error("Export failed!")
            logger.error(result.stderr)
            raise RuntimeError(f"TDengine export failed: {result.stderr}")
        
        logger.info(result.stdout)
        logger.info(f"✅ Thermal data exported to: {output_file}")
        
        return str(output_file)
    
    def verify_match(self, thermal_data_path: str, annotation_path: str) -> Dict:
        """
        Verify that thermal data matches annotations.
        
        Args:
            thermal_data_path: Path to thermal data file
            annotation_path: Path to annotation file
            
        Returns:
            Dictionary with matching statistics
        """
        logger.info("=" * 60)
        logger.info("Verifying annotation-data match")
        logger.info("=" * 60)
        
        import re
        
        # Load thermal timestamps
        with open(thermal_data_path, 'r') as f:
            lines = f.readlines()
        
        thermal_timestamps = []
        for line in lines[1:]:  # Skip header
            match = re.search(r't:\s*([\d.]+)', line)
            if match:
                thermal_timestamps.append(float(match.group(1)))
        
        # Load annotation timestamps
        with open(annotation_path, 'r') as f:
            annotations = [json.loads(line.strip()) for line in f if line.strip()]
        
        ann_timestamps = [ann['data_time'] / 1000.0 for ann in annotations]
        
        # Check matching
        matched = 0
        unmatched = []
        
        for idx, ann_ts in enumerate(ann_timestamps):
            found = False
            for thermal_ts in thermal_timestamps:
                if abs(thermal_ts - ann_ts) < 0.1:  # Within 100ms
                    matched += 1
                    found = True
                    break
            
            if not found:
                unmatched.append(idx)
        
        match_rate = matched / len(ann_timestamps) * 100 if ann_timestamps else 0
        
        stats = {
            'total_frames': len(thermal_timestamps),
            'total_annotations': len(ann_timestamps),
            'matched': matched,
            'unmatched': len(unmatched),
            'match_rate': match_rate,
            'unmatched_indices': unmatched
        }
        
        logger.info(f"Thermal frames: {stats['total_frames']}")
        logger.info(f"Annotations: {stats['total_annotations']}")
        logger.info(f"Matched: {stats['matched']}/{stats['total_annotations']}")
        logger.info(f"Match rate: {match_rate:.1f}%")
        
        if match_rate == 100:
            logger.info("✅ Perfect match! All annotations can be matched.")
        elif match_rate >= 90:
            logger.warning(f"⚠️ Good match but {len(unmatched)} annotations unmatched")
        else:
            logger.error(f"❌ Poor match! Only {match_rate:.1f}% matched")
        
        return stats
    
    def export_training_dataset(self, thermal_data_path: str, 
                                annotation_path: str,
                                output_dir: str,
                                export_format: str = "yolo") -> str:
        """
        Export complete training dataset.
        
        Args:
            thermal_data_path: Path to thermal data
            annotation_path: Path to annotations
            output_dir: Output directory for training data
            export_format: Format to export (yolo, images, video)
            
        Returns:
            Path to output directory
        """
        logger.info("=" * 60)
        logger.info("Exporting training dataset")
        logger.info("=" * 60)
        logger.info(f"Format: {export_format}")
        logger.info(f"Output: {output_dir}")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if export_format == "yolo":
            # Export YOLO format
            cmd = [
                "uv", "run", "python",
                "export_yolo_annotations.py",
                "--data", thermal_data_path,
                "--annotation", annotation_path,
                "--output-dir", output_dir,
                "--export-images",
                "--image-format", "png"
            ]
            
            logger.info("Exporting YOLO dataset...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error("YOLO export failed!")
                logger.error(result.stderr)
                raise RuntimeError(f"YOLO export failed: {result.stderr}")
            
            logger.info(result.stdout)
            logger.info(f"✅ YOLO dataset exported to: {output_dir}")
        
        elif export_format == "video":
            # Export video for verification
            video_path = output_path / "training_data_preview.mp4"
            
            cmd = [
                "uv", "run", "python",
                "create_annotation_video.py",
                "--data", thermal_data_path,
                "--annotation", annotation_path,
                "--output", str(video_path),
                "--create-summary"
            ]
            
            logger.info("Creating preview video...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error("Video export failed!")
                logger.error(result.stderr)
                raise RuntimeError(f"Video export failed: {result.stderr}")
            
            logger.info(result.stdout)
            logger.info(f"✅ Preview video created: {video_path}")
        
        return str(output_path)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Prepare training data pipeline: Read annotations → Fetch from TDengine → Export for training',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Basic usage - auto-fetch from TDengine and export YOLO
  python prepare_training_data.py \\
      --annotation Data/annotations/my_annotations.json \\
      --mac 02:00:1a:62:51:67 \\
      --output training_data/session_001

  # With custom timezone
  python prepare_training_data.py \\
      --annotation Data/annotations/my_annotations.json \\
      --mac 02:00:1a:62:51:67 \\
      --timezone NY \\
      --output training_data/session_001

  # Export as video for verification
  python prepare_training_data.py \\
      --annotation Data/annotations/my_annotations.json \\
      --mac 02:00:1a:62:51:67 \\
      --output training_data/session_001 \\
      --format video

  # Use existing thermal data (skip TDengine fetch)
  python prepare_training_data.py \\
      --annotation Data/annotations/my_annotations.json \\
      --thermal-data Data/existing_data.txt \\
      --output training_data/session_001
        """
    )
    
    parser.add_argument(
        '--annotation',
        type=str,
        required=True,
        help='Path to annotation JSON file'
    )
    parser.add_argument(
        '--mac',
        type=str,
        default=None,
        help='Sensor MAC address (e.g., 02:00:1a:62:51:67). Required if --thermal-data not provided.'
    )
    parser.add_argument(
        '--thermal-data',
        type=str,
        default=None,
        help='Path to existing thermal data file (skip TDengine fetch if provided)'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output directory for training data'
    )
    parser.add_argument(
        '--timezone',
        type=str,
        default='LA',
        choices=['LA', 'NY', 'UTC'],
        help='Timezone for time conversion (default: LA)'
    )
    parser.add_argument(
        '--format',
        type=str,
        default='yolo',
        choices=['yolo', 'video', 'both'],
        help='Export format (default: yolo)'
    )
    parser.add_argument(
        '--buffer',
        type=int,
        default=5,
        help='Buffer time in seconds to add to time range (default: 5)'
    )
    parser.add_argument(
        '--skip-verify',
        action='store_true',
        help='Skip match verification step'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.thermal_data and not args.mac:
        parser.error("Either --thermal-data or --mac must be provided")
    
    annotation_path = Path(args.annotation)
    if not annotation_path.exists():
        logger.error(f"Annotation file not found: {annotation_path}")
        return 1
    
    # Initialize pipeline
    if args.mac:
        pipeline = TrainingDataPipeline(args.mac, args.timezone)
    else:
        pipeline = TrainingDataPipeline("", args.timezone)
    
    # Step 1: Read annotations
    logger.info("\n" + "=" * 60)
    logger.info("STEP 1: Read Annotation File")
    logger.info("=" * 60)
    
    annotations = pipeline.read_annotation_file(str(annotation_path))
    
    # Step 2: Extract time range
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Extract Time Range")
    logger.info("=" * 60)
    
    start_time, end_time = pipeline.extract_time_range(buffer_seconds=args.buffer)
    
    # Step 3: Fetch thermal data (or use existing)
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Get Thermal Data")
    logger.info("=" * 60)
    
    if args.thermal_data:
        # Use existing thermal data
        thermal_path = args.thermal_data
        logger.info(f"Using existing thermal data: {thermal_path}")
        
        if not Path(thermal_path).exists():
            logger.error(f"Thermal data file not found: {thermal_path}")
            return 1
    else:
        # Fetch from TDengine
        # Create output filename
        mac_underscore = args.mac.replace(':', '_')
        start_formatted = start_time.replace(' ', '_').replace(':', '-')
        end_formatted = end_time.replace(' ', '_').replace(':', '-')
        thermal_filename = f"{mac_underscore}_{start_formatted}_{end_formatted}.txt"
        thermal_path = str(Path(args.output) / "raw_data" / thermal_filename)
        
        try:
            thermal_path = pipeline.fetch_thermal_data_from_tdengine(thermal_path)
        except Exception as e:
            logger.error(f"Failed to fetch from TDengine: {e}")
            logger.error("\nTroubleshooting:")
            logger.error("1. Check TDengine connection: uv run python diagnose_tdengine.py")
            logger.error("2. Verify MAC address is correct")
            logger.error("3. Check if data exists for this time range")
            return 1
    
    # Step 4: Verify match
    if not args.skip_verify:
        logger.info("\n" + "=" * 60)
        logger.info("STEP 4: Verify Annotation-Data Match")
        logger.info("=" * 60)
        
        stats = pipeline.verify_match(thermal_path, str(annotation_path))
        
        if stats['match_rate'] < 90:
            logger.warning("\n⚠️ Warning: Low match rate!")
            logger.warning("Some annotations may not have corresponding thermal frames.")
            logger.warning("Consider adjusting the time range or buffer.")
            
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                logger.info("Aborted by user.")
                return 1
    
    # Step 5: Export training dataset
    logger.info("\n" + "=" * 60)
    logger.info("STEP 5: Export Training Dataset")
    logger.info("=" * 60)
    
    formats = ['yolo', 'video'] if args.format == 'both' else [args.format]
    
    for fmt in formats:
        output_subdir = str(Path(args.output) / fmt)
        pipeline.export_training_dataset(
            thermal_path,
            str(annotation_path),
            output_subdir,
            export_format=fmt
        )
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("✅ TRAINING DATA PIPELINE COMPLETE")
    logger.info("=" * 60)
    logger.info(f"\nOutput location: {args.output}")
    logger.info(f"Annotations: {len(annotations)}")
    logger.info(f"Thermal data: {thermal_path}")
    
    if 'yolo' in formats:
        logger.info(f"\nYOLO dataset: {args.output}/yolo/")
        logger.info("  - labels/ (annotation files)")
        logger.info("  - images/ (thermal images)")
        logger.info("  - classes.txt")
        logger.info("  - dataset.yaml")
    
    if 'video' in formats:
        logger.info(f"\nPreview video: {args.output}/video/training_data_preview.mp4")
    
    logger.info("\n✅ Ready for deep learning model training!")
    
    return 0


if __name__ == '__main__':
    exit(main())

