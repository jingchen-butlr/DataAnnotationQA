# Deep Learning Training Data Pipeline

## 🎯 Overview

This pipeline automates the process of preparing training data for deep learning models:

1. **Read annotation JSON files**
2. **Extract data_time timestamps**
3. **Fetch raw thermal data from TDengine** using MAC address
4. **Verify 100% match** between annotations and thermal frames
5. **Export in training-ready format** (YOLO dataset)

**Single Command**: Annotation JSON → TDengine → Training Dataset

---

## 🚀 Quick Start

### Basic Usage

```bash
uv run python prepare_training_data.py \
    --annotation Data/annotations/my_annotations.json \
    --mac 02:00:1a:62:51:67 \
    --output training_data/session_001
```

**This automatically:**
1. Reads your annotation JSON file
2. Extracts the time range from data_time fields
3. Fetches matching raw data from TDengine (MAC: 02:00:1a:62:51:67)
4. Verifies all annotations match thermal frames
5. Exports YOLO dataset ready for training

---

## 📋 Features

### 1. Annotation Reading

**Reads JSON annotation files**:
```json
{
  "data_time": 1760639220331,
  "annotations": [
    {
      "bbox": [0.3198, 0.7576, 0.185, 0.2517],
      "category": "person",
      "subcategory": "standing"
    }
  ]
}
```

**Extracts**:
- `data_time` timestamps (epoch milliseconds)
- Bounding boxes (YOLO format)
- Categories and subcategories
- Object IDs

### 2. Time Range Extraction

**Automatically calculates**:
- Minimum and maximum data_time from all annotations
- Adds configurable buffer (default: 5 seconds)
- Converts to query format

**Example**:
```
Annotations: 54
First: 2025-10-16 11:27:00.331
Last: 2025-10-16 11:27:59.207
Duration: 58.9 seconds
With buffer (5s): 2025-10-16 11:26:55 to 2025-10-16 11:28:04
```

### 3. TDengine Data Fetch

**Automatic fetch using**:
- MAC address (provided by user)
- Time range (extracted from annotations)
- Timezone conversion (LA/NY/UTC with automatic DST)

**Calls**:
```bash
dependent_tools/tdengine_export/tools/export_tool/export_thermal_data.py
  --mac 02:00:1a:62:51:67
  --start "2025-10-16 18:26:55"  # UTC (converted from LA)
  --end "2025-10-16 18:28:04"
  --output-multi output_file.txt
```

### 4. Match Verification

**Automatically verifies**:
- All annotations have matching thermal frames
- Matching tolerance: ±100ms
- Calculates match rate percentage

**Reports**:
```
Thermal frames: 414
Annotations: 54
Matched: 54/54
Match rate: 100.0%
✅ Perfect match! All annotations can be matched.
```

### 5. Training Dataset Export

**Exports YOLO dataset**:
```
training_data/session_001/
├── raw_data/
│   └── 02_00_1a_62_51_67_*.txt  # Raw thermal data
└── yolo/
    ├── labels/                  # YOLO annotation files
    │   ├── frame_0030.txt
    │   ├── frame_0039.txt
    │   └── ...
    ├── images/                  # Thermal PNG images
    │   ├── frame_0030.png
    │   ├── frame_0039.png
    │   └── ...
    ├── classes.txt              # Class names
    └── dataset.yaml             # YOLO configuration
```

**Ready for**:
- YOLOv5 training
- YOLOv8 training
- Custom model training
- Data augmentation

---

## 🎛️ Command-Line Options

### Required Arguments

```
--annotation PATH    Path to annotation JSON file
--output PATH        Output directory for training data
```

### Data Source (One Required)

```
--mac MAC               Sensor MAC address (fetch from TDengine)
                       Example: 02:00:1a:62:51:67

--thermal-data PATH    Use existing thermal data file
                       (skip TDengine fetch)
```

### Optional Arguments

