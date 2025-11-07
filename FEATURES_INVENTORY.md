# Complete Features and Functions Inventory

This document lists all functions and features in the DataAnnotationQA project for refactoring reference.

---

## 📦 Core Modules (src/)

### 1. src/visualize_annotations/ (Main Visualization Package)

#### loader.py

**ThermalDataLoader Class:**
- `load(data_path)` - Load thermal data from text files
- `get_frame(idx)` - Get specific frame by index
- `get_timestamp(idx)` - Get timestamp for specific frame

**AnnotationLoader Class:**
- `load(annotation_path)` - Load annotations from JSON files
- `get_category_id(category, subcategory)` - Get or create category ID
- `match_frame_to_annotation(frame_idx, timestamps, tolerance_ms=100)` - Match frames to annotations by timestamp

**Purpose**: Load and manage thermal data and annotations

#### visualizer.py

**AnnotationVisualizer Class:**
- `normalize_frame_for_display(frame, vmin, vmax)` - Normalize temperature to 8-bit grayscale
- `draw_bbox(image, bbox, color)` - Draw bounding box on image (YOLO format → pixels)
- `draw_label(image, bbox, label_text, color)` - Draw label text near bounding box
- `draw_timestamp(image, timestamp, frame_idx)` - Draw timestamp overlay
- `visualize_frame(frame, annotation, timestamp, frame_idx, vmin, vmax)` - Create complete annotated frame
- `create_legend(categories, width, height)` - Create category color legend

**Purpose**: Render annotations on thermal frames with proper scaling

#### video_exporter.py

**VideoExporter Class:**
- `load_data(data_path, annotation_path)` - Load both thermal data and annotations
- `export_video(output_path, start_frame, num_frames, codec)` - Export annotated video (MP4, AVI, etc.)
- `export_frames_as_images(output_dir, start_frame, num_frames, image_format)` - Export as image sequence
- `create_summary_report(output_path)` - Generate dataset statistics report
- `_calculate_temperature_range(start_frame, end_frame)` - Calculate normalization range

**Purpose**: Export annotated data as videos or image sequences

---

### 2. src/thermal_data_processing/ (Data Loading Utilities)

#### data_loader.py

**ThermalDataLoader Class:**
- `load_from_text_file(file_path)` - Load thermal data from TXT format (deciKelvin)
- `load_from_numpy(file_path)` - Load from .npy or .npz files
- `load_from_csv(file_path)` - Load from CSV files
- `load_thermal_data(file_path)` - Auto-detect format and load
- `save_thermal_data(frames, file_path, file_format)` - Save to various formats

**Purpose**: Universal thermal data loader supporting multiple formats

#### frame_processor.py

**FrameDataProcessor Class (Abstract):**
- `process_frame(frame, **kwargs)` - Process single frame (abstract)
- `process_batch(frames, **kwargs)` - Process batch of frames (abstract)

**ThermalFrameDataProcessor Class:**
- `convert_temperature(value, from_unit, to_unit)` - Convert between Kelvin, Celsius, Fahrenheit, deciKelvin
- `validate_frame_shape(frame)` - Validate frame dimensions
- `process_frame(frame, convert_to)` - Process single frame with temperature conversion
- `process_batch(frames, convert_to)` - Batch process frames
- `calculate_mean_frame(frames)` - Calculate mean/average frame
- `calculate_frame_statistics(frame)` - Get min/max/mean/std statistics

**Purpose**: Temperature conversion and frame processing utilities

#### streaming_data_loader.py

**StreamingDataLoader Class:**
- `parse_timestamp_from_filename(filename)` - Extract timestamp from SQS filename format
- `load_frame_from_file(file_path)` - Load single frame from SQS file
- `get_files_in_time_range(directory, duration_minutes)` - Filter files by time range
- `load_streaming_data(directory, duration_minutes, start_time)` - Load SQS streaming data

