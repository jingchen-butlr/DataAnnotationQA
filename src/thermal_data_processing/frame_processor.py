#!/usr/bin/env python3
"""
Thermal Frame Data Processor
Component 1: Handles thermal frame data processing, conversion, and preprocessing.
"""

import numpy as np
import logging
from typing import Union, Tuple, Optional, List, Dict, Any
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class FrameDataProcessor(ABC):
    """Abstract base class for thermal frame data processing."""
    
    @abstractmethod
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process a single thermal frame."""
        pass
    
    @abstractmethod
    def process_batch(self, frames: np.ndarray) -> np.ndarray:
        """Process a batch of thermal frames."""
        pass


class ThermalFrameDataProcessor(FrameDataProcessor):
    """
    Thermal frame data processor for 60x40 thermal sensors.
    
    Handles temperature conversion, preprocessing, validation, and statistics.
    Designed to be independent and reusable across different thermal sensors.
    """
    
    def __init__(self, 
                 target_shape: Tuple[int, int] = (40, 60),
                 temperature_unit: str = 'kelvin'):
        """
        Initialize thermal frame processor.
        
        Args:
            target_shape: Expected frame shape (height, width)
            temperature_unit: Input temperature unit ('kelvin', 'celsius', 'decikelvin')
        """
        self.target_shape = target_shape
        self.temperature_unit = temperature_unit.lower()
        self.height, self.width = target_shape
        
        logger.info(f"Initialized thermal frame processor: {self.width}x{self.height}, unit: {temperature_unit}")
    
    def convert_temperature(self, data: np.ndarray, 
                          from_unit: str = None, 
                          to_unit: str = 'celsius') -> np.ndarray:
        """
        Convert temperature between units.
        
        Args:
            data: Temperature data array
            from_unit: Source unit (if None, uses self.temperature_unit)
            to_unit: Target unit
            
        Returns:
            Converted temperature data
        """
        if from_unit is None:
            from_unit = self.temperature_unit
        
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        
        if from_unit == to_unit:
            return data.copy()
        
        # Convert to Kelvin first
        if from_unit == 'decikelvin':
            kelvin_data = data / 10.0
        elif from_unit == 'celsius':
            kelvin_data = data + 273.15
        elif from_unit == 'kelvin':
            kelvin_data = data.copy()
        else:
            raise ValueError(f"Unsupported source unit: {from_unit}")
        
        # Convert from Kelvin to target
        if to_unit == 'kelvin':
            return kelvin_data
        elif to_unit == 'celsius':
            return kelvin_data - 273.15
        elif to_unit == 'decikelvin':
            return kelvin_data * 10.0
        else:
            raise ValueError(f"Unsupported target unit: {to_unit}")
    
    def validate_frame_shape(self, frame: np.ndarray) -> bool:
        """
        Validate frame shape matches expected dimensions.
        
        Args:
            frame: Input thermal frame
            
        Returns:
            True if shape is valid
        """
        return frame.shape == self.target_shape
    
    def process_frame(self, frame: np.ndarray, 
                     convert_to: str = 'celsius',
                     validate_shape: bool = True) -> np.ndarray:
        """
        Process a single thermal frame.
        
        Args:
            frame: Input thermal frame
            convert_to: Target temperature unit
            validate_shape: Whether to validate frame shape
            
        Returns:
            Processed thermal frame
        """
        if validate_shape and not self.validate_frame_shape(frame):
            raise ValueError(f"Frame shape {frame.shape} doesn't match expected {self.target_shape}")
        
        # Convert temperature
        processed_frame = self.convert_temperature(frame, to_unit=convert_to)
        
        # Remove any invalid values
        processed_frame = np.where(np.isfinite(processed_frame), processed_frame, np.nan)
        
        return processed_frame
    
    def process_batch(self, frames: np.ndarray, 
                     convert_to: str = 'celsius',
                     validate_shapes: bool = True) -> np.ndarray:
        """
        Process a batch of thermal frames.
        
        Args:
            frames: Input thermal frames (batch_size, height, width)
            convert_to: Target temperature unit
            validate_shapes: Whether to validate frame shapes
            
        Returns:
            Processed thermal frames
        """
        if len(frames.shape) != 3:
            raise ValueError(f"Expected 3D array (batch, height, width), got shape {frames.shape}")
        
        processed_frames = []
        
        for i, frame in enumerate(frames):
            try:
                processed_frame = self.process_frame(frame, convert_to, validate_shapes)
                processed_frames.append(processed_frame)
            except Exception as e:
                logger.error(f"Error processing frame {i}: {e}")
                # Add NaN frame to maintain batch size
                nan_frame = np.full(self.target_shape, np.nan)
                processed_frames.append(nan_frame)
        
        return np.array(processed_frames)
    
    def calculate_mean_frame(self, frames: np.ndarray, 
                           ignore_nan: bool = True) -> np.ndarray:
        """
        Calculate mean frame across temporal dimension.
        
        Args:
            frames: Input frames (batch_size, height, width)
            ignore_nan: Whether to ignore NaN values in calculation
            
        Returns:
            Mean frame (height, width)
        """
        if ignore_nan:
            mean_frame = np.nanmean(frames, axis=0)
        else:
            mean_frame = np.mean(frames, axis=0)
        
        logger.info(f"Calculated mean frame from {len(frames)} frames")
        return mean_frame
    
    def calculate_frame_statistics(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Calculate statistics for a thermal frame.
        
        Args:
            frame: Input thermal frame
            
        Returns:
            Dictionary with frame statistics
        """
        valid_pixels = frame[~np.isnan(frame)]
        
        if len(valid_pixels) == 0:
            return {
                'min': np.nan, 'max': np.nan, 'mean': np.nan, 'std': np.nan,
                'valid_pixels': 0, 'total_pixels': frame.size
            }
        
        return {
            'min': np.min(valid_pixels),
            'max': np.max(valid_pixels),
            'mean': np.mean(valid_pixels),
            'std': np.std(valid_pixels),
            'valid_pixels': len(valid_pixels),
            'total_pixels': frame.size
        }
