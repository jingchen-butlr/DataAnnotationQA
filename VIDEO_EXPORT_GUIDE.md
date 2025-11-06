# Video Export Guide

## Overview

This guide explains how to create annotated videos from thermal data using the `src/visualize_annotations` module.

The module provides functionality to:
1. Load thermal image frames and annotations
2. Overlay bounding boxes and labels on each frame
3. Export a video showing all frames sequentially with annotations
4. Export individual annotated frames as images

## Module Structure

```
src/visualize_annotations/
├── __init__.py          # Package initialization
├── loader.py            # Data and annotation loading
├── visualizer.py        # Annotation rendering
└── video_exporter.py    # Video and image export
```

### Components

- **ThermalDataLoader**: Loads thermal data from text files
- **AnnotationLoader**: Loads and manages annotations from JSON
- **AnnotationVisualizer**: Draws bounding boxes and labels on frames
- **VideoExporter**: Exports videos or image sequences

## Quick Start

### Create Annotated Video

```bash
# Basic usage - creates video with default settings
uv run python create_annotation_video.py

# Create full video with all frames
uv run python create_annotation_video.py \
    --output output/videos/my_video.mp4 \
    --fps 10 \
    --create-summary
```

### Export as Image Sequence

```bash
# Export frames as individual images
uv run python create_annotation_video.py \
    --export-images \
    --output-dir output/frames \
    --num-frames 100
```

## Command-Line Options

### Basic Options

```
--data PATH              Path to thermal data file
                        (default: Data/Gen3_Annotated_Data_MVP/Raw/SL18_R1.txt)

--annotation PATH        Path to annotation file
                        (default: Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json)

--output PATH           Output video file path
                        (default: output/videos/annotated_thermal.mp4)
```

### Frame Selection

```
--start-frame N         Starting frame index (default: 0)

--num-frames N          Number of frames to process
                        (default: all frames)
```

### Video Settings

```
--fps N                 Frames per second for output video
                        (default: 10)

--scale N               Scale factor for upscaling frames
                        (default: 8, produces 480x320 output from 60x40 input)

--codec CODEC           Video codec: mp4v, avc1, XVID, MJPG
                        (default: mp4v)
```

### Image Export

```
--export-images         Export as individual images instead of video

--output-dir PATH       Output directory for image frames
                        (default: output/annotated_frames)

--image-format FORMAT   Image format: png or jpg
                        (default: png)
```

### Additional Options

```
--create-summary        Create a summary report of the dataset
```

## Examples

### Example 1: Quick Preview

Create a short video with the first 50 frames:

```bash
uv run python create_annotation_video.py \
    --num-frames 50 \
    --fps 15 \
    --output output/videos/preview.mp4
```

### Example 2: Full Quality Video

Create full video with all frames and higher frame rate:

```bash
uv run python create_annotation_video.py \
    --fps 15 \
    --scale 10 \
    --output output/videos/full_quality.mp4 \
    --create-summary
```

### Example 3: Process Specific Section

Process frames 100-200:

```bash
uv run python create_annotation_video.py \
    --start-frame 100 \
    --num-frames 100 \
    --output output/videos/section_100_200.mp4
```

### Example 4: Export as Images

Export annotated frames as PNG images:

```bash
uv run python create_annotation_video.py \
    --export-images \
    --output-dir output/annotated_frames \
    --image-format png
```

### Example 5: Process Different Dataset

Process a different thermal data file:

```bash
uv run python create_annotation_video.py \
    --data Data/Gen3_Annotated_Data_MVP/Raw/SL18_R2.txt \
    --annotation Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R2_annotation.json \
    --output output/videos/SL18_R2.mp4
```

## Output Files

### Video Output

```
output/videos/
├── annotated_thermal.mp4        # Main video file
└── dataset_summary.txt          # Summary report (if --create-summary used)
```

**Video specifications:**
- Resolution: 480x320 (with default scale=8 from 60x40 input)
- Format: MP4
- Codec: mp4v (configurable)
- Frame rate: 10 fps (configurable)

### Image Output

```
output/annotated_frames/
├── frame_0000.png
├── frame_0001.png
├── frame_0002.png
└── ...
```

**Image specifications:**
- Format: PNG or JPG
- Resolution: 480x320 (with default scale=8)
- Color: BGR format with annotations

## Visualization Features

### Bounding Boxes

Annotations are drawn with color-coded bounding boxes:

| Category | Color |
|----------|-------|
| Person | Red |
| Furniture | Blue |
| Object | Green |
| Building | Yellow |
| Environment | Cyan |
| Appliance | Magenta |

### Labels

Each bounding box includes:
- Category and subcategory (abbreviated for space)
- Object ID number
- Example: `per/standi #1` for "person/standing, ID 1"

### Frame Information

Each frame displays:
- Frame number
- Timestamp in seconds
- Temperature visualization (grayscale)

