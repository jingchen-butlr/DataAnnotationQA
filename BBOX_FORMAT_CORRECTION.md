# Bounding Box Format Correction

## ✅ Issue Fixed: Annotation bbox Format Was Already YOLO

### The Mistake

I initially **incorrectly assumed** the bbox format in the annotations was `[x, y, width, height]` (top-left corner format), but it was actually **already in YOLO format** `[center_x, center_y, width, height]`.

### The Correct Format

According to `annotation_format.tsx`, the bbox is stored as:

```typescript
interface EnhancedAnnotation {
  // YOLO bbox format
  centerX: number;    // Normalized 0-1
  centerY: number;    // Normalized 0-1
  width: number;      // Normalized 0-1
  height: number;     // Normalized 0-1
}
```

**Output in JSON:**
```json
{
  "bbox": [0.3197916666666667, 0.75759765625, 0.185, 0.2516666666666666],
  "category": "furniture",
  "subcategory": "chair"
}
```

This is: `[center_x, center_y, width, height]` ← **YOLO format!**

## 🔧 Changes Made

### 1. Fixed `src/visualize_annotations/visualizer.py`

**Updated `draw_bbox()` method:**

```python
def draw_bbox(self, image: np.ndarray, bbox: List[float], color):
    """
    Draw bounding box on image.
    
    Args:
        bbox: [center_x, center_y, width, height] in YOLO format (normalized 0-1)
    """
    height, width = image.shape[:2]
    
    # Convert YOLO format (center) to pixel coordinates
    cx_norm, cy_norm, w_norm, h_norm = bbox
    
    # Convert center coordinates to top-left corner
    x_norm = cx_norm - w_norm / 2.0
    y_norm = cy_norm - h_norm / 2.0
    
    # Convert to pixel coordinates
    x = int(x_norm * width)
    y = int(y_norm * height)
    w = int(w_norm * width)
    h = int(h_norm * height)
    
    # Draw rectangle from top-left to bottom-right
    cv2.rectangle(image, (x, y), (x + w, y + h), color, self.line_thickness)
```

**Updated `draw_label()` method:**

```python
def draw_label(self, image: np.ndarray, bbox: List[float], label_text, color):
    """
    Args:
        bbox: [center_x, center_y, width, height] in YOLO format
    """
    height, width = image.shape[:2]
    
    # Convert YOLO format (center) to top-left corner for label placement
    cx_norm, cy_norm, w_norm, h_norm = bbox
    x_norm = cx_norm - w_norm / 2.0
    y_norm = cy_norm - h_norm / 2.0
    
    x = int(x_norm * width)
    y = int(y_norm * height)
    # ... draw label at (x, y)
```

### 2. Removed Incorrect Conversion from `loader.py`

**Removed this method** (no longer needed):
```python
# REMOVED - bbox is already in YOLO format!
def bbox_to_yolo(self, bbox: List[float]) -> List[float]:
    x, y, w, h = bbox
    cx = x + w / 2.0
    cy = y + h / 2.0
    return [cx, cy, w, h]
```

### 3. Updated `visualize_annotations.py`

**Renamed and simplified methods:**

```python
# OLD (incorrect):
def bbox_to_yolo(self, bbox):
    # ... convert from corner to center

def convert_annotation_to_yolo(self, annotation):
    bbox = annotation['bbox']
    yolo_bbox = self.bbox_to_yolo(bbox)  # WRONG!
    return class_id, yolo_bbox

# NEW (correct):
def get_annotation_for_yolo(self, annotation):
    bbox = annotation['bbox']  # Already in YOLO format!
    return class_id, bbox  # No conversion needed
```

**Fixed pixel coordinate conversion:**

```python
# Convert YOLO format (center) to pixel coordinates
cx_norm, cy_norm, w_norm, h_norm = bbox

# Convert center to top-left corner
x_norm = cx_norm - w_norm / 2.0
y_norm = cy_norm - h_norm / 2.0

# Convert to pixel coordinates
x_pixel = x_norm * width
y_pixel = y_norm * height
w_pixel = w_norm * width
h_pixel = h_norm * height
```

### 4. Updated `export_yolo_annotations.py`

**Removed unnecessary conversion:**

