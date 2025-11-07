# Essential Features for Deep Learning Training Pipeline

## 🎯 Your Requirements

> "I need the features that can:
> 1. Read the annotation json files
> 2. Use the data_time in json file and mac address to fetch the raw thermal data from tdengine
> 3. The raw data and annotation json data will use for deep learning model training's data pipeline"

---

## ✅ ESSENTIAL FEATURES (Must Keep)

### 1. NEW: Automated Training Data Pipeline ⭐⭐⭐

**File**: `prepare_training_data.py` (NEW - 330 lines)

**What it does**:
- ✅ Reads annotation JSON files
- ✅ Extracts data_time timestamps from JSON
- ✅ Uses MAC address to fetch raw thermal data from TDengine
- ✅ Automatically converts timezone (LA/NY/UTC)
- ✅ Verifies 100% match between annotations and data
- ✅ Exports YOLO dataset ready for DL training

**Usage**:
```bash
uv run python prepare_training_data.py \
    --annotation your_annotations.json \
    --mac 02:00:1a:62:51:67 \
    --output training_data/session_001
```

**Output**: Complete YOLO dataset ready for training

---

### 2. Annotation JSON Reader

**File**: `src/visualize_annotations/loader.py`

**AnnotationLoader Class:**
- `load(annotation_path)` - Read JSON annotations
- `match_frame_to_annotation(frame_idx, timestamps)` - Match by data_time
- `get_category_id(category, subcategory)` - Category ID mapping

**Used by**: prepare_training_data.py, export_yolo_annotations.py

---

### 3. YOLO Dataset Exporter

**File**: `export_yolo_annotations.py`

**YOLOExporter Class:**
- `export_annotations()` - Export YOLO label files
- `export_frames_as_images()` - Export thermal images
- `_export_class_mapping()` - Create classes.txt
- `_export_dataset_info()` - Create dataset.yaml

**Used by**: prepare_training_data.py (called automatically)

---

### 4. Thermal Data Loader

**File**: `src/thermal_data_processing/data_loader.py`

**ThermalDataLoader Class:**
- `load_from_text_file(file_path)` - Load thermal data (deciKelvin format)
- `load_thermal_data(file_path)` - Auto-detect format and load

**Used by**: All visualization and export tools

---

### 5. TDengine Integration

**Files**:
- `dependent_tools/tdengine_export/tools/export_tool/export_thermal_data.py`
- `diagnose_tdengine.py` (diagnostic)
- `export_from_tdengine.sh` (helper)

**Features:**
- Fetch data from TDengine database
- MAC address-based queries
- Timezone conversion
- Epoch timestamp preservation

**Used by**: prepare_training_data.py (automatic), or manual export

---

## ⚠️ OPTIONAL FEATURES (For QA/Verification)

### 6. Video Export (QA Verification)

**File**: `create_annotation_video.py`

**Purpose**: Create videos to verify annotations before training

**Usage**:
```bash
# Verify your training data visually
uv run python create_annotation_video.py \
    --data training_data/session_001/raw_data/*.txt \
    --annotation your_annotations.json \
    --output qa_review.mp4
```

**Keep if**: You want to QA-review annotations before training  
**Remove if**: You trust your annotations

---

### 7. Visualization Module

**Files**: `src/visualize_annotations/visualizer.py`, `video_exporter.py`

**Purpose**: Render annotations on frames, create verification videos

**Keep if**: Using QA video verification  
**Remove if**: Only exporting YOLO datasets

---

## ❌ NOT NEEDED FOR DL TRAINING

### Can be Safely Removed:

1. **visualize_annotations.py** (292 lines)
   - Matplotlib interactive viewer
   - Redundant with video export
   - Not part of training pipeline

2. **visualize_raw_thermal.py** (150 lines)
   - No annotations
   - Not useful for training

3. **src/thermal_data_processing/streaming_data_loader.py** (257 lines)
   - SQS format support
   - Different data format
   - Not used in pipeline

4. **src/thermal_data_processing/frame_processor.py** (211 lines)
   - Advanced processing
   - Not needed for training prep

---

## 📊 Minimal Configuration for DL Training

### Keep Only These Files:

**Python Modules (5 files)**:
```
src/visualize_annotations/
├── __init__.py
└── loader.py           # Annotation reading

src/thermal_data_processing/
├── __init__.py
└── data_loader.py      # Thermal data loading
```

**Scripts (3 files)**:
```
prepare_training_data.py        # NEW - Main pipeline ⭐
export_yolo_annotations.py      # YOLO export
diagnose_tdengine.py            # Troubleshooting
```

