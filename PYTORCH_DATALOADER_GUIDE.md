# PyTorch Custom DataLoader for Thermal Sensor Data

## Overview

This module provides a PyTorch custom Dataset and DataLoader that:
1. **Reads annotation JSON files** (with `data_time` timestamps)
2. **Fetches raw thermal data from TDengine** using MAC address and timestamps
3. **Loads data directly into PC memory** (no disk files needed)
4. **Provides PyTorch tensors** ready for deep learning training

Reference: [PyTorch Custom Dataset Tutorial](https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html)

---

## Key Features

✅ **No Disk I/O** - Data fetched directly from TDengine into memory  
✅ **Automatic Timestamp Matching** - Uses `data_time` from JSON  
✅ **In-Memory Caching** - Caches fetched frames for performance  
✅ **Batch Prefetching** - Load all frames before training  
✅ **Standard PyTorch API** - Compatible with all PyTorch training code  
✅ **Custom Transforms** - Support for data augmentation  
✅ **YOLO Format** - Bounding boxes in YOLO format `[cx, cy, w, h]`  

---

## Installation

PyTorch is already included in dependencies:

```bash
uv sync
```

Dependencies added:
- torch >= 2.0.0
- requests >= 2.31.0
- pyyaml >= 6.0

---

## Quick Start

### Basic Usage

```python
from src.data_pipeline import ThermalAnnotationDataset

# Create dataset
dataset = ThermalAnnotationDataset(
    annotation_file='Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json',
    mac_address='02:00:1a:62:51:67',
    cache_frames=True
)

# Get a sample (fetches from TDengine automatically)
frame, target = dataset[0]

# frame: torch.Tensor of shape (1, 40, 60) - thermal image in Celsius
# target: Dict with 'boxes', 'labels', 'timestamp', 'num_objects'
```

### With DataLoader (Recommended)

```python
from src.data_pipeline import create_dataloader

# Create DataLoader with prefetching
dataloader = create_dataloader(
    annotation_file='Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json',
    mac_address='02:00:1a:62:51:67',
    batch_size=8,
    shuffle=True,
    prefetch=True  # Loads all frames into memory before training
)

# Use in training loop
for frames, targets in dataloader:
    # frames: (batch_size, 1, 40, 60)
    # targets: list of dicts with boxes and labels
    predictions = model(frames)
    loss = criterion(predictions, targets)
    # ... training code
```

---

## Module Structure

### src/data_pipeline/

```
src/data_pipeline/
├── __init__.py            # Package exports
└── thermal_dataset.py     # Main implementation
```

### Classes

**1. TDengineConnector**
- Connects to TDengine database
- Fetches frame data directly into memory
- Decompresses data from TDengine format
- No disk I/O

**2. ThermalAnnotationDataset** (PyTorch Dataset)
- Implements `__init__`, `__len__`, `__getitem__`
- Reads annotation JSON files
- Fetches thermal frames on-demand or prefetched
- Returns PyTorch tensors

**3. Helper Functions**
- `create_dataloader()` - Easy DataLoader creation
- `collate_fn()` - Custom batch collation

---

## API Reference

### ThermalAnnotationDataset

```python
class ThermalAnnotationDataset(Dataset):
    def __init__(self,
                 annotation_file: str,
                 mac_address: str,
                 tdengine_config: Optional[Dict] = None,
                 transform=None,
                 target_transform=None,
                 cache_frames: bool = True)
```

**Parameters:**
- `annotation_file`: Path to annotation JSON file (one JSON per line)
- `mac_address`: Sensor MAC address (e.g., "02:00:1a:62:51:67")
- `tdengine_config`: Optional TDengine connection config
- `transform`: Optional transform for thermal frames
- `target_transform`: Optional transform for annotations
- `cache_frames`: Whether to cache fetched frames (default: True)

**Methods:**