```
--timezone TZ          Timezone for time conversion
                       Choices: LA, NY, UTC
                       Default: LA

--format FORMAT        Export format
                       Choices: yolo, video, both
                       Default: yolo

--buffer N            Buffer time in seconds
                       Added to both sides of time range
                       Default: 5

--skip-verify         Skip match verification step
```

---

## 📚 Usage Examples

### Example 1: Basic Training Data Preparation

Prepare YOLO dataset from annotations:

```bash
uv run python prepare_training_data.py \
    --annotation Data/annotations/session_001.json \
    --mac 02:00:1a:62:51:67 \
    --output training_data/session_001
```

**Output**:
- Raw data fetched from TDengine
- YOLO dataset exported
- Ready for model training

### Example 2: With Video Verification

Export both YOLO dataset and verification video:

```bash
uv run python prepare_training_data.py \
    --annotation Data/annotations/session_001.json \
    --mac 02:00:1a:62:51:67 \
    --output training_data/session_001 \
    --format both
```

**Output**:
- YOLO dataset in `training_data/session_001/yolo/`
- Verification video in `training_data/session_001/video/`

### Example 3: Custom Timezone

For data collected in New York:

```bash
uv run python prepare_training_data.py \
    --annotation Data/annotations/ny_session.json \
    --mac 02:00:1a:62:51:67 \
    --timezone NY \
    --output training_data/ny_session
```

### Example 4: Use Existing Thermal Data

If you already have thermal data file (skip TDengine):

```bash
uv run python prepare_training_data.py \
    --annotation Data/annotations/session_001.json \
    --thermal-data Data/existing_thermal.txt \
    --output training_data/session_001
```

### Example 5: Larger Time Buffer

For annotations with larger time gaps:

```bash
uv run python prepare_training_data.py \
    --annotation Data/annotations/session_001.json \
    --mac 02:00:1a:62:51:67 \
    --buffer 10 \
    --output training_data/session_001
```

---

## 🔄 Complete Workflow

### Typical DL Training Preparation

```bash
# Step 1: Prepare training data (automated)
uv run python prepare_training_data.py \
    --annotation Data/annotations/session_001.json \
    --mac 02:00:1a:62:51:67 \
    --output training_data/session_001 \
    --format both

# Step 2: Review video (QA check)
open training_data/session_001/video/training_data_preview.mp4

# Step 3: Use YOLO dataset for training
# training_data/session_001/yolo/ is ready for YOLOv8
```

---

## 📊 Pipeline Steps Explained

### Step 1: Read Annotation File

```python
# Reads JSON file line by line
annotations = []
with open(annotation_file, 'r') as f:
    for line in f:
        annotations.append(json.loads(line.strip()))

# Result: List of annotation dictionaries
```

### Step 2: Extract Time Range

```python
# Get all data_time values (milliseconds)
timestamps_ms = [ann['data_time'] for ann in annotations]

# Find min/max and add buffer
min_ts = min(timestamps_ms) / 1000.0
max_ts = max(timestamps_ms) / 1000.0

start_time = min_ts - buffer_seconds
end_time = max_ts + buffer_seconds

# Convert to datetime string for TDengine
start_str = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d %H:%M:%S")
end_str = datetime.fromtimestamp(end_time).strftime("%Y-%m-%d %H:%M:%S")
```

### Step 3: Fetch from TDengine

```python
# Automatically calls TDengine export tool
subprocess.run([
    "uv", "run", "python",
    "dependent_tools/tdengine_export/tools/export_tool/export_thermal_data.py",
    "--mac", mac_address,
    "--start", start_utc,  # Converted to UTC
    "--end", end_utc,
    "--output-multi", output_file
])
```

### Step 4: Verify Match

```python
# Match thermal frames to annotations by timestamp
matched = 0
for ann_timestamp in annotation_timestamps:
    for thermal_timestamp in thermal_timestamps:
        if abs(thermal_timestamp - ann_timestamp) < 0.1:  # ±100ms
            matched += 1
            break

match_rate = matched / total_annotations * 100
```

