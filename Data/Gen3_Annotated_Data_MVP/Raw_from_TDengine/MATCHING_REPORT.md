# TDengine Data Matching Report

## ✅ Perfect Match Achieved

Successfully exported thermal data from TDengine that matches the existing SL18_R1 annotations.

### Source Files

**Annotation File:**
- Path: `Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json`
- Annotations: 54
- Objects tracked: 6 categories (person, furniture, object)

**Original Sample Data:**
- Path: `Data/Gen3_Annotated_Data_MVP/Raw/SL18_R1.txt`
- Frames: 360

**TDengine Export (Matching):**
- Path: `Data/Gen3_Annotated_Data_MVP/Raw_from_TDengine/SL18_R1_from_tdengine.txt`
- Frames: 420 (with 5-second buffer on each side)
- MAC: 02:00:1a:62:51:67

### Time Range

**Annotation Timestamps:**
- First: 1760639220.331 (2025-10-16 11:27:00.331 LA)
- Last: 1760639279.207 (2025-10-16 11:27:59.207 LA)
- Duration: ~59 seconds

**TDengine Export:**
- Start: 2025-10-16 18:26:55 UTC (11:26:55 LA)
- End: 2025-10-16 18:28:05 UTC (11:28:05 LA)
- Duration: ~70 seconds (includes 5-sec buffer on each side)

### Matching Results

✅ **100% Match Rate**
- Total annotations: 54
- Matched annotations: 54
- Match tolerance: ±100ms
- All frames with annotations found in TDengine data

### Frame Index Mapping

First 10 annotated frames in TDengine export:

| Frame Index | Timestamp (epoch) | LA Time | Annotation |
|-------------|-------------------|---------|------------|
| 30 | 1760639220.331 | 11:27:00.331 | ✅ Yes |
| 39 | 1760639221.458 | 11:27:01.458 | ✅ Yes |
| 45 | 1760639222.460 | 11:27:02.460 | ✅ Yes |
| 50 | 1760639223.610 | 11:27:03.610 | ✅ Yes |
| 58 | 1760639224.615 | 11:27:04.615 | ✅ Yes |
| 64 | 1760639225.619 | 11:27:05.619 | ✅ Yes |
| 70 | 1760639226.962 | 11:27:06.962 | ✅ Yes |
| 79 | 1760639228.137 | 11:27:08.137 | ✅ Yes |
| 86 | 1760639229.297 | 11:27:09.297 | ✅ Yes |
| 90 | 1760639230.308 | 11:27:10.308 | ✅ Yes |

### Verification

**Video Created:**
- Path: `output/videos/SL18_R1_from_tdengine.mp4`
- Duration: 42 seconds (420 frames @ 10 fps)
- Resolution: 480x320
- Annotations displayed: 54 frames

**Test Images:**
- Path: `output/test_annotated_tdengine/frame_*.png`
- Sample verified: Frame 30 shows annotations correctly
  - Red box: person/standing
  - Blue box: furniture/chair
  - Timestamp: 1760639220.331s (matches annotation)

### Data Quality

- ✅ Epoch timestamps preserved
- ✅ Temperature data in deciKelvin format
- ✅ 2400 values per frame (60x40 pixels)
- ✅ Compatible with visualization tools
- ✅ Ready for quality assurance review

### Usage

Visualize this data with existing annotations:

```bash
# Create video
uv run python create_annotation_video.py \
    --data Data/Gen3_Annotated_Data_MVP/Raw_from_TDengine/SL18_R1_from_tdengine.txt \
    --annotation Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json \
    --output output/videos/SL18_R1_tdengine_annotated.mp4

# Export YOLO format
uv run python export_yolo_annotations.py \
    --data Data/Gen3_Annotated_Data_MVP/Raw_from_TDengine/SL18_R1_from_tdengine.txt \
    --annotation Data/Gen3_Annotated_Data_MVP/Annotations/SL18_R1_annotation.json \
    --output-dir output/yolo_format_tdengine \
    --export-images
```

### Comparison with Original Sample

Both files can now be used with the same annotation file:

| File | Source | Frames | Annotated | Match |
|------|--------|--------|-----------|-------|
| SL18_R1.txt | Original sample | 360 | 54 | ✅ 100% |
| SL18_R1_from_tdengine.txt | TDengine | 420 | 54 | ✅ 100% |

---

**Export Date**: November 6, 2025
**MAC Address**: 02:00:1a:62:51:67
**Status**: ✅ Perfect Match - Ready for QA
