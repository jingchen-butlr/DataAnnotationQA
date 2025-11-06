#!/usr/bin/env python3
"""
Thermal Data Loader
Handles loading thermal data from various file formats.
"""

import numpy as np
import logging
import re
from pathlib import Path
from typing import Union, Tuple, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ThermalDataLoader:
    """
    Thermal data loader supporting multiple file formats.
    
    Supports:
    - Text files with deciKelvin values (like 250922_distort_001.txt)
    - NumPy arrays (.npy, .npz)
    - CSV files
    """
    
    def __init__(self, target_shape: Tuple[int, int] = (40, 60)):
        """
        Initialize thermal data loader.
        
        Args:
            target_shape: Expected frame shape (height, width)
        """
        self.target_shape = target_shape
        self.height, self.width = target_shape
        
        logger.info(f"Initialized thermal data loader for {self.width}x{self.height} frames")
    
    def load_from_text_file(self, file_path: str) -> Tuple[np.ndarray, List[float]]:
        """
        Load thermal data from text file (deciKelvin format).
        
        Args:
            file_path: Path to text file
            
        Returns:
            Tuple of (frames_array, timestamps)
        """
        logger.info(f"Loading thermal data from text file: {file_path}")
        
        frames = []
        timestamps = []
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        logger.info(f"Total lines in file: {len(lines)}")
        
        # Parse each frame
        for line_idx, line in enumerate(lines[1:], 1):  # Skip header
            line = line.strip()
            if not line:
                continue
            
            # Extract timestamp if present
            timestamp_match = re.search(r't:\s*([\d.]+)', line)
            if timestamp_match:
                timestamp = float(timestamp_match.group(1))
                timestamps.append(timestamp)
                line = re.sub(r't:\s*[\d.]+', '', line)
            
            # Extract temperature values
            temp_values = []
            clean_line = re.sub(r'[^\d\s]', ' ', line)
            parts = clean_line.split()
            
            for part in parts:
                if len(part) == 5 and part.isdigit():
                    # Convert from deciKelvin to Kelvin
                    temp_k = int(part) / 10.0
                    temp_values.append(temp_k)
            
            # Create frame if we have enough values
            if len(temp_values) >= self.height * self.width:
                thermal_values = temp_values[:self.height * self.width]
                frame = np.array(thermal_values, dtype=np.float32).reshape(self.target_shape)
                # Flip left-right to correct image orientation
                # frame = np.fliplr(frame)
                frames.append(frame)
        
        frames_array = np.array(frames)
        logger.info(f"Loaded {len(frames)} frames from text file")
        
        if len(frames) > 0:
            logger.info(f"Temperature range: {np.min(frames_array):.1f}K to {np.max(frames_array):.1f}K")
        
        return frames_array, timestamps
    
    def load_from_numpy(self, file_path: str) -> np.ndarray:
        """
        Load thermal data from NumPy file.
        
        Args:
            file_path: Path to .npy or .npz file
            
        Returns:
            Thermal frames array
        """
        logger.info(f"Loading thermal data from NumPy file: {file_path}")
        
        file_path = Path(file_path)
        
        if file_path.suffix == '.npy':
            data = np.load(file_path)
        elif file_path.suffix == '.npz':
            npz_data = np.load(file_path)
            # Try common keys
            if 'data' in npz_data:
                data = npz_data['data']
            elif 'frames' in npz_data:
                data = npz_data['frames']
            else:
                data = npz_data[npz_data.files[0]]
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Ensure proper shape
        if len(data.shape) == 2:
            data = data[np.newaxis, ...]  # Add batch dimension
        elif len(data.shape) != 3:
            raise ValueError(f"Expected 2D or 3D array, got shape {data.shape}")
        
        logger.info(f"Loaded {len(data)} frames from NumPy file")
        return data
    
    def load_from_csv(self, file_path: str) -> np.ndarray:
        """
        Load thermal data from CSV file (single frame).
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Single thermal frame
        """
        logger.info(f"Loading thermal data from CSV file: {file_path}")
        
        data = np.loadtxt(file_path, delimiter=',')
        
        if data.shape != self.target_shape:
            logger.warning(f"CSV shape {data.shape} != expected {self.target_shape}, reshaping...")
            if data.size == self.height * self.width:
                data = data.reshape(self.target_shape)
            else:
                raise ValueError(f"Cannot reshape CSV data to {self.target_shape}")
        
        # Add batch dimension
        data = data[np.newaxis, ...]
        
        logger.info("Loaded single frame from CSV file")
        return data
    
    def load_thermal_data(self, file_path: str) -> Tuple[np.ndarray, Optional[List[float]]]:
        """
        Load thermal data from any supported format.
        
        Args:
            file_path: Path to thermal data file
            
        Returns:
            Tuple of (frames_array, timestamps_or_None)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = file_path.suffix.lower()
        
        if extension == '.txt':
            return self.load_from_text_file(str(file_path))
        elif extension in ['.npy', '.npz']:
            frames = self.load_from_numpy(str(file_path))
            return frames, None
        elif extension == '.csv':
            frames = self.load_from_csv(str(file_path))
            return frames, None
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    def save_thermal_data(self, frames: np.ndarray, file_path: str, 
                         file_format: str = None) -> None:
        """
        Save thermal data to file.
        
        Args:
            frames: Thermal frames to save
            file_path: Output file path
            file_format: File format ('npy', 'npz', 'csv'). If None, inferred from extension
        """
        file_path = Path(file_path)
        
        if file_format is None:
            file_format = file_path.suffix[1:].lower()
        
        if file_format == 'npy':
            np.save(file_path, frames)
        elif file_format == 'npz':
            np.savez_compressed(file_path, data=frames)
        elif file_format == 'csv':
            if len(frames.shape) == 3 and frames.shape[0] == 1:
                np.savetxt(file_path, frames[0], delimiter=',')
            else:
                raise ValueError("CSV format only supports single frame")
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
        
        logger.info(f"Saved {len(frames)} frames to: {file_path}")