### Step 5: Export Training Data

```python
# Calls export_yolo_annotations.py
subprocess.run([
    "uv", "run", "python",
    "export_yolo_annotations.py",
    "--data", thermal_data_path,
    "--annotation", annotation_path,
    "--output-dir", output_dir,
    "--export-images",
    "--image-format", "png"
])
```

---

## 📁 Output Structure

### YOLO Dataset (Default)

```
training_data/session_001/
├── raw_data/
│   └── 02_00_1a_62_51_67_2025-10-16_11-26-55_2025-10-16_11-28-04.txt
│       # Raw thermal data (multi-frame format)
│       # 414 frames with epoch timestamps
│
└── yolo/
    ├── labels/              # YOLO format annotations
    │   ├── frame_0030.txt   # First annotated frame
    │   │   0 0.319792 0.757598 0.185000 0.251667  # furniture/chair
    │   │   1 0.237292 0.056764 0.116667 0.106667  # person/standing
    │   ├── frame_0039.txt
    │   └── ... (54 files total)
    │
    ├── images/              # Thermal images (PNG, grayscale)
    │   ├── frame_0000.png   # All frames (414 total)
    │   ├── frame_0001.png
    │   └── ...
    │
    ├── classes.txt          # Class names (6 classes)
    │   furniture/chair
    │   person/standing
    │   person/transition-lying with risk transition
    │   person/lying down-lying with risk
    │   object/cellphone
    │   person/lower position-kneeling
    │
    └── dataset.yaml         # YOLO dataset configuration
        path: /path/to/training_data/session_001/yolo
        train: labels
        val: labels
        nc: 6
        names:
          0: furniture/chair
          1: person/standing
          ...
```

---

## 🎓 Use Cases

### Use Case 1: Single Session Training Data

Prepare one annotation session for training:

```bash
uv run python prepare_training_data.py \
    --annotation Data/annotations/morning_session.json \
    --mac 02:00:1a:62:51:67 \
    --output training_data/morning_session
```

### Use Case 2: Batch Preparation

Prepare multiple sessions:

```bash
#!/bin/bash
for ann_file in Data/annotations/*.json; do
    session_name=$(basename "$ann_file" .json)
    uv run python prepare_training_data.py \
        --annotation "$ann_file" \
        --mac 02:00:1a:62:51:67 \
        --output "training_data/$session_name"
done
```

### Use Case 3: Quality Assurance

Prepare with video for QA review:

```bash
uv run python prepare_training_data.py \
    --annotation Data/annotations/session_001.json \
    --mac 02:00:1a:62:51:67 \
    --output training_data/session_001 \
    --format both

# Review video before training
open training_data/session_001/video/training_data_preview.mp4
```

### Use Case 4: From Pre-Exported Data

Use existing thermal data (bypass TDengine):

```bash
uv run python prepare_training_data.py \
    --annotation Data/annotations/session_001.json \
    --thermal-data exported_data/existing_data.txt \
    --output training_data/session_001
```

---

## 🔧 Integration with Training Frameworks

### YOLOv8 Training

```python
from ultralytics import YOLO

# Load model
model = YOLO('yolov8n.pt')

# Train on prepared dataset
model.train(
    data='training_data/session_001/yolo/dataset.yaml',
    epochs=100,
    imgsz=640,
    batch=16
)
```

### YOLOv5 Training

```bash
# Clone YOLOv5
git clone https://github.com/ultralytics/yolov5
cd yolov5

# Train
python train.py \
    --data ../training_data/session_001/yolo/dataset.yaml \
    --weights yolov5s.pt \
    --epochs 100 \
    --batch 16
```

### Custom PyTorch Training