**Helpers**:
```
export_from_tdengine.sh         # Manual TDengine export
```

**External**:
```
dependent_tools/tdengine_export/tools/export_tool/
```

**Total**: ~1,200 lines of code (50% reduction)

---

### With QA Verification (Recommended):

**Add these for quality assurance**:
```
create_annotation_video.py      # Video QA
src/visualize_annotations/
├── visualizer.py               # Rendering
└── video_exporter.py           # Video export
```

**Total**: ~1,600 lines of code (35% reduction)

---

## 🔄 Complete DL Training Workflow

### Step 1: Prepare Training Data (Automated)

```bash
uv run python prepare_training_data.py \
    --annotation Data/annotations/session_001.json \
    --mac 02:00:1a:62:51:67 \
    --output training_data/session_001
```

**What happens**:
1. Reads annotation JSON → extracts data_time
2. Queries TDengine with MAC + time range
3. Fetches raw thermal data
4. Verifies 100% match
5. Exports YOLO dataset

**Time**: ~1 minute

### Step 2: Optional QA Review

```bash
# Create verification video
uv run python prepare_training_data.py \
    --annotation Data/annotations/session_001.json \
    --thermal-data training_data/session_001/raw_data/*.txt \
    --output training_data/session_001_qa \
    --format video

# Review
open training_data/session_001_qa/video/training_data_preview.mp4
```

**Time**: ~30 seconds

### Step 3: Train Model

```bash
# YOLOv8
yolo train data=training_data/session_001/yolo/dataset.yaml \
    model=yolov8n.pt epochs=100
```

**Time**: Depends on dataset size and hardware

---

## 📦 Dependencies for DL Pipeline

### Python Packages (in pyproject.toml)

**Essential**:
```toml
dependencies = [
    "numpy>=2.3.3",           # Array operations
    "opencv-python>=4.11.0",  # Image processing
    "pytz>=2025.2",           # Timezone handling
    "pyyaml>=6.0",            # YAML config
    "requests>=2.32.0",       # HTTP requests
]
```

**Optional (for QA videos)**:
```toml
dependencies = [
    "matplotlib>=3.10.6",     # Visualization
    "tqdm>=4.67.1",           # Progress bars
]
```

**Not needed**:
```toml
# Can be removed if not using other features
"flask>=3.0.0",           # Web server (unused)
"pandas>=2.3.2",          # Data analysis (unused)
"scipy>=1.16.2",          # Scientific computing (unused)
"openpyxl>=3.1.5",        # Excel support (unused)
"psutil>=7.1.0",          # System utilities (unused)
```

---

## 🎯 Recommended Minimal Setup

For **pure DL training pipeline** without QA features:

### Keep (Essential Only):

**Modules**: 2 files (400 lines)
```
src/visualize_annotations/loader.py
src/thermal_data_processing/data_loader.py
```

**Scripts**: 3 files (900 lines)
```
prepare_training_data.py           # Main pipeline
export_yolo_annotations.py         # YOLO export
diagnose_tdengine.py               # Diagnostics
```

**Helpers**: 1 file
```
export_from_tdengine.sh
```

**External**: TDengine export tool

**Documentation**: 3 files
```
README.md
DL_TRAINING_PIPELINE.md
QUICK_START.md
```

**Total**: ~1,300 lines + documentation

---

### With QA Features (Recommended):

**Add**: Video export capability (600 lines)
```
create_annotation_video.py
src/visualize_annotations/visualizer.py
src/visualize_annotations/video_exporter.py
```

**Total**: ~1,900 lines + documentation

---

## 🎉 Summary

**You need these features for DL training**:

1. ✅ **prepare_training_data.py** (NEW)
   - Single command to prepare training data
   - Reads annotations, fetches from TDengine, exports YOLO

2. ✅ **Annotation reading** (loader.py)
   - Reads JSON, extracts data_time

3. ✅ **TDengine fetch** (export tools)
   - Gets raw data using MAC + data_time

4. ✅ **YOLO export** (export_yolo_annotations.py)
   - Creates training dataset

5. ⚠️ **Video QA** (optional, for verification)
   - create_annotation_video.py
   - Visualizer module

**Everything else can be removed** if not needed for other workflows.

---

**See also**:
- DL_TRAINING_PIPELINE.md - Complete pipeline documentation
- FEATURES_INVENTORY.md - Full feature analysis
- REFACTORING_GUIDE.md - Step-by-step refactoring instructions

