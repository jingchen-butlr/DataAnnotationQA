# TDengine Data Export Guide

## Overview

This project includes integration with TDengine database to export thermal sensor raw data. The TDengine export tool is located at `dependent_tools/tdengine_export/`.

## Quick Start

### 1. Install Dependencies

Using uv (recommended):
```bash
uv pip install -r dependent_tools/tdengine_export/tools/export_tool/requirements.txt
```

Or navigate to the tool directory:
```bash
cd dependent_tools/tdengine_export/tools/export_tool
uv pip install -r requirements.txt
```

### 2. Export Data Using Helper Script

The simplest way to export data is using the provided helper script:

```bash
./export_from_tdengine.sh <MAC> <START_TIME> <END_TIME> [TIMEZONE]
```

**Example (based on your requirements):**

```bash
./export_from_tdengine.sh 02:00:1a:62:51:67 '2025-10-13 00:35:00' '2025-10-13 01:20:00' LA
```

This will:
- Export data from MAC address `02:00:1a:62:51:67`
- Time range: October 13, 2025, 00:35 to 01:20 (LA timezone)
- Output format: multi-frame with epoch timestamps
- Save to: `Data/exported_from_tdengine/02_00_1a_62_51_67_2025-10-13_00-35-00_2025-10-13_01-20-00_multi-frame/`

### 3. List Available Sensors

```bash
./export_from_tdengine.sh list
```

### 4. Get Help

```bash
./export_from_tdengine.sh help
```

## Advanced Usage

### Direct Tool Usage

You can also use the export tool directly:

```bash
cd dependent_tools/tdengine_export/tools/export_tool

# Basic export (multi-frame with epoch timestamps)
./quick_export.sh 02:00:1a:62:51:67 "2025-10-13 00:35:00" "2025-10-13 01:20:00" LA

# Export both single-frame and multi-frame formats
./quick_export.sh 02:00:1a:62:51:67 "2025-10-13 00:35:00" "2025-10-13 01:20:00" LA both
```

### Batch Export Configuration

For exporting multiple sensors or time ranges, create a YAML config file:

```yaml
exports:
  - name: "sensor_51_morning"
    mac: "02:00:1a:62:51:67"
    timezone: "America/Los_Angeles"
    start: "2025-10-13 00:35:00"
    end: "2025-10-13 01:20:00"
    format: "multi_frame"
  
  - name: "sensor_51_afternoon"
    mac: "02:00:1a:62:51:67"
    timezone: "America/Los_Angeles"
    start: "2025-10-13 12:00:00"
    end: "2025-10-13 13:00:00"
    format: "multi_frame"
```

Then run:

```bash
cd dependent_tools/tdengine_export/tools/export_tool
python3 batch_export.py --config your_export_config.yaml
```

## Output Format

### Multi-Frame Format (Default)

The exported data will be in the same format as your existing thermal data:

```
ARRAYTYPE=14MBIT=12REFCAL=3T=YProtocolType=0(deciK)
02909 02923 02878 ... [2400 values] ... t: 1760639220.331
02963 02959 02920 ... [2400 values] ... t: 1760639220.404
...
```

**Key Points:**
- Header line with format specification
- Each line: 2400 space-separated deciKelvin values
- Epoch timestamp at end of each line: `t: 1760639220.331`
- Compatible with your existing `create_annotation_video.py` workflow

### Temperature Format

- **Storage**: deciKelvin (5-digit integers)
- **Conversion**: deciK = (temperature°C + 273.15) × 10
- **Example**: 21.2°C → (21.2 + 273.15) × 10 = 2943 deciK

## Timezone Handling

### Important Notes

⚠️ **TDengine stores data in UTC format**

The export tool automatically converts local time to UTC for querying. You only need to:
1. Specify the timezone (LA, NY, or UTC)
2. Input local time
3. Tool handles the conversion

### Timezone Options

| Code | Timezone | DST | Conversion |
|------|----------|-----|------------|
| `LA` | America/Los_Angeles | Auto (PST/PDT) | LA time → UTC |
| `NY` | America/New_York | Auto (EST/EDT) | NY time → UTC |
| `UTC` | UTC | No DST | No conversion |

### Example Conversion

```bash
# Input: LA time October 13, 2025 00:35:00
# October is in PDT (UTC-7)

# LA 00:35 + 7 hours = UTC 07:35
# TDengine query: WHERE ts >= '2025-10-13 07:35:00'
```

## Integration with Annotation Workflow

### 1. Export Raw Data from TDengine

```bash
./export_from_tdengine.sh 02:00:1a:62:51:67 '2025-10-13 00:35:00' '2025-10-13 01:20:00' LA
```

### 2. Locate Exported Data