```python
from torch.utils.data import Dataset, DataLoader
import cv2

class ThermalDataset(Dataset):
    def __init__(self, data_dir):
        self.images_dir = Path(data_dir) / "images"
        self.labels_dir = Path(data_dir) / "labels"
        self.image_files = sorted(self.images_dir.glob("*.png"))
    
    def __len__(self):
        return len(self.image_files)
    
    def __getitem__(self, idx):
        # Load image
        img_path = self.image_files[idx]
        image = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        
        # Load labels
        label_path = self.labels_dir / f"{img_path.stem}.txt"
        if label_path.exists():
            labels = []
            with open(label_path) as f:
                for line in f:
                    parts = line.strip().split()
                    class_id = int(parts[0])
                    bbox = [float(x) for x in parts[1:5]]
                    labels.append([class_id] + bbox)
            labels = torch.tensor(labels)
        else:
            labels = torch.zeros((0, 5))
        
        return image, labels

# Create dataset
dataset = ThermalDataset('training_data/session_001/yolo')
dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
```

---

## ⚙️ Configuration

### Timezone Handling

The pipeline supports automatic timezone conversion:

| Timezone | Code | DST | Example |
|----------|------|-----|---------|
| Los Angeles | LA | Auto (PST/PDT) | Oct: UTC-7, Jan: UTC-8 |
| New York | NY | Auto (EST/EDT) | Oct: UTC-4, Jan: UTC-5 |
| UTC | UTC | None | No conversion |

**Important**: Provide local time in command, conversion is automatic.

### Buffer Time

Buffer adds extra time on both sides of the annotation range:

- **Default**: 5 seconds
- **Purpose**: Ensure all frames are captured
- **Adjustable**: Use `--buffer N` flag

**Example**:
```
Annotations: 11:27:00 to 11:27:59
Buffer (5s): 11:26:55 to 11:28:04
Result: Extra frames before and after annotations
```

---

## 🔍 Troubleshooting

### Issue: TDengine Connection Error

```
Error: Failed to fetch from TDengine: Connection error
```

**Solution**:
```bash
# 1. Check connection
uv run python diagnose_tdengine.py

# 2. Verify MAC address
./export_from_tdengine.sh list

# 3. Try manual export
./export_from_tdengine.sh 02:00:1a:62:51:67 \
    '2025-10-16 11:27:00' '2025-10-16 11:28:00' LA
```

### Issue: Low Match Rate

```
⚠️ Warning: Low match rate! Only 80% matched.
```

**Solutions**:
1. Increase buffer: `--buffer 10`
2. Check time range is correct
3. Verify MAC address
4. Check if data exists in TDengine

### Issue: No Annotations Matched

```
❌ Poor match! Only 0% matched
```

**Solutions**:
1. Verify data_time is in milliseconds
2. Check thermal data has correct timestamps
3. Ensure MAC address is correct
4. Try wider buffer: `--buffer 30`

---

## 📊 Pipeline Components

### Components Used

**From this project**:
- ✅ `prepare_training_data.py` - Main pipeline script (NEW)
- ✅ `export_yolo_annotations.py` - YOLO dataset export
- ✅ `create_annotation_video.py` - Video creation (optional)
- ✅ `src/visualize_annotations/loader.py` - Annotation loading
- ✅ `src/thermal_data_processing/data_loader.py` - Thermal data loading

**External dependencies**:
- ✅ `dependent_tools/tdengine_export/` - TDengine data fetch
- ✅ pytz - Timezone conversion
- ✅ PyYAML - Configuration handling
- ✅ requests - HTTP requests

### Components NOT Used

**Not needed for training pipeline**:
- ❌ `visualize_annotations.py` - Interactive matplotlib viewer
- ❌ `visualize_raw_thermal.py` - Raw video export
- ❌ `streaming_data_loader.py` - SQS format
- ❌ `frame_processor.py` - Advanced processing

---

## 🎯 Core Features for DL Training

### Essential Components (KEEP for DL pipeline)

```
✅ prepare_training_data.py            # NEW - Main pipeline
✅ export_yolo_annotations.py          # YOLO export
✅ src/visualize_annotations/loader.py  # Annotation loading
✅ src/thermal_data_processing/data_loader.py  # Data loading
✅ dependent_tools/tdengine_export/    # Data fetch
✅ diagnose_tdengine.py                # Troubleshooting
✅ export_from_tdengine.sh             # Manual export
```

