# Quick Start Guide

## Setup (One Time)

```bash
# Install dependencies
uv sync
```

## Visualize Annotations

### View a single frame
```bash
uv run python visualize_annotations.py --frame 0
```

### View multiple frames
```bash
uv run python visualize_annotations.py --frame 0 --num-frames 5
```

### Save visualizations
```bash
uv run python visualize_annotations.py --frame 0 --num-frames 5 --output-dir output/viz
```

## Export YOLO Dataset

### Basic export
```bash
uv run python export_yolo_annotations.py
```

### Export with images (PNG)
```bash
uv run python export_yolo_annotations.py --export-images --image-format png
```

### Export with images (NumPy)
```bash
uv run python export_yolo_annotations.py --export-images --image-format npy
```

## YOLO Format Example

Each line in a label file contains:
```
<class_id> <center_x> <center_y> <width> <height>
```

Example (`SL18_R1_frame_0000.txt`):
```
0 0.412292 0.883431 0.185000 0.251667
1 0.295625 0.110098 0.116667 0.106667
```

## Class Mapping

See `output/yolo_format/classes.txt`:
```
0: furniture/chair
1: person/standing
2: person/transition-lying with risk transition
3: person/lying down-lying with risk
4: object/cellphone
5: person/lower position-kneeling
```

## Output Structure

```
output/
├── yolo_format/
│   ├── labels/          # YOLO annotation files
│   ├── images/          # Thermal images
│   ├── classes.txt      # Class names
│   └── dataset.yaml     # YOLO config
└── visualizations/      # Visualization images
```

## Common Tasks

### Check annotation for specific frame
```bash
cat output/yolo_format/labels/SL18_R1_frame_0000.txt
```

### View class mapping
```bash
cat output/yolo_format/classes.txt
```

### Count annotations
```bash
ls output/yolo_format/labels/ | wc -l
```

### View dataset config
```bash
cat output/yolo_format/dataset.yaml
```

## Tips

- All coordinates are normalized (0-1)
- Thermal images are 60x40 pixels (width x height)
- Temperature displayed in Celsius
- Bounding box colors: Red (person), Blue (furniture), Green (object)

For more details, see:
- `YOLO_VISUALIZATION_GUIDE.md` - Complete documentation
- `SUMMARY.md` - Project summary
- `README.md` - Project overview