**Purpose**: Load thermal data from AWS SQS streaming format

---

## 🎬 Main Scripts (Root Directory)

### 1. create_annotation_video.py (PRIMARY VIDEO TOOL)

**Main Features:**
- Create annotated videos from thermal data
- Export annotated frames as images
- Support for frame range selection
- Configurable FPS, scale factor, codec
- Summary report generation

**Key Functions:**
- `main()` - CLI interface with argparse

**Usage:**
```bash
uv run python create_annotation_video.py [OPTIONS]
```

**Options:**
- `--data PATH` - Thermal data file
- `--annotation PATH` - Annotation file
- `--output PATH` - Output video file
- `--start-frame N` - Starting frame
- `--num-frames N` - Number of frames
- `--fps N` - Frames per second
- `--scale N` - Scale factor (default: 8)
- `--codec CODEC` - Video codec (mp4v, avc1, etc.)
- `--export-images` - Export as images instead
- `--image-format FORMAT` - png or jpg
- `--create-summary` - Generate summary report

**Depends on:**
- src/visualize_annotations/VideoExporter

---

### 2. visualize_annotations.py (MATPLOTLIB VISUALIZER)

**Main Features:**
- Interactive frame visualization with matplotlib
- YOLO format annotation display
- Print YOLO format to console
- Save high-quality matplotlib figures
- View multiple frames sequentially

**Classes:**

**AnnotationConverter:**
- `yolo_to_corner(yolo_bbox)` - Convert YOLO center to corner format
- `get_category_id(category, subcategory)` - Manage category IDs
- `get_annotation_for_yolo(annotation)` - Get annotation in YOLO format
- `format_yolo_line(class_id, yolo_bbox)` - Format YOLO line string

**AnnotationVisualizer:**
- `visualize_frame(frame_idx, save_path, show_yolo_format)` - Visualize single frame with matplotlib
- `visualize_multiple_frames(start_idx, num_frames, output_dir)` - Visualize multiple frames

**Usage:**
```bash
uv run python visualize_annotations.py [OPTIONS]
```

**Options:**
- `--data PATH` - Thermal data file
- `--annotation PATH` - Annotation file
- `--frame N` - Frame index to visualize
- `--num-frames N` - Number of frames
- `--output-dir PATH` - Save directory

**Depends on:**
- matplotlib for plotting
- src/thermal_data_processing/ThermalDataLoader

---

### 3. export_yolo_annotations.py (YOLO DATASET EXPORT)

**Main Features:**
- Export annotations to YOLO format
- Generate class mapping files
- Create YOLO dataset configuration
- Export thermal frames as images
- Batch export all annotations

**YOLOExporter Class:**
- `get_category_id(category, subcategory)` - Get/create YOLO class ID
- `export_annotations()` - Export all annotations to YOLO label files
- `export_frames_as_images(output_format)` - Export frames as NPY or PNG
- `_find_frame_by_timestamp(annotation_timestamp_ms)` - Match annotation to frame
- `_export_class_mapping()` - Create classes.txt file
- `_export_dataset_info()` - Create dataset.yaml file

**Usage:**
```bash
uv run python export_yolo_annotations.py [OPTIONS]
```

**Options:**
- `--data PATH` - Thermal data file
- `--annotation PATH` - Annotation file
- `--output-dir PATH` - Output directory (default: output/yolo_format)
- `--export-images` - Export frames too
- `--image-format FORMAT` - npy or png

**Output:**
- `labels/*.txt` - YOLO format annotation files
- `images/*.png` - Thermal frame images
- `classes.txt` - Class names mapping
- `dataset.yaml` - YOLO dataset configuration

**Depends on:**
- src/thermal_data_processing/ThermalDataLoader

---

### 4. diagnose_tdengine.py (DIAGNOSTIC TOOL)

**Main Features:**
- Test TDengine server connection
- Verify authentication
- Check database access
- Test table queries
- Identify connection issues