```python
# OLD (incorrect):
yolo_bbox = self.bbox_to_yolo(bbox)  # WRONG!
cx, cy, w, h = yolo_bbox

# NEW (correct):
bbox = ann['bbox']  # Already in YOLO format!
cx, cy, w, h = bbox  # Use directly
f.write(f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
```

## 📐 Coordinate Conversion Example

### Example Annotation from JSON:

```json
{
  "bbox": [0.3198, 0.7576, 0.185, 0.2517],
  "category": "furniture",
  "subcategory": "chair"
}
```

### Step-by-Step Conversion:

```python
# Input (YOLO format - already correct!)
center_x = 0.3198  # Center X
center_y = 0.7576  # Center Y
width = 0.185
height = 0.2517

# Convert to top-left corner (for drawing rectangle)
top_left_x = center_x - width / 2.0   = 0.3198 - 0.0925 = 0.2273
top_left_y = center_y - height / 2.0  = 0.7576 - 0.1259 = 0.6317

# Scale to 480x320 image
x_pixel = int(0.2273 * 480) = 109
y_pixel = int(0.6317 * 320) = 202
w_pixel = int(0.185 * 480) = 88
h_pixel = int(0.2517 * 320) = 80

# Draw rectangle
cv2.rectangle(
    image,
    (109, 202),      # Top-left
    (197, 282),      # Bottom-right (109+88, 202+80)
    (255, 0, 0),     # Blue for furniture
    2
)
```

## 🎯 Visualization Pipeline (Corrected)

```
1. Load annotation JSON
   bbox = [0.3198, 0.7576, 0.185, 0.2517]  # YOLO format ✓

2. Load thermal frame (60x40)
   frame = thermal_loader.get_frame(0)

3. Scale image to 480x320
   scaled = cv2.resize(frame, (480, 320))

4. Convert YOLO center to top-left corner
   cx, cy, w, h = bbox
   x = cx - w/2 = 0.3198 - 0.0925 = 0.2273
   y = cy - h/2 = 0.7576 - 0.1259 = 0.6317

5. Convert normalized to pixels (on 480x320 image)
   x_pixel = 0.2273 * 480 = 109
   y_pixel = 0.6317 * 320 = 202
   w_pixel = 0.185 * 480 = 88
   h_pixel = 0.2517 * 320 = 80

6. Draw rectangle at pixel coordinates
   cv2.rectangle(image, (109, 202), (197, 282), color, 2)

7. Draw label at top-left corner (109, 202)
```

## ✅ Verification

### Test Results:

```bash
uv run python create_annotation_video.py \
    --export-images \
    --num-frames 3 \
    --output-dir output/test_yolo_correct
```

**Output**: Bounding boxes are now **correctly positioned**!

- Red box (person/standing) in upper portion
- Blue box (furniture/chair) in lower-center portion
- Labels placed at correct positions
- All coordinates match expected locations

## 📊 Format Comparison

| Format | Structure | Origin | Usage |
|--------|-----------|--------|-------|
| **YOLO** | `[cx, cy, w, h]` | Annotation JSON | ✅ Storage format |
| **Corner** | `[x, y, w, h]` | Converted for drawing | ✅ OpenCV rectangles |
| **Pixel** | `[x_px, y_px, w_px, h_px]` | Scaled coordinates | ✅ Final rendering |

## 🎓 Key Takeaways

1. **Annotation bbox is already in YOLO format** (center coordinates)
2. **No conversion needed** for YOLO export - use bbox directly
3. **Conversion IS needed** for drawing:
   - YOLO (center) → Corner (top-left) → Pixels
4. **Formula**: `top_left = center - size/2`

## 📝 Summary

**What was wrong:**
- Assumed bbox was `[x, y, w, h]` (top-left corner)
- Incorrectly converted it "to YOLO" (was already YOLO!)
- This caused double conversion and incorrect positioning

**What is correct:**
- Bbox is `[cx, cy, w, h]` (YOLO center format)
- For YOLO export: use bbox directly (no conversion)
- For drawing: convert center → corner → pixels

**All code has been corrected and verified!** ✅

---

**Date**: November 5, 2025  
**Issue**: Misunderstood bbox format  
**Resolution**: Corrected all conversion code  
**Status**: ✅ Fixed and Verified