```python
def __len__() -> int
    # Returns number of annotations (samples)

def __getitem__(idx: int) -> Tuple[torch.Tensor, Dict]
    # Returns (frame_tensor, target_dict)
    # Fetches from TDengine if not cached

def prefetch_all_frames()
    # Prefetch all frames into memory (recommended for training)

def get_category_name(label_id: int) -> str
    # Get category name from label ID

def get_statistics() -> Dict
    # Get dataset statistics
```

---

## Data Format

### Input: Annotation JSON

```json
{
  "data_id": "SL18_R1",
  "data_time": 1760639220331,  ← Used to fetch from TDengine
  "annotations": [
    {
      "bbox": [0.3198, 0.7576, 0.185, 0.2517],  ← YOLO format
      "category": "furniture",
      "subcategory": "chair",
      "object_id": 0
    }
  ]
}
```

### Output: PyTorch Tensors

**Frame Tensor:**
```python
frame: torch.Tensor
  Shape: (1, 40, 60)  # (channels, height, width)
  Dtype: torch.float32
  Values: Temperature in Celsius
  Range: ~10°C to ~30°C
```

**Target Dictionary:**
```python
target: Dict {
  'boxes': torch.Tensor,      # Shape: (N, 4) - YOLO format [cx, cy, w, h]
  'labels': torch.Tensor,     # Shape: (N,) - category IDs
  'image_id': str,            # data_id from annotation
  'timestamp': int,           # data_time in milliseconds
  'num_objects': int,         # Number of objects in frame
}
```

---

## Usage Examples

### Example 1: Basic Dataset

```python
from src.data_pipeline import ThermalAnnotationDataset

# Create dataset
dataset = ThermalAnnotationDataset(
    annotation_file='annotations.json',
    mac_address='02:00:1a:62:51:67'
)

# Get info
print(f"Total samples: {len(dataset)}")
print(f"Categories: {dataset.category_to_id}")

# Get a sample (fetches from TDengine)
frame, target = dataset[0]

print(f"Frame shape: {frame.shape}")           # (1, 40, 60)
print(f"Temperature range: {frame.min():.1f}°C to {frame.max():.1f}°C")
print(f"Num objects: {target['num_objects']}")
print(f"Boxes: {target['boxes']}")             # (N, 4) YOLO format
print(f"Labels: {target['labels']}")           # (N,) category IDs
```

### Example 2: With Prefetching

```python
from src.data_pipeline import ThermalAnnotationDataset

dataset = ThermalAnnotationDataset(
    annotation_file='annotations.json',
    mac_address='02:00:1a:62:51:67',
    cache_frames=True
)

# Prefetch all frames into memory (recommended for training)
dataset.prefetch_all_frames()

# Now accessing samples is fast (from cache, no network queries)
for i in range(10):
    frame, target = dataset[i]  # Instant - from cache
```

### Example 3: Complete Training Loop

```python
from src.data_pipeline import create_dataloader
import torch.nn as nn
import torch.optim as optim

# Create DataLoader
dataloader = create_dataloader(
    annotation_file='annotations.json',
    mac_address='02:00:1a:62:51:67',
    batch_size=16,
    shuffle=True,
    prefetch=True  # Load all frames before training
)

# Setup model
model = YourDetectionModel()
optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = YourLossFunction()

# Training loop
for epoch in range(num_epochs):
    for batch_idx, (frames, targets) in enumerate(dataloader):
        # frames: (batch_size, 1, 40, 60) torch.Tensor
        # targets: list of dicts with boxes and labels
        
        optimizer.zero_grad()
        
        # Forward pass
        predictions = model(frames)
        
        # Calculate loss
        loss = criterion(predictions, targets)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        if batch_idx % 10 == 0:
            print(f"Epoch {epoch}, Batch {batch_idx}, Loss: {loss.item():.4f}")
```

### Example 4: Custom Transforms