## Temperature Normalization

The module automatically:
1. Calculates global temperature range across all frames
2. Uses 1st and 99th percentiles to handle outliers
3. Adds 5% margin for better visualization
4. Applies consistent normalization across all frames

This ensures:
- Consistent brightness across the video
- Outliers don't dominate the color scale
- Temperature changes are visible

## Dataset Summary Report

When using `--create-summary`, a text report is generated:

```
============================================================
THERMAL DATA ANNOTATION SUMMARY
============================================================

Total Frames: 360
Annotated Frames: 54
Temperature Range: 4.9°C to 26.9°C
Duration: 59.5 seconds

Categories Found:
------------------------------------------------------------
  0: furniture/chair                          (54 instances)
  1: person/standing                          (2 instances)
  2: person/transition-lying with risk transition (1 instances)
  3: person/lying down-lying with risk        (50 instances)
  4: object/cellphone                         (11 instances)
  5: person/lower position-kneeling           (1 instances)

============================================================
```

## Using the Module Programmatically

### Python API

```python
from src.visualize_annotations import VideoExporter

# Create exporter
exporter = VideoExporter(fps=10, scale_factor=8)

# Load data
exporter.load_data(
    'Data/Gen3_Annotated_Data_MVP/Raw/SL18_R1.txt',
    'Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json'
)

# Export video
exporter.export_video(
    'output/videos/my_video.mp4',
    start_frame=0,
    num_frames=100
)

# Or export as images
exporter.export_frames_as_images(
    'output/frames',
    start_frame=0,
    num_frames=100,
    image_format='png'
)

# Create summary report
exporter.create_summary_report('output/summary.txt')
```

### Individual Components

```python
from src.visualize_annotations import (
    ThermalDataLoader, 
    AnnotationLoader,
    AnnotationVisualizer
)

# Load thermal data
thermal_loader = ThermalDataLoader()
frames, timestamps = thermal_loader.load('path/to/data.txt')

# Load annotations
ann_loader = AnnotationLoader()
annotations = ann_loader.load('path/to/annotations.json')

# Visualize a frame
visualizer = AnnotationVisualizer()
frame_idx = 0
annotation = ann_loader.match_frame_to_annotation(frame_idx, timestamps)
annotated_frame = visualizer.visualize_frame(
    frames[frame_idx],
    annotation,
    timestamps[frame_idx],
    frame_idx
)

# Save or display
import cv2
cv2.imwrite('frame.png', annotated_frame)
```

## Performance

- **Video creation**: ~2700 frames/second
- **Image export**: ~980 frames/second
- **Memory usage**: Loads all frames into memory (360 frames ≈ 2-3 MB)

For very large datasets, consider processing in chunks using `--start-frame` and `--num-frames`.

## Troubleshooting

### Video codec issues

If `mp4v` doesn't work, try different codecs:

```bash
# Try H.264 (may require additional codecs)
python create_annotation_video.py --codec avc1

# Try XVID
python create_annotation_video.py --codec XVID

# Try MJPEG (larger files but better compatibility)
python create_annotation_video.py --codec MJPG
```

### Video won't play

- Install VLC or another media player that supports more codecs
- Use `--codec MJPG` for maximum compatibility
- Export as images instead and create video with external tool

### Out of memory

For very large datasets:

```bash
# Process in chunks
python create_annotation_video.py --start-frame 0 --num-frames 100
python create_annotation_video.py --start-frame 100 --num-frames 100
# etc.
```

### Missing annotations

- Check that timestamps match between data and annotations
- Verify annotation file format
- Look for warnings in log output

## Technical Details

### Frame Processing Pipeline

1. Load thermal data (deciKelvin → Kelvin → Celsius)
2. Match frames to annotations by timestamp (±100ms tolerance)
3. Normalize temperature to 8-bit grayscale
4. Convert grayscale to BGR for color annotations
5. Draw bounding boxes and labels
6. Scale up frame by scale factor
7. Write to video or save as image

### Coordinate System

- Input annotations: Normalized coordinates [0, 1]
- Bounding box format: `[x, y, width, height]` (top-left corner)
- Output: Pixel coordinates scaled to output resolution

### Color Format

- Input frames: Grayscale (temperature data)
- Output frames: BGR (for OpenCV compatibility)
- Display: RGB (automatically converted by viewers)

## Integration with YOLO

The annotated videos can be used for:
1. Verifying YOLO training data quality
2. Visualizing model predictions
3. Creating demonstration videos
4. Quality assurance of annotations

See `YOLO_VISUALIZATION_GUIDE.md` for YOLO-specific features.

## Next Steps

- Create videos for all datasets
- Compare annotations across different sessions
- Use videos for quality assurance reviews
- Export frames for manual inspection
- Generate training videos for annotators

---

**Version**: 1.0.0  
**Last Updated**: November 2025  
**Module**: `src/visualize_annotations`

