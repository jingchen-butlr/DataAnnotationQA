#!/usr/bin/env python3
"""
Streaming Thermal Data Loader
Handles loading streaming thermal data from directories (like SQS data).
Integrated into the main data processing module.
"""

import numpy as np
import os
import re
import logging
import glob
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class StreamingDataLoader:
    """
    Loads streaming thermal sensor data from directories.
    Handles timestamp parsing and data validation for streaming formats.
    """
    
    def __init__(self, target_shape: Tuple[int, int] = (40, 60)):
        """
        Initialize streaming data loader.
        
        Args:
            target_shape: Expected frame shape (height, width)
        """
        self.target_shape = target_shape
        self.height, self.width = target_shape
        
        logger.info(f"Initialized streaming data loader for {self.width}x{self.height} frames")
    
    def parse_timestamp_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Parse timestamp from streaming data filename.
        
        Supported formats:
        - SQS format: udpc_XX_XX_XX_XX_XX_XX_packet_0_YYYYMMDD_HHMMSS_mmm.txt
        
        Args:
            filename: Data filename
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        try:
            # SQS format: udpc_*_packet_0_YYYYMMDD_HHMMSS_mmm.txt
            pattern = r'udpc_.*_packet_0_(\d{8})_(\d{6})_(\d{3})\.txt'
            match = re.match(pattern, filename, re.IGNORECASE)
            
            if not match:
                return None
            
            date_str, time_str, ms_str = match.groups()
            
            # Parse date and time
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            
            hour = int(time_str[:2])
            minute = int(time_str[2:4])
            second = int(time_str[4:6])
            
            microsecond = int(ms_str) * 1000  # Convert milliseconds to microseconds
            
            return datetime(year, month, day, hour, minute, second, microsecond)
            
        except (ValueError, AttributeError) as e:
            logger.debug(f"Failed to parse timestamp from {filename}: {e}")
            return None
    
    def load_frame_from_file(self, file_path: str) -> Optional[np.ndarray]:
        """
        Load thermal frame data from single file.
        
        Args:
            file_path: Path to thermal data file
            
        Returns:
            Thermal frame as numpy array or None if loading fails
        """
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Parse temperature values (one per line in Celsius)
            temperatures = []
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        temp = float(line)
                        temperatures.append(temp)
                    except ValueError:
                        continue
            
            # Check if we have the expected number of values
            expected_size = self.height * self.width
            if len(temperatures) < expected_size:
                logger.warning(f"File {file_path} has only {len(temperatures)} values, expected {expected_size}")
                return None
            
            # Take first values and reshape
            frame_data = np.array(temperatures[:expected_size], dtype=np.float32)
            frame = frame_data.reshape(self.target_shape)
            
            # Flip left-right to correct image orientation
            # frame = np.fliplr(frame)
            
            return frame
            
        except Exception as e:
            logger.warning(f"Failed to load frame from {file_path}: {e}")
            return None
    
    def get_files_in_time_range(self, directory: str, start_time: datetime, 
                                duration_minutes: float) -> List[Tuple[str, datetime]]:
        """
        Get all files within a specified time range.
        
        Args:
            directory: Directory containing streaming data files
            start_time: Start time for data collection
            duration_minutes: Duration in minutes
            
        Returns:
            List of (filepath, timestamp) tuples sorted by timestamp
        """
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        logger.info(f"Looking for files between {start_time} and {end_time}")
        
        # Get all txt files in directory
        pattern = str(Path(directory) / "*.txt")
        all_files = glob.glob(pattern)
        
        valid_files = []
        error_count = 0
        
        for file_path in all_files:
            filename = os.path.basename(file_path)
            timestamp = self.parse_timestamp_from_filename(filename)
            
            if timestamp is None:
                error_count += 1
                continue
            
            # Check if timestamp is within range
            if start_time <= timestamp <= end_time:
                valid_files.append((file_path, timestamp))
        
        # Sort by timestamp
        valid_files.sort(key=lambda x: x[1])
        
        logger.info(f"Found {len(valid_files)} valid files in time range")
        if error_count > 0:
            logger.debug(f"Ignored {error_count} files with parsing errors")
        
        return valid_files
    
    def load_streaming_data(self, directory: str, duration_minutes: float = None,
                           start_time: datetime = None) -> Tuple[np.ndarray, List[datetime], dict]:
        """
        Load streaming thermal data from directory.
        
        Args:
            directory: Directory containing streaming data files
            duration_minutes: Duration to read in minutes (if None, load all)
            start_time: Start time (if None, use earliest available)
            
        Returns:
            Tuple of (frames_array, timestamps_list, metadata_dict)
        """
        logger.info(f"Loading streaming data from: {directory}")
        
        # Get all files
        pattern = str(Path(directory) / "*.txt")
        all_files = glob.glob(pattern)
        
        if not all_files:
            raise ValueError(f"No data files found in directory: {directory}")
        
        # Parse timestamps to find time range
        file_timestamps = []
        for file_path in all_files:
            filename = os.path.basename(file_path)
            timestamp = self.parse_timestamp_from_filename(filename)
            if timestamp:
                file_timestamps.append((file_path, timestamp))
        
        if not file_timestamps:
            raise ValueError("No valid timestamps found in files")
        
        # Sort by timestamp
        file_timestamps.sort(key=lambda x: x[1])
        
        # Determine time range
        if start_time is None:
            start_time = file_timestamps[0][1]
        
        if duration_minutes is not None:
            # Filter to time range
            files_to_process = self.get_files_in_time_range(directory, start_time, duration_minutes)
        else:
            # Use all files
            files_to_process = file_timestamps
        
        logger.info(f"Processing {len(files_to_process)} files from {start_time}")
        
        # Load frames
        frames = []
        timestamps = []
        successful_loads = 0
        failed_loads = 0
        
        for file_path, timestamp in files_to_process:
            frame = self.load_frame_from_file(file_path)
            
            if frame is not None:
                frames.append(frame)
                timestamps.append(timestamp)
                successful_loads += 1
            else:
                failed_loads += 1
        
        if not frames:
            raise ValueError("No valid frames loaded from directory")
        
        # Convert to numpy array
        frames_array = np.array(frames)
        
        # Create metadata
        metadata = {
            'total_files_found': len(files_to_process),
            'successful_loads': successful_loads,
            'failed_loads': failed_loads,
            'start_time': start_time.isoformat(),
            'end_time': timestamps[-1].isoformat() if timestamps else None,
            'duration_minutes': (timestamps[-1] - timestamps[0]).total_seconds() / 60 if len(timestamps) > 1 else 0,
            'frame_rate_hz': len(frames) / ((timestamps[-1] - timestamps[0]).total_seconds()) if len(timestamps) > 1 else 0,
            'temperature_range': (float(np.min(frames_array)), float(np.max(frames_array))),
            'frame_shape': frames_array.shape
        }
        
        logger.info(f"Loaded {successful_loads} frames, failed {failed_loads}")
        logger.info(f"Frame rate: {metadata['frame_rate_hz']:.2f} Hz")
        logger.info(f"Temperature range: {metadata['temperature_range'][0]:.1f}°C to {metadata['temperature_range'][1]:.1f}°C")
        
        return frames_array, timestamps, metadata