**Functions:**
- `check_server_status(host, port)` - Test server reachability
- `test_connection(host, port, user, password)` - Test basic connection
- `test_database_access(host, port, user, password, database)` - Test database access
- `test_table_access(host, port, user, password, database)` - Test table queries
- `test_sample_query(host, port, user, password, database)` - Test sample data retrieval
- `print_summary(passed, total)` - Display diagnostic results

**Usage:**
```bash
uv run python diagnose_tdengine.py
```

**Purpose**: Troubleshoot TDengine connection issues

---

### 5. visualize_raw_thermal.py (RAW VISUALIZER)

**Main Features:**
- Visualize thermal data WITHOUT annotations
- Create videos from raw thermal data only
- Export frames without overlays

**RawThermalVisualizer Class:**
- `load_data(data_path)` - Load thermal data
- `export_video(output_path, start_frame, num_frames, fps, scale_factor)` - Export raw video
- `export_frames_as_images(output_dir, start_frame, num_frames, image_format)` - Export raw frames

**Usage:**
```bash
uv run python visualize_raw_thermal.py [OPTIONS]
```

**Purpose**: Create videos without annotations for comparison

---

## 🔧 Helper Scripts

### 1. export_from_tdengine.sh (TDENGINE EXPORT WRAPPER)

**Features:**
- Wrapper around TDengine export tool
- Automatic output directory naming
- Timezone conversion helper
- List available sensors
- Help and usage information

**Usage:**
```bash
./export_from_tdengine.sh <MAC> <START_TIME> <END_TIME> [TIMEZONE]
./export_from_tdengine.sh list
./export_from_tdengine.sh help
```

**Purpose**: Simplified interface for TDengine data export

---

## 🛠️ External Tools (dependent_tools/)

### tdengine_export/ (Cloned Repository)

**Location**: `dependent_tools/tdengine_export/`

**Key Tools:**
- `tools/export_tool/export_thermal_data.py` - Core export script
- `tools/export_tool/quick_export.sh` - Quick export shell script
- `tools/export_tool/batch_export.py` - Batch export with YAML config
- `tdengine_exporter.py` - Main exporter with list-sensors feature

**Features:**
- Export from TDengine database
- Single-frame and multi-frame formats
- Timezone conversion (LA, NY, UTC)
- Automatic DST handling
- Anomalous frame filtering
- Batch export configuration
- List available sensors
- Query sensor time distribution

**Not integrated**: Many tools in this repo are standalone utilities

---

## 📊 Feature Categorization

### 🎥 Video Export Features (CORE)

**Priority: HIGH - Main project purpose**

1. **create_annotation_video.py** ⭐ PRIMARY
   - Video export with annotations
   - Image sequence export
   - Frame range selection
   - Configurable output settings

