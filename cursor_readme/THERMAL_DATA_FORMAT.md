# Thermal Data Format Documentation

Comprehensive documentation for thermal sensor data formats used in the Butlr thermal imaging system.

## 📊 Overview

This document describes the thermal data formats from **60×40 thermal sensors** with **L1.4 lens**, including:
- Single file TXT format (deciKelvin)
- Streaming data format (SQS)
- Calibration data format (Excel)
- Processed data formats (NumPy, video)

## 🌡️ Temperature Units

### DeciKelvin (Primary Storage Format)
- **Format**: 5-digit integer (e.g., `03155`)
- **Conversion**: DeciKelvin / 10 = Kelvin
- **Example**: `03155` → 315.5 K → 42.35°C
- **Range**: Typically `02800` to `03500` (7°C to 77°C)
- **Why**: Compact storage, integer precision

### Kelvin (Intermediate Format)
- **Conversion**: DeciKelvin / 10
- **Usage**: Internal processing
- **Range**: 280 K to 350 K typical

### Celsius (Display Format)
- **Conversion**: Kelvin - 273.15
- **Usage**: Visualization and analysis
- **Range**: 7°C to 77°C typical

## 📄 Single File TXT Format

### File Structure

```
ARRAYTYPE=14MBIT=12REFCAL=3T=YProtocolType=0(deciK)
03155 03145 03116 ... [2400 values] ... t: 17585.062
03184 03172 03137 ... [2400 values] ... t: 17585.187
...
```

### Header Line
```
ARRAYTYPE=14MBIT=12REFCAL=3T=YProtocolType=0(deciK)
```
- **ARRAYTYPE**: 14 (array type identifier)
- **MBIT**: 12 (data resolution)
- **REFCAL**: 3 (reference calibration)
- **T**: Y (temperature data)
- **ProtocolType**: 0
- **(deciK)**: Data in deciKelvin units

### Data Lines

**Format**: `[2400 space-separated deciKelvin values] t: [timestamp]`

**Frame Data**:
- **Values per frame**: 2400 (60 × 40 pixels)
- **Format**: 5-digit deciKelvin integers
- **Separator**: Single space
- **Layout**: Row-major order (left-to-right, top-to-bottom)

**Timestamp**:
- **Marker**: ` t: `
- **Format**: Decimal seconds (Unix timestamp or relative time)
- **Example**: `t: 17585.062`
- **Precision**: Milliseconds

### Example Files
- `250922_distort_001.txt` (441 frames)
- `test_export_010_2025-09-24_122007-122219_RyanDemo.txt` (818 frames)
- `250930_distort_straight_wire.TXT` (1385 frames)

### Reading in Python
```python
from src.data_processing.data_loader import ThermalDataLoader

loader = ThermalDataLoader(target_shape=(40, 60))
frames, timestamps = loader.load_from_text_file("data.txt")

# frames shape: (N, 40, 60) in Kelvin
# timestamps: list of float timestamps
# frames automatically have fliplr applied for correct orientation
```

## 📁 SQS Streaming Data Format

### Directory Structure
```
sqs_data/
├── udpc_02_00_71_62_50_67_packet_0_20250926_005735_181.txt
├── udpc_02_00_71_62_50_67_packet_0_20250926_005735_354.txt
├── udpc_02_00_71_62_50_67_packet_0_20250926_005735_511.txt
└── ... (179,171 files)
```

### Filename Format
```
udpc_[MAC_ADDRESS]_packet_0_[YYYYMMDD]_[HHMMSS]_[mmm].txt
```

**Components**:
- **udpc**: Protocol identifier
- **MAC_ADDRESS**: Sensor MAC address (e.g., `02_00_71_62_50_67`)
- **packet_0**: Packet number (usually 0)
- **YYYYMMDD**: Date (e.g., `20250926` = September 26, 2025)
- **HHMMSS**: Time (e.g., `005735` = 00:57:35)
- **mmm**: Milliseconds (e.g., `181`)

**Example**: `udpc_02_00_71_62_50_67_packet_0_20250926_005735_181.txt`
- MAC: 02:00:71:62:50:67
- Timestamp: 2025-09-26 00:57:35.181

### File Content

**One thermal frame per file** (not multiple frames):
```
16.5
16.9
17.3
...
[2400 lines total, one temperature value per line in Celsius]
```

