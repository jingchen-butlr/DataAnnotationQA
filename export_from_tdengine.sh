#!/bin/bash
#
# TDengine Data Export Helper Script
# This script exports thermal sensor data from TDengine using the export tool
#

# Set colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
EXPORT_TOOL_DIR="dependent_tools/tdengine_export/tools/export_tool"
OUTPUT_BASE_DIR="Data/exported_from_tdengine"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_BASE_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     TDengine Thermal Data Export Helper               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if export tool exists
if [ ! -d "$EXPORT_TOOL_DIR" ]; then
    echo -e "${YELLOW}⚠️  Export tool not found at: $EXPORT_TOOL_DIR${NC}"
    echo -e "${YELLOW}Please ensure dependent_tools/tdengine_export repository is cloned.${NC}"
    exit 1
fi

# Function to show usage
show_usage() {
    echo "Usage: ./export_from_tdengine.sh <MAC> <START_TIME> <END_TIME> [TIMEZONE]"
    echo ""
    echo "Parameters:"
    echo "  MAC         - Sensor MAC address (format: 02:00:1a:62:51:67)"
    echo "  START_TIME  - Start time (format: 'YYYY-MM-DD HH:MM:SS')"
    echo "  END_TIME    - End time (format: 'YYYY-MM-DD HH:MM:SS')"
    echo "  TIMEZONE    - Optional timezone (UTC, LA, NY) - default: LA"
    echo ""
    echo "Examples:"
    echo "  # Export using LA timezone (default)"
    echo "  ./export_from_tdengine.sh 02:00:1a:62:51:67 '2025-10-13 00:35:00' '2025-10-13 01:20:00'"
    echo ""
    echo "  # Export using UTC timezone"
    echo "  ./export_from_tdengine.sh 02:00:1a:62:51:67 '2025-10-13 00:35:00' '2025-10-13 01:20:00' UTC"
    echo ""
    echo "Special commands:"
    echo "  ./export_from_tdengine.sh list   - List available sensors"
    echo "  ./export_from_tdengine.sh help   - Show detailed help"
}

# Check arguments
if [ "$1" == "help" ] || [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    show_usage
    echo ""
    echo -e "${GREEN}For detailed documentation, see:${NC}"
    echo "  - dependent_tools/tdengine_export/tools/export_tool/README.md"
    echo "  - dependent_tools/tdengine_export/README.md"
    exit 0
fi

if [ "$1" == "list" ]; then
    echo -e "${GREEN}Listing available sensors...${NC}"
    cd "$EXPORT_TOOL_DIR" && ./quick_export.sh list
    exit 0
fi

if [ $# -lt 3 ]; then
    echo -e "${YELLOW}Error: Missing required parameters${NC}"
    echo ""
    show_usage
    exit 1
fi

# Parse arguments
MAC=$1
START_TIME=$2
END_TIME=$3
TIMEZONE=${4:-LA}  # Default to LA timezone

# Convert MAC format for directory name
MAC_UNDERSCORE=$(echo "$MAC" | tr ':' '_')

# Create formatted directory name
START_FORMATTED=$(echo "$START_TIME" | tr ' ' '_' | tr ':' '-')
END_FORMATTED=$(echo "$END_TIME" | tr ' ' '_' | tr ':' '-')
OUTPUT_DIR="${OUTPUT_BASE_DIR}/${MAC_UNDERSCORE}_${START_FORMATTED}_${END_FORMATTED}_multi-frame"

echo -e "${GREEN}Export Parameters:${NC}"
echo "  MAC Address:  $MAC"
echo "  Start Time:   $START_TIME"
echo "  End Time:     $END_TIME"
echo "  Timezone:     $TIMEZONE"
echo "  Output Dir:   $OUTPUT_DIR"
echo ""

# Run the export tool
echo -e "${GREEN}Starting export...${NC}"
cd "$EXPORT_TOOL_DIR" || exit 1

# Run quick_export.sh with the parameters
# Format: multi-frame with epoch timestamps
./quick_export.sh "$MAC" "$START_TIME" "$END_TIME" "$TIMEZONE" multi

# Check if export was successful
if [ $# -eq 0 ]; then
    echo -e "${GREEN}✅ Export completed successfully!${NC}"
    echo ""
    echo "Output location:"
    echo "  $OUTPUT_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Check the exported data in the output directory"
    echo "  2. Use create_annotation_video.py to visualize with annotations"
else
    echo -e "${YELLOW}⚠️  Export may have encountered issues${NC}"
    exit 1
fi