2. **src/visualize_annotations/** ⭐ CORE MODULE
   - All classes and methods
   - Professional implementation
   - Well-tested and documented

**Keep**: ✅ Essential for project

---

### 📈 YOLO Format Features (IMPORTANT)

**Priority: MEDIUM-HIGH - ML training support**

1. **export_yolo_annotations.py**
   - YOLO dataset export
   - Class mapping generation
   - Dataset configuration

2. **YOLO bbox handling** (in visualizers)
   - Correct center coordinate conversion
   - YOLO format validation

**Keep**: ✅ Useful for ML training

---

### 🔍 Visualization Features (UTILITY)

**Priority: MEDIUM - Alternative visualization**

1. **visualize_annotations.py** (matplotlib-based)
   - Interactive single frame view
   - YOLO format console output
   - High-quality matplotlib figures
   - Multiple frame export

**Consider**: 
- ⚠️ Redundant with create_annotation_video.py for video
- ✅ Useful for single frame inspection
- 🤔 **Decision**: Keep for interactive exploration, or merge into main tool?

---

### 🗄️ TDengine Integration (EXTERNAL)

**Priority: HIGH - Data source**

1. **dependent_tools/tdengine_export/** (external repo)
   - Full TDengine export tool
   - Many utilities not currently used

2. **export_from_tdengine.sh** (wrapper)
   - Simplified interface
   - Auto-formatting

3. **diagnose_tdengine.py**
   - Connection diagnostics
   - Error troubleshooting

**Consider**:
- ✅ Keep wrapper script and diagnostic
- 🤔 **Decision**: Keep external repo as-is (in .gitignore), or extract only needed parts?

---

### 📁 Data Loading Utilities (UTILITY)

**Priority: MEDIUM - Support multiple formats**

1. **src/thermal_data_processing/data_loader.py**
   - Load from TXT (deciKelvin)
   - Load from NumPy (.npy, .npz)
   - Load from CSV
   - Save to various formats

2. **src/thermal_data_processing/streaming_data_loader.py**
   - Load SQS streaming format
   - Parse timestamps from filenames
   - Time range filtering

3. **src/thermal_data_processing/frame_processor.py**
   - Temperature unit conversion
   - Frame statistics calculation
   - Mean frame calculation
   - Frame validation

**Consider**:
- ✅ data_loader.py - Used by visualizers (KEEP)
- ⚠️ streaming_data_loader.py - Not currently used
- ⚠️ frame_processor.py - Advanced features not used
- 🤔 **Decision**: Keep data_loader, consider removing unused modules?

---

### 🎨 Raw Visualization (LOW PRIORITY)

**Priority: LOW - No annotations**

1. **visualize_raw_thermal.py**
   - Visualize without annotations
   - Export videos without overlays

**Consider**:
- ⚠️ Limited use case
- 🤔 **Decision**: Remove or keep as utility?

---

## 📋 Feature Usage Analysis

### ✅ ACTIVELY USED

1. **Video Export with Annotations** ⭐
   - create_annotation_video.py
   - src/visualize_annotations/
   - **Usage**: Primary workflow

2. **YOLO Dataset Export** ⭐
   - export_yolo_annotations.py
   - **Usage**: ML training preparation

3. **TDengine Data Export** ⭐
   - export_from_tdengine.sh
   - dependent_tools/tdengine_export/tools/export_tool/
   - **Usage**: Get raw data from database

4. **Data Loading** ⭐
   - src/thermal_data_processing/data_loader.py
   - **Usage**: Used by all visualizers

5. **Diagnostics** ⭐
   - diagnose_tdengine.py
   - **Usage**: Troubleshooting

---

### ⚠️ PARTIALLY USED / REDUNDANT

1. **visualize_annotations.py** (matplotlib)
   - Alternative to create_annotation_video.py
   - Provides YOLO console output
   - Interactive frame viewing
   - **Consider**: Merge features into main tool or keep for interactive use?

2. **visualize_raw_thermal.py**
   - No annotations
   - Limited use case
   - **Consider**: Remove or keep as comparison tool?

---

### ❌ NOT CURRENTLY USED

1. **src/thermal_data_processing/streaming_data_loader.py**
   - SQS format support
   - Not used in any current workflow
   - **Consider**: Remove unless needed for future SQS data?

2. **src/thermal_data_processing/frame_processor.py**
   - Advanced processing features
   - Temperature conversion utilities
   - Not used in current visualizers
   - **Consider**: Remove or keep for future features?

3. **TDengine tools** (most of dependent_tools/)
   - Many utilities: backup, cloudwatch, analysis, import
   - Only using export_tool
   - **Consider**: Keep only export_tool or reference external repo?

---

## 🎯 Refactoring Recommendations

### Option 1: Minimal (Keep Core Only)

**Keep:**
- ✅ src/visualize_annotations/ (all 4 files)
- ✅ src/thermal_data_processing/data_loader.py
- ✅ create_annotation_video.py
- ✅ export_yolo_annotations.py
- ✅ export_from_tdengine.sh
- ✅ diagnose_tdengine.py
- ✅ Essential documentation (README, QUICK_START, VIDEO_EXPORT_GUIDE)

**Remove:**
- ❌ visualize_annotations.py (redundant)
- ❌ visualize_raw_thermal.py (rarely used)
- ❌ src/thermal_data_processing/streaming_data_loader.py (unused)
- ❌ src/thermal_data_processing/frame_processor.py (unused)
- ❌ dependent_tools/ (reference external repo instead)
- ❌ Extra documentation (keep main guides only)

**Result**: ~60% reduction in code, keeps all essential features

---

### Option 2: Keep All Current Features

**Keep Everything:**
- ✅ All modules (for flexibility)
- ✅ All scripts (different use cases)
- ✅ All documentation (comprehensive)

**Add:**
- Documentation on when to use each tool
- Usage examples for each module
- Feature comparison table

**Result**: Full-featured system, more maintenance

---

### Option 3: Modular Packages

**Restructure into separate packages:**

```
src/
├── core/              # Essential functionality
│   ├── data_loader.py
│   └── annotation_loader.py
│
├── visualization/     # All visualization features
│   ├── video_export.py
│   ├── frame_renderer.py
│   └── yolo_export.py
│
├── processing/        # Data processing utilities
│   ├── temperature.py
│   └── statistics.py
│
└── integration/       # External integrations
    ├── tdengine.py
    └── diagnostics.py
```

**Result**: Better organization, easier to maintain

---

## 📊 Feature Comparison Matrix

| Feature | Script | Priority | Used | Keep? |
|---------|--------|----------|------|-------|
| Video with annotations | create_annotation_video.py | ⭐⭐⭐ | Yes | ✅ YES |
| YOLO dataset export | export_yolo_annotations.py | ⭐⭐⭐ | Yes | ✅ YES |
| TDengine export | export_from_tdengine.sh | ⭐⭐⭐ | Yes | ✅ YES |
| Connection diagnostic | diagnose_tdengine.py | ⭐⭐ | Yes | ✅ YES |
| Matplotlib viz | visualize_annotations.py | ⭐ | Partial | ⚠️ MAYBE |
| Raw video export | visualize_raw_thermal.py | ⭐ | Rarely | ❌ NO |
| Data loader (TXT) | data_loader.py | ⭐⭐⭐ | Yes | ✅ YES |
| Streaming loader | streaming_data_loader.py | ⭐ | No | ❌ NO |
| Frame processor | frame_processor.py | ⭐ | No | ❌ NO |
| Visualization module | src/visualize_annotations/ | ⭐⭐⭐ | Yes | ✅ YES |

---

## 🗂️ File Size Analysis

```bash
# Module sizes
src/visualize_annotations/
  - loader.py: 193 lines
  - visualizer.py: 290 lines
  - video_exporter.py: 246 lines
  - __init__.py: 16 lines
  TOTAL: 745 lines

src/thermal_data_processing/
  - data_loader.py: 219 lines
  - streaming_data_loader.py: 257 lines (❌ unused)
  - frame_processor.py: 211 lines (❌ unused)
  - __init__.py: 1 line
  TOTAL: 688 lines (468 unused)

# Scripts
  - create_annotation_video.py: 181 lines ⭐
  - visualize_annotations.py: 292 lines ⚠️
  - export_yolo_annotations.py: 278 lines ⭐
  - diagnose_tdengine.py: 305 lines ⭐
  - visualize_raw_thermal.py: ~150 lines ❌
  TOTAL: ~1,206 lines (150 removable)

# Documentation
  11 .md files: ~4,000 lines
  (May consolidate to 5-6 key guides)
```

---

## 💡 Specific Recommendations

### Definitely Keep (Core Functionality)

1. **src/visualize_annotations/** (all 4 files)
   - Professional implementation
   - Well-tested
   - Main project feature

2. **src/thermal_data_processing/data_loader.py**
   - Used by all visualizers
   - Supports multiple formats
   - Essential utility

3. **create_annotation_video.py**
   - Primary user interface
   - Most-used script
   - Complete feature set

4. **export_yolo_annotations.py**
   - YOLO format export
   - ML training support
   - Unique functionality

5. **export_from_tdengine.sh + diagnose_tdengine.py**
   - TDengine integration
   - Data source access
   - Diagnostic support

### Consider Removing (Unused/Redundant)

1. **src/thermal_data_processing/streaming_data_loader.py**
   - 257 lines
   - Not used in any workflow
   - SQS format not needed currently

2. **src/thermal_data_processing/frame_processor.py**
   - 211 lines
   - Advanced features not used
   - Temperature conversion available elsewhere

3. **visualize_raw_thermal.py**
   - ~150 lines
   - No annotations = limited value
   - Same functionality in main tool with `--annotation` omitted

4. **visualize_annotations.py**
   - 292 lines
   - Redundant with create_annotation_video.py
   - BUT: Provides matplotlib interactive viewing
   - **Decision**: Keep if interactive matplotlib viewing needed

### Documentation Consolidation

**Current**: 11 markdown files (~4,000 lines)

**Consolidate to**:
1. README.md - Overview and quick start
2. USER_GUIDE.md - Complete usage guide
3. API_REFERENCE.md - Module API documentation
4. TROUBLESHOOTING.md - Common issues
5. CHANGELOG.md - Version history

**Remove**:
- BBOX_FORMAT_CORRECTION.md (historical, issue fixed)
- TEXT_RENDERING_FIX.md (historical, issue fixed)
- SUMMARY.md (superseded by FINAL_SUMMARY)
- Multiple partial guides

---

## 📊 Summary Statistics

### Current State

- **Python modules**: 8 files (745 + 688 = 1,433 lines)
- **Unused code**: ~470 lines (33%)
- **Scripts**: 5 files (1,206 lines)
- **Redundant scripts**: ~440 lines (36%)
- **Documentation**: 11 files (~4,000 lines)
- **External tools**: 1 repository (large, mostly unused)

### Refactored (Minimal)

- **Python modules**: 5 files (745 + 219 = 964 lines) ↓33%
- **Scripts**: 3 files (764 lines) ↓37%
- **Documentation**: 5 files (~2,000 lines) ↓50%
- **External tools**: Reference only (not included)

**Total reduction**: ~40% smaller, same functionality

---

## 🎯 Decision Matrix

| Component | Lines | Used? | Impact if Removed | Recommendation |
|-----------|-------|-------|-------------------|----------------|
| visualize_annotations/ | 745 | ✅ Yes | ❌ Critical | ✅ KEEP |
| data_loader.py | 219 | ✅ Yes | ❌ Critical | ✅ KEEP |
| streaming_loader.py | 257 | ❌ No | ✅ None | ❌ REMOVE |
| frame_processor.py | 211 | ❌ No | ✅ None | ❌ REMOVE |
| create_annotation_video.py | 181 | ✅ Yes | ❌ Critical | ✅ KEEP |
| visualize_annotations.py | 292 | ⚠️ Partial | ⚠️ Minor | ⚠️ OPTIONAL |
| export_yolo_annotations.py | 278 | ✅ Yes | ⚠️ Moderate | ✅ KEEP |
| diagnose_tdengine.py | 305 | ✅ Yes | ⚠️ Moderate | ✅ KEEP |
| visualize_raw_thermal.py | 150 | ❌ No | ✅ None | ❌ REMOVE |
| export_from_tdengine.sh | - | ✅ Yes | ⚠️ Moderate | ✅ KEEP |

---

## 🚀 Recommended Refactoring Plan

### Phase 1: Remove Unused Code

```bash
# Remove unused modules
rm src/thermal_data_processing/streaming_data_loader.py
rm src/thermal_data_processing/frame_processor.py
rm visualize_raw_thermal.py

# Update imports in __init__.py files
```

### Phase 2: Consolidate Documentation

```bash
# Keep essential docs
# Merge or remove historical/issue-specific docs
```

### Phase 3: Clean External Tools

```bash
# Keep tdengine export tool reference
# Don't commit the entire external repo (already in .gitignore)
```

### Phase 4: Simplify Scripts (Optional)

```bash
# Consider: Merge visualize_annotations.py features into create_annotation_video.py
# Add --interactive flag for matplotlib viewing if needed
```

---

## 📝 Next Steps for Refactoring

1. **Review this inventory** with your team
2. **Decide which features to keep** based on actual usage
3. **Create refactoring branch**: `git checkout -b refactor/cleanup`
4. **Remove unused code** systematically
5. **Update documentation** to reflect changes
6. **Test thoroughly** after each removal
7. **Merge when complete**: `git merge refactor/cleanup`

---

**Document Created**: November 6, 2025
**Purpose**: Refactoring reference
**Status**: Complete inventory for decision-making

---

See **FINAL_SUMMARY.md** for complete project overview.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 🆕 NEW: PyTorch DataLoader (Added)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Priority: HIGH - Deep Learning Training**

### src/data_pipeline/ (NEW MODULE)

**TDengineConnector Class:**
- `query_frame_by_timestamp(mac, timestamp_ms, tolerance_ms)` - Fetch single frame into memory
- `batch_query_frames(mac, timestamps_ms, tolerance_ms)` - Batch fetch for efficiency
- `_decompress_frame_data(encoded_data, width, height)` - Decompress in-memory

**ThermalAnnotationDataset Class (PyTorch Dataset):**
- `__init__(annotation_file, mac_address, ...)` - Initialize with JSON + MAC
- `__len__()` - Return number of samples (required by PyTorch)
- `__getitem__(idx)` - Fetch frame from TDengine (required by PyTorch)
- `prefetch_all_frames()` - Load all into memory cache
- `get_category_name(label_id)` - Get category from ID
- `get_statistics()` - Dataset statistics
- `_load_annotations()` - Parse JSON file
- `_build_category_mapping()` - Create label mapping
- `_process_annotation(annotation)` - Convert to tensor format

**Helper Functions:**
- `create_dataloader(...)` - Easy DataLoader creation with prefetch
- `collate_fn(batch)` - Custom batch collation

### example_training_pipeline.py (NEW SCRIPT)

**Functions:**
- `example_basic_usage()` - Basic Dataset usage
- `example_prefetch_all()` - Prefetching demonstration
- `example_with_dataloader()` - DataLoader iteration
- `example_training_loop()` - Training loop skeleton
- `example_custom_transforms()` - Custom transform example

**Purpose**: Complete examples for deep learning training pipeline

### Features

✅ **Read annotation JSON** - Parses data_time and MAC address
✅ **Fetch from TDengine** - Direct database queries
✅ **In-memory processing** - NO disk files required
✅ **PyTorch tensors** - Returns torch.Tensor ready for training
✅ **YOLO format** - Preserves bbox format [cx, cy, w, h]
✅ **Caching** - In-memory cache for performance
✅ **Prefetching** - Batch load all frames
✅ **Standard API** - Compatible with all PyTorch code

### Keep Decision

**Keep**: ✅ YES - Essential for deep learning training

**Priority**: ⭐⭐⭐ HIGH

**Reason**: 
- Main requirement for ML training pipeline
- No disk space needed
- Direct TDengine integration
- Standard PyTorch API
- Well-tested and documented

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Updated Feature Count:
- Python modules: 10 files (was 8)
- Core features: 5 modules (was 4)
- Training-ready: ✅ YES (new capability)