Data will be in:
```
Data/exported_from_tdengine/02_00_1a_62_51_67_2025-10-13_00-35-00_2025-10-13_01-20-00_multi-frame/thermal_data.txt
```

### 3. Create Annotation File

Create an annotation JSON file matching your exported data timestamps.

### 4. Visualize with Annotations

```bash
uv run python create_annotation_video.py \
    --data Data/exported_from_tdengine/02_00_1a_62_51_67_2025-10-13_00-35-00_2025-10-13_01-20-00_multi-frame/thermal_data.txt \
    --annotation Data/annotations/your_annotation.json \
    --output output/videos/exported_data_annotated.mp4
```

## Directory Structure

```
DataAnnotationQA/
├── dependent_tools/
│   └── tdengine_export/          # TDengine export tool (cloned repo)
│       ├── tools/
│       │   └── export_tool/      # Main export utilities
│       │       ├── quick_export.sh
│       │       ├── batch_export.py
│       │       ├── export_thermal_data.py
│       │       └── requirements.txt
│       └── README.md
│
├── Data/
│   ├── Gen3_Annotated_Data_MVP/  # Sample annotated data
│   └── exported_from_tdengine/   # TDengine exports go here
│       └── [MAC]_[START]_[END]_multi-frame/
│           └── thermal_data.txt
│
├── export_from_tdengine.sh       # Helper script
└── TDENGINE_EXPORT_GUIDE.md      # This file
```

## Troubleshooting

### Issue: Connection Error

```
Error: Cannot connect to TDengine server
```

**Solutions:**
1. Check network connectivity to TDengine server
2. Verify server address and port in configuration
3. Check firewall settings

### Issue: No Data Found

```
Found 0 frames
No data found in the specified time range.
```

**Solutions:**
1. Verify MAC address is correct: `./export_from_tdengine.sh list`
2. Check time range - data may not exist for that period
3. Verify timezone conversion is correct
4. Try a different time range

### Issue: Permission Denied

```bash
chmod +x export_from_tdengine.sh
chmod +x dependent_tools/tdengine_export/tools/export_tool/quick_export.sh
```

### Issue: Missing Dependencies

```bash
cd dependent_tools/tdengine_export/tools/export_tool
uv pip install -r requirements.txt
```

## Data Quality

### Automatic Filtering

The export tool automatically filters out anomalous frames:
- Frames with NaN values
- Temperatures < -272°C (absolute zero)
- Temperatures < -50°C (unlikely in real scenarios)
- Frames with >50 anomalous pixels are skipped

### Export Statistics

After export, you'll see:
```
Exported 11836 frames to multi-frame txt file
Skipped 3457 frames with >50 anomalous pixels
```

This ensures high-quality data for annotation and analysis.

## Additional Resources

### Documentation

- **TDengine Export Tool README**: `dependent_tools/tdengine_export/tools/export_tool/README.md`
- **TDengine Project README**: `dependent_tools/tdengine_export/README.md`
- **Thermal Data Format**: `THERMAL_DATA_FORMAT.md`

### Related Guides

- **COMPLETE_GUIDE.md** - Comprehensive annotation visualization guide
- **VIDEO_EXPORT_GUIDE.md** - Video export documentation
- **YOLO_VISUALIZATION_GUIDE.md** - YOLO format guide

## Example: Complete Workflow

### Step 1: Export from TDengine

```bash
# Export sensor data
./export_from_tdengine.sh 02:00:1a:62:51:67 '2025-10-13 00:35:00' '2025-10-13 01:20:00' LA
```

### Step 2: Verify Exported Data

```bash
# Check the exported file
head -5 Data/exported_from_tdengine/02_00_1a_62_51_67_2025-10-13_00-35-00_2025-10-13_01-20-00_multi-frame/thermal_data.txt
```

### Step 3: Create Annotations

Create annotation JSON file with matching timestamps (in milliseconds).

### Step 4: Visualize

```bash
# Create video with annotations
uv run python create_annotation_video.py \
    --data Data/exported_from_tdengine/02_00_1a_62_51_67_*/thermal_data.txt \
    --annotation Data/annotations/sensor_51_annotations.json \
    --output output/videos/sensor_51_annotated.mp4 \
    --create-summary
```

### Step 5: Export YOLO Format (Optional)

```bash
# Export for YOLO training
uv run python export_yolo_annotations.py \
    --data Data/exported_from_tdengine/02_00_1a_62_51_67_*/thermal_data.txt \
    --annotation Data/annotations/sensor_51_annotations.json \
    --output-dir output/yolo_format_sensor_51 \
    --export-images
```

---

**Last Updated**: November 6, 2025  
**Version**: 1.0  
**Status**: ✅ Ready for Use