### Optional Components (for QA/verification)

```
⚠️ create_annotation_video.py          # Video QA
⚠️ src/visualize_annotations/visualizer.py  # Rendering
⚠️ src/visualize_annotations/video_exporter.py  # Video export
```

### Not Needed (can remove)

```
❌ visualize_annotations.py            # Redundant
❌ visualize_raw_thermal.py            # No annotations
❌ streaming_data_loader.py            # Different format
❌ frame_processor.py                  # Advanced features
```

---

## 💡 Advantages of This Pipeline

### vs Manual Process

| Task | Manual | Automated Pipeline |
|------|--------|-------------------|
| Find time range | Manual calculation | ✅ Auto-extracted |
| Convert timezone | Manual conversion | ✅ Auto-converted |
| Query TDengine | Multiple commands | ✅ Single command |
| Verify match | Manual checking | ✅ Auto-verified |
| Export dataset | Multiple steps | ✅ Single command |
| **Total time** | ~30 minutes | **~1 minute** |

### Benefits

1. **Automated**: One command does everything
2. **Error-free**: No manual timezone/time calculations
3. **Verified**: Automatic match checking
4. **Fast**: Complete pipeline in ~1 minute
5. **Consistent**: Same process every time
6. **Documented**: Clear logs and reports

---

## 🔬 Example Run

### Input

Annotation file with 54 annotations from 2025-10-16 11:27:00 to 11:27:59

### Command

```bash
uv run python prepare_training_data.py \
    --annotation Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json \
    --mac 02:00:1a:62:51:67 \
    --output training_data/SL18_R1_test
```

### Output

```
STEP 1: Read Annotation File
  ✅ Loaded 54 annotations

STEP 2: Extract Time Range
  First: 2025-10-16 11:27:00.331
  Last: 2025-10-16 11:27:59.207
  With buffer (5s): 2025-10-16 11:26:55 to 2025-10-16 11:28:04

STEP 3: Get Thermal Data
  MAC: 02:00:1a:62:51:67
  UTC query: 2025-10-16 18:26:55 to 2025-10-16 18:28:04
  ✅ Exported 414 frames

STEP 4: Verify Match
  Thermal frames: 414
  Annotations: 54
  Matched: 54/54
  ✅ Perfect match! (100%)

STEP 5: Export Training Dataset
  ✅ YOLO dataset exported
  - 414 images
  - 54 label files
  - 6 classes

✅ TRAINING DATA PIPELINE COMPLETE
Ready for deep learning model training!
```

---

## 🚀 Next Steps

1. **Review prepared dataset**:
   ```bash
   ls training_data/session_001/yolo/
   ```

2. **Verify with video** (optional):
   ```bash
   uv run python prepare_training_data.py \
       --annotation your_annotations.json \
       --thermal-data training_data/session_001/raw_data/*.txt \
       --output training_data/session_001_verified \
       --format video
   ```

3. **Start training**:
   ```bash
   # YOLOv8
   yolo train data=training_data/session_001/yolo/dataset.yaml model=yolov8n.pt epochs=100
   ```

---

## 📝 Summary

**New Feature**: `prepare_training_data.py`

**Purpose**: Automated DL training data preparation pipeline

**Input**: Annotation JSON + MAC address

**Output**: Training-ready YOLO dataset

**Key Features**:
- ✅ Reads annotation JSON files
- ✅ Extracts data_time timestamps
- ✅ Fetches matching raw data from TDengine using MAC
- ✅ Verifies 100% annotation-data match
- ✅ Exports YOLO format for training
- ✅ Handles timezone conversion automatically
- ✅ Single command operation

**Status**: ✅ Tested and working

---

**Created**: November 6, 2025  
**Version**: 1.0.0  
**Status**: Production Ready

