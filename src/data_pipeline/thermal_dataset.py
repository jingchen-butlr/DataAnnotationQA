"""
PyTorch Custom Dataset for Thermal Sensor Data with Annotations

This module implements a custom PyTorch Dataset that:
1. Reads annotation JSON files
2. Fetches raw thermal data directly from TDengine (in-memory, no disk files)
3. Returns tensors ready for deep learning training
"""

import json
import logging
import requests
import zlib
import struct
import base64
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class TDengineConnector:
    """
    Direct TDengine connection for fetching thermal data into memory.
    No disk I/O - data decompressed directly into numpy arrays.
    """
    
    def __init__(self, host: str = "35.90.244.93", port: int = 6041,
                 user: str = "root", password: str = "taosdata",
                 database: str = "thermal_sensors_pilot"):
        """
        Initialize TDengine connector.
        
        Args:
            host: TDengine server host
            port: TDengine REST API port
            user: Database user
            password: Database password
            database: Database name
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.base_url = f"http://{host}:{port}/rest/sql"
        
        logger.info(f"Initialized TDengine connector: {host}:{port}/{database}")
    
    def query_frame_by_timestamp(self, mac_address: str, timestamp_ms: int,
                                 tolerance_ms: int = 100) -> Optional[np.ndarray]:
        """
        Query a single frame by timestamp, fetch directly into memory.
        
        Args:
            mac_address: Sensor MAC address (e.g., "02:00:1a:62:51:67")
            timestamp_ms: Timestamp in milliseconds
            tolerance_ms: Matching tolerance in milliseconds
            
        Returns:
            Thermal frame as numpy array (40, 60) in Celsius, or None if not found
        """
        # Convert timestamp to TDengine format
        timestamp_sec = timestamp_ms / 1000.0
        dt = datetime.utcfromtimestamp(timestamp_sec)
        ts_str = dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Millisecond precision
        
        # Calculate time window
        start_sec = (timestamp_ms - tolerance_ms) / 1000.0
        end_sec = (timestamp_ms + tolerance_ms) / 1000.0
        start_dt = datetime.utcfromtimestamp(start_sec)
        end_dt = datetime.utcfromtimestamp(end_sec)
        start_str = start_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        end_str = end_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Build table name from MAC
        table_name = f"sensor_{mac_address.replace(':', '_')}"
        
        # Query frame data within tolerance window
        sql = f"""
        SELECT ts, frame_data, width, height
        FROM {table_name}
        WHERE ts >= '{start_str}' AND ts <= '{end_str}'
        ORDER BY ts ASC
        LIMIT 1
        """
        
        try:
            url = f"{self.base_url}/{self.database}"
            response = requests.post(
                url,
                auth=(self.user, self.password),
                data=sql,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"HTTP error {response.status_code}")
                return None
            
            result = response.json()
            
            if result.get('code') != 0:
                error_msg = result.get('desc', result.get('msg', 'Unknown error'))
                logger.error(f"Query failed: {error_msg}")
                return None
            
            data = result.get('data', [])
            
            if not data:
                logger.warning(f"No frame found for timestamp {timestamp_ms}")
                return None
            
            # Extract frame data
            row = data[0]
            encoded_frame_data = row[1]  # Compressed frame data
            width = row[2] if len(row) > 2 else 60
            height = row[3] if len(row) > 3 else 40
            
            # Decompress frame data directly into memory
            frame = self._decompress_frame_data(encoded_frame_data, width, height)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error fetching frame: {e}")
            return None
    
    def _decompress_frame_data(self, encoded_data: str, width: int = 60, 
                               height: int = 40) -> np.ndarray:
        """
        Decompress frame data from TDengine format into numpy array in memory.
        
        Args:
            encoded_data: Hex or base64 encoded compressed data
            width: Frame width
            height: Frame height
            
        Returns:
            Numpy array (height, width) in Celsius
        """
        try:
            # Decode from hex or base64
            try:
                if all(c in '0123456789abcdefABCDEF' for c in encoded_data):
                    compressed_bytes = bytes.fromhex(encoded_data)
                else:
                    compressed_bytes = base64.b64decode(encoded_data)
            except:
                compressed_bytes = base64.b64decode(encoded_data)
            
            # Decompress with zlib
            decompressed = zlib.decompress(compressed_bytes)
            
            num_pixels = width * height
            
            # Detect format by size
            if len(decompressed) == num_pixels * 2:
                # int16 format (deciKelvin)
                frame_data = struct.unpack(f'{num_pixels}h', decompressed)
                # Convert deciKelvin to Celsius
                frame_celsius = np.array([(val / 10.0) - 273.15 for val in frame_data], dtype=np.float32)
            elif len(decompressed) == num_pixels * 4:
                # float32 format (Celsius)
                frame_data = struct.unpack(f'{num_pixels}f', decompressed)
                frame_celsius = np.array(frame_data, dtype=np.float32)
            else:
                raise ValueError(f"Unexpected data size: {len(decompressed)}")
            
            # Reshape to (height, width)
            frame = frame_celsius.reshape(height, width)
            
            # Apply left-right flip for correct orientation
            # Make a copy to avoid negative stride issues with PyTorch
            frame = np.fliplr(frame).copy()
            
            return frame
            
        except Exception as e:
            logger.error(f"Error decompressing frame: {e}")
            raise
    
    def batch_query_frames(self, mac_address: str, timestamps_ms: List[int],
                          tolerance_ms: int = 100) -> Dict[int, np.ndarray]:
        """
        Query multiple frames by timestamps (batch query for efficiency).
        
        Args:
            mac_address: Sensor MAC address
            timestamps_ms: List of timestamps in milliseconds
            tolerance_ms: Matching tolerance
            
        Returns:
            Dictionary mapping timestamp_ms to frame arrays
        """
        frames = {}
        
        # Calculate overall time range
        min_ts = min(timestamps_ms) - tolerance_ms
        max_ts = max(timestamps_ms) + tolerance_ms
        
        min_dt = datetime.utcfromtimestamp(min_ts / 1000.0)
        max_dt = datetime.utcfromtimestamp(max_ts / 1000.0)
        
        start_str = min_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        end_str = max_dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Build table name
        table_name = f"sensor_{mac_address.replace(':', '_')}"
        
        # Query all frames in range
        sql = f"""
        SELECT ts, frame_data, width, height
        FROM {table_name}
        WHERE ts >= '{start_str}' AND ts <= '{end_str}'
        ORDER BY ts ASC
        """
        
        try:
            url = f"{self.base_url}/{self.database}"
            response = requests.post(
                url,
                auth=(self.user, self.password),
                data=sql,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"HTTP error {response.status_code}")
                return frames
            
            result = response.json()
            
            if result.get('code') != 0:
                error_msg = result.get('desc', result.get('msg', 'Unknown error'))
                logger.error(f"Query failed: {error_msg}")
                return frames
            
            data = result.get('data', [])
            logger.info(f"Batch query found {len(data)} frames")
            
            # Process each frame
            for row in data:
                frame_ts_str = row[0]
                frame_data = row[1]
                width = row[2] if len(row) > 2 else 60
                height = row[3] if len(row) > 3 else 40
                
                # Parse timestamp (handle both formats: space and T separator)
                frame_ts_clean = frame_ts_str[:23].replace('T', ' ')
                frame_dt = datetime.strptime(frame_ts_clean, '%Y-%m-%d %H:%M:%S.%f')
                frame_ts_ms = int(frame_dt.timestamp() * 1000)
                
                # Match to requested timestamps
                for target_ts in timestamps_ms:
                    if abs(frame_ts_ms - target_ts) <= tolerance_ms:
                        # Decompress frame
                        frame = self._decompress_frame_data(frame_data, width, height)
                        frames[target_ts] = frame
                        break
            
            logger.info(f"Matched {len(frames)}/{len(timestamps_ms)} frames")
            return frames
            
        except Exception as e:
            logger.error(f"Batch query error: {e}")
            return frames


class ThermalAnnotationDataset(Dataset):
    """
    PyTorch custom Dataset for thermal sensor data with annotations.
    
    Follows PyTorch Dataset pattern with __init__, __len__, __getitem__.
    Fetches thermal data directly from TDengine into memory (no disk files).
    
    Reference: https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html
    """
    
    def __init__(self, annotation_file: str, mac_address: str,
                 tdengine_config: Optional[Dict] = None,
                 transform=None, target_transform=None,
                 cache_frames: bool = True):
        """
        Initialize the dataset.
        
        Args:
            annotation_file: Path to annotation JSON file (one JSON per line)
            mac_address: Sensor MAC address for TDengine queries
            tdengine_config: Optional TDengine connection config
            transform: Optional transform to apply to frames
            target_transform: Optional transform to apply to annotations
            cache_frames: Whether to cache fetched frames in memory
        """
        self.annotation_file = annotation_file
        self.mac_address = mac_address
        self.transform = transform
        self.target_transform = target_transform
        self.cache_frames = cache_frames
        
        # Load annotations from JSON file
        self.annotations = self._load_annotations()
        
        # Initialize TDengine connector
        tdengine_config = tdengine_config or {}
        self.tdengine = TDengineConnector(**tdengine_config)
        
        # Frame cache (in-memory)
        self.frame_cache = {} if cache_frames else None
        
        # Category mapping for labels
        self.category_to_id = {}
        self.id_to_category = {}
        self._build_category_mapping()
        
        logger.info(f"Initialized ThermalAnnotationDataset:")
        logger.info(f"  Annotation file: {annotation_file}")
        logger.info(f"  MAC address: {mac_address}")
        logger.info(f"  Total samples: {len(self.annotations)}")
        logger.info(f"  Categories: {len(self.category_to_id)}")
        logger.info(f"  Cache enabled: {cache_frames}")
    
    def _load_annotations(self) -> List[Dict]:
        """Load annotations from JSON file (one JSON object per line)."""
        annotations = []
        
        with open(self.annotation_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        ann = json.loads(line.strip())
                        annotations.append(ann)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse line {line_num}: {e}")
        
        logger.info(f"Loaded {len(annotations)} annotations from {self.annotation_file}")
        return annotations
    
    def _build_category_mapping(self):
        """Build category to ID mapping for classification tasks."""
        next_id = 0
        
        for ann in self.annotations:
            for obj in ann.get('annotations', []):
                category = obj.get('category', '')
                subcategory = obj.get('subcategory', '')
                full_category = f"{category}/{subcategory}"
                
                if full_category not in self.category_to_id:
                    self.category_to_id[full_category] = next_id
                    self.id_to_category[next_id] = full_category
                    next_id += 1
        
        logger.info(f"Built category mapping with {len(self.category_to_id)} categories")
    
    def __len__(self) -> int:
        """
        Return the number of samples in the dataset.
        Required by PyTorch Dataset.
        """
        return len(self.annotations)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, Dict]:
        """
        Get a sample from the dataset at the given index.
        Required by PyTorch Dataset.
        
        Args:
            idx: Sample index
            
        Returns:
            Tuple of (thermal_frame_tensor, annotation_dict)
            - thermal_frame_tensor: torch.Tensor of shape (1, H, W) in Celsius
            - annotation_dict: Dict with bboxes, labels, and metadata
        """
        if idx >= len(self.annotations):
            raise IndexError(f"Index {idx} out of range (0-{len(self.annotations)-1})")
        
        # Get annotation for this index
        annotation = self.annotations[idx]
        data_time_ms = annotation['data_time']  # Milliseconds
        
        # Check cache first
        if self.cache_frames and data_time_ms in self.frame_cache:
            frame = self.frame_cache[data_time_ms]
        else:
            # Fetch frame from TDengine directly into memory
            frame = self.tdengine.query_frame_by_timestamp(
                self.mac_address,
                data_time_ms,
                tolerance_ms=100
            )
            
            if frame is None:
                logger.warning(f"Frame not found for timestamp {data_time_ms}, using zeros")
                frame = np.zeros((40, 60), dtype=np.float32)
            
            # Cache if enabled
            if self.cache_frames:
                self.frame_cache[data_time_ms] = frame
        
        # Convert numpy to torch tensor
        # Add channel dimension: (H, W) → (1, H, W)
        frame_tensor = torch.from_numpy(frame).unsqueeze(0)
        
        # Apply transform if provided
        if self.transform:
            frame_tensor = self.transform(frame_tensor)
        
        # Process annotations into training format
        target = self._process_annotation(annotation)
        
        # Apply target transform if provided
        if self.target_transform:
            target = self.target_transform(target)
        
        return frame_tensor, target
    
    def _process_annotation(self, annotation: Dict) -> Dict:
        """
        Process annotation into training-ready format.
        
        Args:
            annotation: Raw annotation dictionary
            
        Returns:
            Processed annotation with tensors for bboxes and labels
        """
        objects = annotation.get('annotations', [])
        
        if not objects:
            # No objects in frame
            return {
                'boxes': torch.zeros((0, 4), dtype=torch.float32),
                'labels': torch.zeros((0,), dtype=torch.int64),
                'image_id': annotation.get('data_id', ''),
                'timestamp': annotation.get('data_time', 0),
            }
        
        # Extract bboxes and labels
        boxes = []
        labels = []
        
        for obj in objects:
            bbox = obj.get('bbox', [])
            category = obj.get('category', '')
            subcategory = obj.get('subcategory', '')
            
            if len(bbox) == 4:
                boxes.append(bbox)  # Already in YOLO format [cx, cy, w, h]
                
                # Get category ID
                full_category = f"{category}/{subcategory}"
                label_id = self.category_to_id.get(full_category, 0)
                labels.append(label_id)
        
        # Convert to tensors
        boxes_tensor = torch.tensor(boxes, dtype=torch.float32)
        labels_tensor = torch.tensor(labels, dtype=torch.int64)
        
        return {
            'boxes': boxes_tensor,  # Shape: (N, 4) - YOLO format
            'labels': labels_tensor,  # Shape: (N,)
            'image_id': annotation.get('data_id', ''),
            'timestamp': annotation.get('data_time', 0),
            'num_objects': len(objects),
        }
    
    def get_category_name(self, label_id: int) -> str:
        """Get category name from label ID."""
        return self.id_to_category.get(label_id, 'unknown')
    
    def prefetch_all_frames(self):
        """
        Prefetch all frames from TDengine into memory cache.
        Useful for training to avoid repeated network queries.
        """
        if not self.cache_frames:
            logger.warning("Cache is disabled, prefetch has no effect")
            return
        
        logger.info(f"Prefetching {len(self.annotations)} frames...")
        
        # Collect all timestamps
        timestamps = [ann['data_time'] for ann in self.annotations]
        
        # Batch query for efficiency
        frames = self.tdengine.batch_query_frames(
            self.mac_address,
            timestamps,
            tolerance_ms=100
        )
        
        # Update cache
        self.frame_cache.update(frames)
        
        logger.info(f"Prefetched {len(frames)} frames into cache")
        logger.info(f"Cache hit rate will be: {len(frames)}/{len(timestamps)} ({len(frames)/len(timestamps)*100:.1f}%)")
    
    def get_statistics(self) -> Dict:
        """Get dataset statistics."""
        return {
            'total_samples': len(self.annotations),
            'num_categories': len(self.category_to_id),
            'categories': self.category_to_id,
            'mac_address': self.mac_address,
            'cache_size': len(self.frame_cache) if self.cache_frames else 0,
            'cached_frames': list(self.frame_cache.keys()) if self.cache_frames else [],
        }


def create_dataloader(annotation_file: str, mac_address: str,
                     batch_size: int = 8, shuffle: bool = True,
                     num_workers: int = 0, prefetch: bool = True,
                     tdengine_config: Optional[Dict] = None,
                     **dataloader_kwargs) -> DataLoader:
    """
    Create a PyTorch DataLoader for thermal annotation data.
    
    Args:
        annotation_file: Path to annotation JSON file
        mac_address: Sensor MAC address
        batch_size: Batch size for training
        shuffle: Whether to shuffle data
        num_workers: Number of worker processes
        prefetch: Whether to prefetch all frames before training
        tdengine_config: Optional TDengine connection config
        **dataloader_kwargs: Additional arguments for DataLoader
        
    Returns:
        PyTorch DataLoader ready for training
        
    Example:
        >>> dataloader = create_dataloader(
        ...     'annotations.json',
        ...     '02:00:1a:62:51:67',
        ...     batch_size=16,
        ...     shuffle=True,
        ...     prefetch=True
        ... )
        >>> for frames, targets in dataloader:
        ...     # frames: (batch_size, 1, H, W)
        ...     # targets: list of dicts with boxes and labels
        ...     train_step(frames, targets)
    """
    # Create dataset
    dataset = ThermalAnnotationDataset(
        annotation_file=annotation_file,
        mac_address=mac_address,
        tdengine_config=tdengine_config,
        cache_frames=True  # Always enable cache for training
    )
    
    # Prefetch all frames if requested
    if prefetch:
        logger.info("Prefetching all frames into memory...")
        dataset.prefetch_all_frames()
    
    # Create DataLoader
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        collate_fn=collate_fn,
        **dataloader_kwargs
    )
    
    logger.info(f"Created DataLoader:")
    logger.info(f"  Batch size: {batch_size}")
    logger.info(f"  Shuffle: {shuffle}")
    logger.info(f"  Num workers: {num_workers}")
    logger.info(f"  Total batches: {len(dataloader)}")
    
    return dataloader


def collate_fn(batch: List[Tuple[torch.Tensor, Dict]]) -> Tuple[torch.Tensor, List[Dict]]:
    """
    Custom collate function for batching samples.
    
    Args:
        batch: List of (frame_tensor, target_dict) tuples
        
    Returns:
        Tuple of (batched_frames, list_of_targets)
        - batched_frames: (batch_size, 1, H, W)
        - list_of_targets: List of target dicts (varies by sample)
    """
    frames = []
    targets = []
    
    for frame, target in batch:
        frames.append(frame)
        targets.append(target)
    
    # Stack frames into batch
    frames_batch = torch.stack(frames, dim=0)
    
    return frames_batch, targets

