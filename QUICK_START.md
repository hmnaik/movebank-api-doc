# GPS Viewer - Quick Start Guide

## Step 1: Install Dependencies

### Option A: Automatic Setup (Recommended for Windows)
```bash
setup_gps_viewer.bat
```

### Option B: Manual Installation
```bash
pip install -r requirements_gps_viewer.txt
```

### Option C: Individual Packages
```bash
pip install pandas numpy matplotlib folium
pip install earthengine-api  # Optional, for Google Earth Engine
```

## Step 2: Test Installation
```bash
python test_gps_viewer.py
```

This will verify all dependencies and check for data files.

## Step 3: Fetch GPS Data (if not already done)
```bash
python fetch_movebank_data.py --sensors gps
```

## Step 4: Run the GPS Viewer
```bash
python gps_viewer.py
```

## Quick Usage

1. **Select Animal** from dropdown
2. **Adjust date range** (optional)
3. **Choose base map** (OpenStreetMap, Satellite, Terrain)
4. **Enable visualization options**:
   - ✓ Show Track Line
   - ✓ Show Point Markers
   - ☐ Show Heat Map (optional)
5. **Click "Generate Map"**
6. Map opens automatically in your browser!

## Common Issues

### "GPS data file not found"
→ Run: `python fetch_movebank_data.py --sensors gps`

### "Module not found"
→ Run: `pip install -r requirements_gps_viewer.txt`

### Google Earth Engine not working
→ It's optional! Use "Satellite (Esri)" instead
→ Or authenticate: `earthengine authenticate`

## Files Created

- [gps_viewer.py](gps_viewer.py) - Main application
- [test_gps_viewer.py](test_gps_viewer.py) - Dependency checker
- [setup_gps_viewer.bat](setup_gps_viewer.bat) - Windows setup script
- [requirements_gps_viewer.txt](requirements_gps_viewer.txt) - Python packages
- [GPS_VIEWER_README.md](GPS_VIEWER_README.md) - Full documentation

## Screenshots of Features

### Main Interface
- Left Panel: Controls (animal selection, dates, map options)
- Center Panel: Map preview info
- Right Panel: Movement timeline graphs
- Bottom: Statistics panel

### Interactive Map (Browser)
- Blue line: GPS track
- Red dots: Individual GPS points (clickable)
- Green marker: Start point
- Red marker: End point
- Zoom, pan, click for details

## Example Session

```bash
# 1. Setup (first time only)
setup_gps_viewer.bat

# 2. Fetch data for specific date range
python fetch_movebank_data.py --sensors gps --start 2024-12-01 --end 2024-12-10

# 3. Launch viewer
python gps_viewer.py

# 4. In the GUI:
#    - Select animal: "24AA03_2A1P"
#    - Base map: "Satellite (Esri)"
#    - Check: Show Track Line, Show Point Markers
#    - Click: "Generate Map"
#    - View in browser!
```

## Tips

💡 **Performance**: For large datasets, the app automatically samples points to keep maps responsive

💡 **Multiple Views**: Generate different maps by changing filters and opening each in a new browser tab

💡 **Sharing**: Save the HTML map from your browser to share visualizations

💡 **Satellite Imagery**:
- "Satellite (Esri)" works immediately, no setup needed
- "Satellite (GEE)" provides recent imagery but requires Google Earth Engine authentication

## Need Help?

See [GPS_VIEWER_README.md](GPS_VIEWER_README.md) for detailed documentation.

For Movebank data fetching, see [fetch_movebank_data.py](fetch_movebank_data.py).
