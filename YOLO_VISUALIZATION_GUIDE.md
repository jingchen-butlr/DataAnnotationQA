# YOLO Format Annotation Visualization Guide

This guide explains how to visualize thermal data annotations in YOLO format for the DataAnnotationQA project.

## Overview

The project now includes tools to:
1. Load thermal data and annotations
2. Convert annotations to YOLO format
3. Visualize annotated frames
4. Export annotations to standard YOLO format files

## YOLO Format

YOLO (You Only Look Once) uses a specific bounding box format:

```
<class_id> <center_x> <center_y> <width> <height>
```

All coordinates are normalized to [0, 1] range:
- `center_x`: Center X coordinate (0-1)
- `center_y`: Center Y coordinate (0-1)
- `width`: Box width (0-1)
- `height`: Box height (0-1)

### Conversion from Original Format

Original annotation format: `[x, y, width, height]` (top-left corner)
YOLO format: `[center_x, center_y, width, height]`

Conversion:
```python
center_x = x + width / 2.0
center_y = y + height / 2.0
```

## Installation

The Python environment is already set up using `uv`. All dependencies are installed:

```bash
uv sync
```

## Usage

### 1. Visualize Single Frame

Visualize a specific frame with YOLO format annotations:

```bash
uv run python visualize_annotations.py --frame 0
```

Output shows:
- Thermal image with bounding boxes
- YOLO format annotations in console
- Class ID to category mapping

Example output:
```
============================================================
YOLO Format Annotations:
============================================================
0 0.412292 0.883431 0.185000 0.251667
1 0.295625 0.110098 0.116667 0.106667
============================================================

Class ID Mapping:
  0: furniture/chair
  1: person/standing
============================================================
```

### 2. Visualize Multiple Frames

Visualize and save multiple frames:

```bash
uv run python visualize_annotations.py --frame 0 --num-frames 5 --output-dir output/visualizations
```

This will:
- Visualize 5 frames starting from frame 0
- Save each visualization as PNG to `output/visualizations/`
- Display YOLO format for the first frame

### 3. Export to YOLO Format

Export all annotations to standard YOLO format:

```bash
uv run python export_yolo_annotations.py --export-images --image-format png
```

This creates:
```
output/yolo_format/
├── labels/                    # YOLO format annotation files
│   ├── SL18_R1_frame_0000.txt
│   ├── SL18_R1_frame_0009.txt
│   └── ...
├── images/                    # Thermal images
│   ├── frame_0000.png
│   ├── frame_0001.png
│   └── ...
├── classes.txt               # Class names (one per line)
└── dataset.yaml              # YOLO dataset configuration
```

### 4. Custom Data and Annotations

Use custom files:

```bash
uv run python visualize_annotations.py \
    --data Data/Gen3_Annotated_Data_MVP/Raw/SL18_R2.txt \
    --annotation Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R2_annotation.json \
    --frame 0
```

## YOLO Dataset Structure

The exported dataset follows standard YOLO format:

### classes.txt
```
furniture/chair
person/standing
person/transition-lying with risk transition
person/lying down-lying with risk
object/cellphone
person/lower position-kneeling
```

### Label File Format (labels/SL18_R1_frame_0000.txt)
```
0 0.412292 0.883431 0.185000 0.251667
1 0.295625 0.110098 0.116667 0.106667
```

### dataset.yaml
```yaml
# YOLO Dataset Configuration
path: /path/to/output/yolo_format
train: labels
val: labels

# Classes
nc: 6  # number of classes
names:
  0: furniture/chair
  1: person/standing
  2: person/transition-lying with risk transition
  3: person/lying down-lying with risk
  4: object/cellphone
  5: person/lower position-kneeling
```

## Category Mapping

The converter automatically creates class IDs for all category/subcategory combinations:

| Class ID | Category | Subcategory |
|----------|----------|-------------|
| 0 | furniture | chair |
| 1 | person | standing |
| 2 | person | transition-lying with risk transition |
| 3 | person | lying down-lying with risk |
| 4 | object | cellphone |
| 5 | person | lower position-kneeling |

Additional categories will be assigned IDs sequentially as they are encountered.

## Visualization Features

### Color Coding
- **Red**: Person annotations
- **Blue**: Furniture annotations
- **Green**: Object annotations
- **Yellow**: Building annotations
- **Cyan**: Environment annotations
- **Magenta**: Appliance annotations

### Information Displayed
- Bounding boxes with category-specific colors
- Category and subcategory labels
- Object ID numbers
- Temperature colormap in grayscale (white = hot, black = cold)
- Frame timestamp

## Command-Line Options

### visualize_annotations.py

```
--data PATH              Path to thermal data file (default: Data/Gen3_Annotated_Data_MVP/Raw/SL18_R1.txt)
--annotation PATH        Path to annotation file (default: Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json)
--frame N               Frame index to visualize (default: 0)
--num-frames N          Number of frames to visualize (default: 1)
--output-dir PATH       Output directory to save visualizations (optional)
```

### export_yolo_annotations.py

```
--data PATH              Path to thermal data file
--annotation PATH        Path to annotation file
--output-dir PATH        Output directory for YOLO format files (default: output/yolo_format)
--export-images          Export thermal frames as images
--image-format FORMAT    Format for exported images: 'npy' or 'png' (default: npy)
```

## Technical Details

### Timestamp Matching

Annotations and frames are matched by timestamp:
- Frame timestamps: Unix timestamp in seconds (float)
- Annotation timestamps: Unix timestamp in milliseconds (int)
- Matching tolerance: ±100ms

### Temperature Conversion

Thermal data is automatically converted:
1. Raw data: deciKelvin (5-digit integers like `02881`)
2. Loaded as: Kelvin (288.1 K)
3. Displayed as: Celsius (14.95°C)

### Frame Orientation

Frames are automatically flipped left-right (`np.fliplr()`) to correct the image orientation during loading.

## Examples

### Example 1: Quick visualization

```bash
uv run python visualize_annotations.py
```

Shows frame 0 with YOLO annotations in console.

### Example 2: Export complete dataset

```bash
uv run python export_yolo_annotations.py --export-images --image-format png
```

Creates a complete YOLO dataset ready for training.

### Example 3: Analyze specific frames

```bash
uv run python visualize_annotations.py --frame 10 --num-frames 10 --output-dir analysis
```

Saves frames 10-19 to `analysis/` directory.

## Output Files

Generated in `output/` directory:

```
output/
├── yolo_format/              # YOLO dataset export
│   ├── labels/              # Annotation files
│   ├── images/              # Thermal images
│   ├── classes.txt          # Class mapping
│   └── dataset.yaml         # Dataset config
└── visualizations/           # Visualization images
    ├── frame_0000.png
    ├── frame_0001.png
    └── ...
```

## Notes

- Only annotated frames will have corresponding label files
- Frames without annotations will still be exported as images
- All coordinates are normalized to [0, 1] range
- Class IDs are assigned in the order categories are encountered
- The dataset.yaml follows YOLOv5/YOLOv8 format standards

## Troubleshooting

### No matching frame found

If you see "No matching frame found for annotation", check:
- Frame timestamps in thermal data file
- Annotation timestamps in JSON file
- Timestamp matching tolerance (currently 100ms)

### Missing dependencies

Run:
```bash
uv sync
```

### Wrong Python version

The project requires Python 3.11+. Check with:
```bash
python --version
```

## References

- [YOLO Format Documentation](https://docs.ultralytics.com/datasets/detect/)
- [Thermal Data Format](THERMAL_DATA_FORMAT.md)
- [Annotation Format](annotation_format.tsx)