```python
from src.data_pipeline import ThermalAnnotationDataset
import torch

# Define custom transform
def normalize_temperature(frame_tensor):
    """Normalize to [0, 1] range."""
    min_temp = 10.0
    max_temp = 30.0
    normalized = (frame_tensor - min_temp) / (max_temp - min_temp)
    return torch.clamp(normalized, 0.0, 1.0)

# Create dataset with transform
dataset = ThermalAnnotationDataset(
    annotation_file='annotations.json',
    mac_address='02:00:1a:62:51:67',
    transform=normalize_temperature
)

# Frames will be normalized
frame, target = dataset[0]
print(f"Normalized range: {frame.min():.3f} to {frame.max():.3f}")
```

### Example 5: Custom TDengine Configuration

```python
from src.data_pipeline import ThermalAnnotationDataset

# Custom TDengine connection
tdengine_config = {
    'host': '35.90.244.93',
    'port': 6041,
    'user': 'root',
    'password': 'taosdata',
    'database': 'thermal_sensors_pilot'
}

dataset = ThermalAnnotationDataset(
    annotation_file='annotations.json',
    mac_address='02:00:1a:62:51:67',
    tdengine_config=tdengine_config
)
```

---

## How It Works

### 1. Read Annotation JSON

```python
# annotation_file contains (one JSON per line):
{"data_id":"SL18_R1","data_time":1760639220331,"annotations":[...]}
{"data_id":"SL18_R1","data_time":1760639221458,"annotations":[...]}
...
```

### 2. Fetch Frame from TDengine

```python
# Uses data_time and MAC address:
timestamp_ms = 1760639220331
mac = "02:00:1a:62:51:67"

# Query TDengine:
# SELECT ts, frame_data FROM sensor_02_00_1a_62_51_67
# WHERE ts >= '2025-10-16 18:27:00.231' AND ts <= '2025-10-16 18:27:00.431'
# (±100ms tolerance)
```

### 3. Decompress Data in Memory

```python
# TDengine stores compressed data:
compressed_data (hex/base64)
  → decode to bytes
  → zlib.decompress()
  → struct.unpack()
  → numpy.array (deciKelvin)
  → convert to Celsius
  → reshape to (40, 60)
  → np.fliplr() for correct orientation
  → torch.Tensor

# All in memory - NO disk writes!
```

### 4. Return Training-Ready Tensors

```python
frame_tensor: torch.Size([1, 40, 60])  # Ready for CNN
target_dict: {
    'boxes': torch.Size([N, 4]),        # YOLO format bboxes
    'labels': torch.Size([N]),          # Category IDs
    'timestamp': int,                   # For tracking
}
```

---

## Performance

### Memory Usage

- **Per frame**: ~10 KB (40×60 float32)
- **54 frames**: ~540 KB
- **Cache all**: <1 MB
- **Batch (16 frames)**: ~160 KB

### Speed

- **Single frame fetch**: ~100ms (network query)
- **With cache**: <1ms (instant)
- **Prefetch 54 frames**: ~3 seconds
- **Training iteration**: Depends on model

### Optimization

**For Training** (Recommended):
```python
# Prefetch all frames once at start
dataloader = create_dataloader(..., prefetch=True)

# Then training is fast (all from memory cache)
for epoch in range(100):
    for frames, targets in dataloader:
        # Fast - no network queries
        train_step(frames, targets)
```

**For Large Datasets**:
```python
# Don't prefetch - fetch on demand
dataset = ThermalAnnotationDataset(..., cache_frames=True)

# Frames cached as accessed
for i in range(len(dataset)):
    frame, target = dataset[i]  # Cached after first access
```

---

## Integration with Training Frameworks

### PyTorch (Native)

```python
from src.data_pipeline import create_dataloader

dataloader = create_dataloader(
    'annotations.json',
    '02:00:1a:62:51:67',
    batch_size=16,
    shuffle=True
)

for frames, targets in dataloader:
    # Standard PyTorch training
    outputs = model(frames)
    loss = criterion(outputs, targets)
```