**Format**:
- **Values**: 2400 temperature values (one per line)
- **Unit**: Celsius (directly, not deciKelvin)
- **Precision**: Decimal (e.g., `16.5`, `17.3`)
- **Layout**: Same row-major order as TXT format

### Data Quality Issues

**Common Errors** (~10% of files):
- **Incomplete frames**: 1824, 1248, 672, or 96 values instead of 2400
- **Corrupted data**: Parse errors or invalid values
- **Handling**: Automatically skipped by StreamingDataLoader

### Reading in Python
```python
from src.data_processing.streaming_data_loader import StreamingDataLoader

loader = StreamingDataLoader(target_shape=(40, 60))

# Load all data from directory
frames, timestamps, metadata = loader.load_streaming_data("sqs_data/")

# Load specific time range (10 minutes)
frames, timestamps, metadata = loader.load_streaming_data(
    "sqs_data/", 
    duration_minutes=10
)

# frames shape: (N, 40, 60) in Celsius
# timestamps: list of datetime objects
# frames automatically have fliplr applied for correct orientation
```

### Converting to Single TXT
```bash
# Convert entire SQS directory to single TXT file
python convert_sqs_to_txt.py -i ../../Data/sqs_data_fall -o output/converted.txt

# Convert specific duration
python convert_sqs_to_txt.py -i ../../Data/sqs_data_fall -o output/60min.txt --duration 60
```


## 🔧 Processing Tools

### Load Single File
```bash
python run_inference.py -i ../../Data/file.TXT -f mean_png
```

### Convert SQS to TXT
```bash
python convert_sqs_to_txt.py -i ../../Data/sqs_data/ -o output/converted.txt
```

### Process Mean Frame
```python
from src.data_processing.frame_processor import ThermalFrameDataProcessor

processor = ThermalFrameDataProcessor(temperature_unit='decikelvin')
frames_celsius = processor.process_batch(frames_kelvin, convert_to='celsius')
mean_frame = processor.calculate_mean_frame(frames_celsius)

### Valid Data
- **Complete frames**: Exactly 2400 values
- **Temperature range**: Realistic values (0-80°C)
- **Sequential**: Properly ordered values

### Common Issues

**Incomplete Frames** (~10% in SQS data):
- **1824 values**: Missing 576 values (24%)
- **1248 values**: Missing 1152 values (48%)
- **672 values**: Missing 1728 values (72%)
- **96 values**: Missing 2304 values (96%)

**Handling**: Automatically detected and skipped by loaders

**Timestamp Issues**:
- **Missing timestamps**: Optional in single TXT files
- **Parse errors**: Invalid filename formats
- **Time gaps**: Non-continuous data collection

## 💾 Processed Data Formats

### NumPy Arrays (.npy, .npz)

**Structure**:
```python
# Shape: (frames, height, width)
frames_array.shape  # (N, 40, 60)

# NPZ with metadata
np.savez_compressed('output.npz',
    frames=frames_array,
    timestamps=timestamps_array,
    metadata=metadata_dict
)
```

**Units**: Typically Celsius for analysis


**Specifications**:
- **Resolution**: 984×368 pixels (scaled up from 40×60)
- **Background**: Black
- **Layout**: Side-by-side (Raw | Undistorted)
- **Labels**: "Raw Frame" and "Undistorted Frame"
- **Colormap**: Grayscale
- **Frame rate**: 5-10 FPS typical

### Corrected TXT Files

**Format**: Same as input TXT format
```
ARRAYTYPE=14MBIT=12REFCAL=3T=YProtocolType=0(deciK)
[2400 undistorted deciKelvin values] t: [timestamp]
...
```

**Usage**: Can be processed by same tools as original data

## 🎨 Visualization Standards

### Colormap
- **Primary**: Grayscale (`cmap='gray'`)
- **White**: Hot (higher temperature)
- **Black**: Cold (lower temperature)
- **Difference maps**: RdBu_r (red-blue diverging)

### Temperature Scaling

**Adaptive Range** (recommended):
- Calculate per-frame or per-dataset
- Remove top/bottom 3 extreme pixels
- Add 5% margin
- Optimal contrast for each scene

**Fixed Range** (for consistency):
- 0°C to 50°C typical
- 20°C to 40°C for indoor scenes

### Resolution
- **PNG outputs**: 150 DPI (high quality)
- **Videos**: 8× scaling from 40×60 to 320×480 per frame


