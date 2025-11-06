This project is to do quality assurance of thermal data annotation.

## Data Format

The thermal data is txt file that saved video frames with epoch time stamp(e.g t: 1760639220.331). An example is Data/Gen3_Annotated_Data_MVP/Raw/SL18_R1.txt
thermal data format is THERMAL_DATA_FORMAT.md and data_loader codes are at src/thermal_data_processing

The annotation file is in json format. An example is Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json
The "data_time":1760639220331 is the epoch timestamp 
The annotation format is at annotation_format.tsx

## Setup

Install dependencies using uv:
```bash
uv sync
```

## Annotation Visualization

This project includes comprehensive tools to visualize and export thermal data annotations:

### 🎥 Video Export (NEW!)

Create annotated videos with bounding boxes overlaid on thermal frames:

```bash
# Create annotated video (all frames)
uv run python create_annotation_video.py

# Create video with specific frame range
uv run python create_annotation_video.py --num-frames 100 --fps 15

# Export as individual images
uv run python create_annotation_video.py --export-images
```

The `src/visualize_annotations/` module provides:
- Load thermal image frames and annotations
- Overlay bounding boxes and labels directly on frames
- Export videos showing all frames sequentially with annotations
- Export individual annotated frames as images

### 📊 YOLO Format Visualization

Tools to visualize and export annotations in YOLO format:

```bash
# Visualize a single frame
uv run python visualize_annotations.py --frame 0

# Export to YOLO format
uv run python export_yolo_annotations.py --export-images --image-format png
```

### 📚 Documentation

- **VIDEO_EXPORT_GUIDE.md** - Complete guide for video creation
- **YOLO_VISUALIZATION_GUIDE.md** - YOLO format documentation
- **QUICK_START.md** - Quick reference for common tasks
- **SUMMARY.md** - Project summary and statistics

### 📁 Output

- **output/videos/** - Annotated video files
- **output/annotated_frames/** - Individual annotated frame images
- **output/yolo_format/** - YOLO dataset with labels and images
- **output/visualizations/** - Matplotlib-based visualizations

### ✨ Features

- **Video Export**: Create MP4 videos with annotations overlaid
- **YOLO Format**: Convert annotations to YOLO format (center_x, center_y, width, height)
- **Color-coded Boxes**: Different colors for each category (person=red, furniture=blue, etc.)
- **Flexible Export**: Video or image sequence output
- **Summary Reports**: Automatic dataset statistics generation
- **Scalable**: Process specific frame ranges for large datasets