### PyTorch Lightning

```python
import pytorch_lightning as pl
from src.data_pipeline import ThermalAnnotationDataset

class ThermalDataModule(pl.LightningDataModule):
    def train_dataloader(self):
        dataset = ThermalAnnotationDataset(
            'train_annotations.json',
            '02:00:1a:62:51:67'
        )
        return DataLoader(dataset, batch_size=16)
```

### YOLO

```python
from src.data_pipeline import ThermalAnnotationDataset

# YOLO expects specific format
class YOLOThermalDataset(ThermalAnnotationDataset):
    def __getitem__(self, idx):
        frame, target = super().__getitem__(idx)
        # Convert to YOLO training format
        return frame, target['boxes'], target['labels']
```

---

## Comparison with File-Based Approach

### Traditional (File-Based)

```python
# 1. Export from TDengine to disk
./export_from_tdengine.sh mac start end tz
# Creates: exported_data/MAC_START_END/thermal_data.txt (163 MB)

# 2. Load from disk file
from src.thermal_data_processing import ThermalDataLoader
loader = ThermalDataLoader()
frames, timestamps = loader.load_from_text_file('thermal_data.txt')

# 3. Use in training
# ... manual batching and matching
```

**Drawbacks:**
- ❌ Requires 163 MB disk space per export
- ❌ Two-step process (export then load)
- ❌ Data duplication (database + disk)
- ❌ Manual timestamp matching needed

### New (Memory-Based)

```python
# 1. Create DataLoader (no disk files)
from src.data_pipeline import create_dataloader

dataloader = create_dataloader(
    'annotations.json',
    '02:00:1a:62:51:67',
    prefetch=True
)

# 2. Use directly in training
for frames, targets in dataloader:
    # Ready to use!
    train_step(frames, targets)
```

**Benefits:**
- ✅ No disk space needed
- ✅ One-step process
- ✅ No data duplication
- ✅ Automatic timestamp matching
- ✅ Faster setup

---

## TDengine Integration Details

### Connection

```python
# Default connection (can be customized)
TDengineConnector(
    host='35.90.244.93',
    port=6041,
    user='root',
    password='taosdata',
    database='thermal_sensors_pilot'
)
```

### Data Fetching

**Single Frame:**
```python
connector.query_frame_by_timestamp(
    mac_address='02:00:1a:62:51:67',
    timestamp_ms=1760639220331,  # From annotation data_time
    tolerance_ms=100             # ±100ms window
)
```

**Batch Query:**
```python
connector.batch_query_frames(
    mac_address='02:00:1a:62:51:67',
    timestamps_ms=[1760639220331, 1760639221458, ...],
    tolerance_ms=100
)
```

### Data Decompression

TDengine stores compressed data:

```python
# Stored: Hex/base64 encoded + zlib compressed
# Format: int16 (deciKelvin) or float32 (Celsius)

# Decompression pipeline:
1. Decode hex/base64 → bytes
2. zlib.decompress() → raw bytes
3. struct.unpack() → list of values
4. Convert deciKelvin to Celsius (if needed)
5. Reshape to (40, 60)
6. np.fliplr() for correct orientation
7. → numpy.array → torch.Tensor

# All in memory!
```

---

## Testing

### Run Examples

```bash
# Test all features
uv run python example_training_pipeline.py
```

**Examples included:**
1. Basic Dataset usage
2. Prefetch all frames
3. PyTorch DataLoader iteration
4. Training loop skeleton
5. Custom transforms

### Verify Connection

```bash
# Test TDengine connection first
uv run python diagnose_tdengine.py
```

---

## Troubleshooting

### Issue: Frame Not Found

```
Frame not found for timestamp 1760639220331
```

**Solution:**
- Check TDengine has data for that MAC address
- Verify timestamp is in database time range
- Run: `./export_from_tdengine.sh list`

