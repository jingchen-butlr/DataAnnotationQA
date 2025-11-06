"""
Data and annotation loading functionality.
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from src.thermal_data_processing.data_loader import ThermalDataLoader as BaseThermalLoader

logger = logging.getLogger(__name__)


class ThermalDataLoader:
    """Load thermal data from text files."""
    
    def __init__(self, target_shape: Tuple[int, int] = (40, 60)):
        """
        Initialize thermal data loader.
        
        Args:
            target_shape: Expected frame shape (height, width)
        """
        self.loader = BaseThermalLoader(target_shape=target_shape)
        self.frames = None
        self.timestamps = None
        self.frames_celsius = None
    
    def load(self, data_path: str) -> Tuple[np.ndarray, List[float]]:
        """
        Load thermal data from file.
        
        Args:
            data_path: Path to thermal data file
            
        Returns:
            Tuple of (frames_celsius, timestamps)
        """
        logger.info(f"Loading thermal data from {data_path}")
        
        # Load frames in Kelvin
        self.frames, self.timestamps = self.loader.load_from_text_file(data_path)
        
        # Convert to Celsius for visualization
        self.frames_celsius = self.frames - 273.15
        
        logger.info(f"Loaded {len(self.frames)} frames")
        logger.info(f"Temperature range: {np.min(self.frames_celsius):.1f}°C to {np.max(self.frames_celsius):.1f}°C")
        
        return self.frames_celsius, self.timestamps
    
    def get_frame(self, idx: int) -> Optional[np.ndarray]:
        """
        Get a specific frame.
        
        Args:
            idx: Frame index
            
        Returns:
            Frame in Celsius or None if invalid index
        """
        if self.frames_celsius is None or idx >= len(self.frames_celsius):
            return None
        return self.frames_celsius[idx]
    
    def get_timestamp(self, idx: int) -> Optional[float]:
        """
        Get timestamp for a specific frame.
        
        Args:
            idx: Frame index
            
        Returns:
            Timestamp or None if invalid index
        """
        if self.timestamps is None or idx >= len(self.timestamps):
            return None
        return self.timestamps[idx]


class AnnotationLoader:
    """Load and manage annotations."""
    
    def __init__(self):
        """Initialize annotation loader."""
        self.annotations = []
        self.category_to_id = {}
        self.id_to_category = {}
        self.next_id = 0
    
    def load(self, annotation_path: str) -> List[Dict]:
        """
        Load annotations from JSON file.
        
        Args:
            annotation_path: Path to annotation file
            
        Returns:
            List of annotation dictionaries
        """
        logger.info(f"Loading annotations from {annotation_path}")
        
        self.annotations = []
        with open(annotation_path, 'r') as f:
            for line in f:
                if line.strip():
                    ann = json.loads(line.strip())
                    self.annotations.append(ann)
                    
                    # Build category mapping
                    for obj in ann.get('annotations', []):
                        category = obj.get('category', '')
                        subcategory = obj.get('subcategory', '')
                        self._register_category(category, subcategory)
        
        logger.info(f"Loaded {len(self.annotations)} annotations")
        logger.info(f"Found {len(self.category_to_id)} unique categories")
        
        return self.annotations
    
    def _register_category(self, category: str, subcategory: str) -> int:
        """
        Register a category and get its ID.
        
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
    
    def get_category_id(self, category: str, subcategory: str) -> int:
        """
        Get category ID.
        
        Args:
            category: Main category
            subcategory: Subcategory
            
        Returns:
            Category ID
        """
        full_category = f"{category}/{subcategory}"
        return self.category_to_id.get(full_category, -1)
    
    def match_frame_to_annotation(self, frame_idx: int, timestamps: List[float], 
                                   tolerance_ms: int = 100) -> Optional[Dict]:
        """
        Match a frame to its annotation by timestamp.
        
        Args:
            frame_idx: Frame index
            timestamps: List of frame timestamps
            tolerance_ms: Matching tolerance in milliseconds
            
        Returns:
            Annotation dictionary or None if no match
        """
        if frame_idx >= len(timestamps):
            return None
        
        frame_timestamp = timestamps[frame_idx]
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
        
        # Only return if difference is within tolerance
        if min_diff < tolerance_ms:
            return best_match
        
        return None
    