### Issue: Connection Error

```
Connection error: ...
```

**Solution:**
- Run diagnostic: `uv run python diagnose_tdengine.py`
- Check network connectivity
- Verify TDengine server status

### Issue: Out of Disk Space

```
Query failed: Out of disk space
```

**Solution:**
- This is TDengine server issue (not local)
- Contact server administrator
- See: TDENGINE_TROUBLESHOOTING.md

### Issue: Slow Performance

**Solution:**
```python
# Always prefetch for training
dataloader = create_dataloader(..., prefetch=True)

# This loads all frames once at start
# Then training is fast from cache
```

---

## Advanced Features

### Custom Collate Function

```python
def custom_collate(batch):
    frames, targets = zip(*batch)
    # Custom batching logic
    return torch.stack(frames), list(targets)

dataloader = DataLoader(
    dataset,
    batch_size=8,
    collate_fn=custom_collate
)
```

### Data Augmentation

```python
import torch
import torchvision.transforms as T

# Define transforms
transform = T.Compose([
    T.Lambda(lambda x: (x - x.mean()) / x.std()),  # Normalize
    T.Lambda(lambda x: x + torch.randn_like(x) * 0.01),  # Add noise
])

dataset = ThermalAnnotationDataset(
    'annotations.json',
    '02:00:1a:62:51:67',
    transform=transform
)
```

### Subset Selection

```python
from torch.utils.data import Subset

dataset = ThermalAnnotationDataset(...)

# Use first 40 samples for training, rest for validation
train_dataset = Subset(dataset, range(40))
val_dataset = Subset(dataset, range(40, len(dataset)))

train_loader = DataLoader(train_dataset, batch_size=8)
val_loader = DataLoader(val_dataset, batch_size=8)
```

---

## Benefits for Deep Learning

### 1. Memory Efficient

- Only loads frames as needed
- Cache only what's used
- No large disk files

### 2. Flexible

- Works with any annotation JSON
- Query any MAC address
- Custom transforms supported

### 3. Standard API

- Compatible with all PyTorch training code
- Works with PyTorch Lightning
- Integrates with existing tools

### 4. Real-Time Data

- Always fetches latest data from TDengine
- No stale disk files
- Easy to update with new annotations

---

## Comparison with PyTorch Tutorial

Following the [PyTorch Custom Dataset Tutorial](https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html):

### Required Methods ✅

```python
class ThermalAnnotationDataset(Dataset):
    def __init__(self, annotation_file, mac_address, ...):
        # Load annotations (like CSV in tutorial)
        # Setup TDengine connector (like image directory)
        
    def __len__(self):
        # Return number of annotations
        return len(self.annotations)
    
    def __getitem__(self, idx):
        # Fetch thermal frame from TDengine (like loading image)
        # Return (frame_tensor, target_dict)
```

### Tutorial Pattern vs Our Implementation

| Tutorial | Our Implementation |
|----------|-------------------|
| `pd.read_csv(annotations_file)` | `json.loads()` for each line |
| `Image directory` | TDengine database |
| `decode_image(img_path)` | `query_frame_by_timestamp()` |
| Return `(image, label)` | Return `(frame, target_dict)` |
| Disk I/O | Network I/O + Memory |

---

## Next Steps

1. **Test the DataLoader**:
   ```bash
   uv run python example_training_pipeline.py
   ```

2. **Integrate with your model**:
   ```python
   dataloader = create_dataloader('annotations.json', 'MAC')
   for frames, targets in dataloader:
       train_your_model(frames, targets)
   ```

3. **Add data augmentation** as needed

4. **Monitor memory** usage during training

---

**Module**: `src/data_pipeline/`  
**Reference**: [PyTorch Custom Dataset Tutorial](https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html)  
**Status**: ✅ Ready for deep learning training  
**Date**: November 6, 2025

