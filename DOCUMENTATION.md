# Movebank Data Fetcher - Complete Documentation

## Table of Contents
- [About Movebank](#about-movebank)
- [Quick Start](#quick-start)
- [Setup Instructions](#setup-instructions)
- [Credentials Setup](#credentials-setup)
- [Usage Guide](#usage-guide)
- [Programmatic Usage](#programmatic-usage)
- [Sensor Reference](#sensor-reference)
- [Output Files](#output-files)
- [Troubleshooting](#troubleshooting)

---

## About Movebank

[Movebank](https://www.movebank.org/node/2) is a free, online database and research platform for animal tracking and other on-animal sensor data hosted by the Max Planck Institute for Animal Behavior. It helps animal tracking researchers manage, share, protect, analyze and archive their data.

See the [movebank-api.md](movebank-api.md) file for a complete description of the download interface to build calls to the Movebank database using HTTP/CSV or JSON/JavaScript requests. For working in R, check out the [move2 package](http://cran.r-project.org/web/packages/move2/index.html).

### Getting Started with Movebank
If you are not already familiar with Movebank, spend some time with the [Tracking Data Map](https://www.movebank.org/panel_embedded_movebank_webapp) to better understand how data are organized, viewed and accessed. If you want to compile existing studies for analysis, check out the [Collaborations using Movebank](https://www.movebank.org/node/30029) page for tips.

### Important Notes About Data
- Data in Movebank are stored in user-created studies and used during all stages of research
- Studies have varying levels of completeness (e.g., deployment periods and species names might or might not be defined)
- Animal and tag identifiers are unique within a study but not across studies
- The [Movebank Data Repository](https://www.movebank.org/node/15294) comprises a subset of curated, publicly archived studies
- Data access and use are subject to Movebank's [user agreement](https://www.movebank.org/cms/movebank-content/data-policy#user_agreement) and [general terms of use](https://www.movebank.org/cms/movebank-content/general-movebank-terms-of-use)

---

## Quick Start

### 1. One-Time Setup

```bash
# Install packages (if using pip)
pip install requests pandas

# OR create a new conda environment
conda create -n movebank_env python=3.11 -y
conda activate movebank_env
conda install -c conda-forge requests pandas -y
```

### 2. Set Credentials

**Method 1: Using config.py (Recommended - Easiest)**

Edit `config.py` and replace with your actual credentials:
```python
MOVEBANK_USERNAME = 'your_username'
MOVEBANK_PASSWORD = 'your_password'
```

**Method 2: Environment Variables (Each Session)**

PowerShell:
```powershell
$env:mbus='your_username'
$env:mbpw='your_password'
```

Command Prompt:
```cmd
set mbus=your_username
set mbpw=your_password
```

Linux/Mac:
```bash
export mbus=your_username
export mbpw=your_password
```

### 3. Common Commands

```bash
# See what sensors are available
python fetch_movebank_data.py --list-sensors

# Fetch all data from the entire study
python fetch_movebank_data.py

# Fetch only GPS data
python fetch_movebank_data.py --sensors gps

# Fetch GPS + Acceleration data
python fetch_movebank_data.py --sensors gps acceleration

# Fetch data from a specific time period
python fetch_movebank_data.py --start 2024-01-01 --end 2024-12-31

# Fetch GPS data from January 2024
python fetch_movebank_data.py --sensors gps --start 2024-01-01 --end 2024-01-31

# Fetch data to a custom folder
python fetch_movebank_data.py --output my_custom_folder
```

---

## Setup Instructions

### Setup Process

```bash
# Create new conda environment
conda create -n movebank_env python=3.11 -y

# Activate the environment
conda activate movebank_env

# Install required packages
conda install -c conda-forge requests pandas -y
```

### Verification

Test that everything is working:

```bash
# Activate environment (if using conda)
conda activate movebank_env

# Set credentials
$env:mbus='your_username'
$env:mbpw='your_password'

# List available sensors
python fetch_movebank_data.py --list-sensors
```

If this works, you're all set!

---

## Credentials Setup

### Method 1: Using config.py (EASIEST - Recommended)

1. Open the file `config.py` in a text editor (Notepad, VS Code, etc.)

2. Replace `'your_username'` and `'your_password'` with your actual Movebank credentials:

```python
# Before:
MOVEBANK_USERNAME = 'your_username'
MOVEBANK_PASSWORD = 'your_password'

# After (example):
MOVEBANK_USERNAME = 'john.doe@email.com'
MOVEBANK_PASSWORD = 'mySecurePassword123'
```

3. Save the file

4. Run the script - it will automatically use these credentials!

```bash
python fetch_movebank_data.py --list-sensors
```

**That's it!** No need to set environment variables every time.

### Method 2: Environment Variables (Each Session)

If you prefer not to save credentials in a file, you can set them each time:

**PowerShell:**
```powershell
$env:mbus='your_username'
$env:mbpw='your_password'
```

**Command Prompt:**
```cmd
set mbus=your_username
set mbpw=your_password
```

**Linux/Mac:**
```bash
export mbus=your_username
export mbpw=your_password
```

### Security Note

**Important:** If you use config.py:
- Don't share this file with others (it contains your password)
- Don't commit it to version control (Git)
- The file is for your local use only

If you're concerned about security, use Method 2 (environment variables) instead.

---

## Usage Guide

### Command Line Options

```bash
python fetch_movebank_data.py [OPTIONS]

Options:
  --study-id ID          Study ID (default: 3445611111)
  --sensors TYPE [TYPE]  Sensor types to fetch (names or IDs)
  --start DATE           Start date (YYYY-MM-DD or "YYYY-MM-DD HH:MM:SS")
  --end DATE             End date (YYYY-MM-DD or "YYYY-MM-DD HH:MM:SS")
  --output DIR           Output directory (default: movebank_data)
  --no-metadata          Skip fetching metadata
  --list-sensors         List available sensors and exit
  -h, --help             Show help message
```

### Basic Usage

**Fetch all data (default):**
```bash
python fetch_movebank_data.py
```

This will fetch all metadata and all sensor data from the entire study period.

### Specify Sensors

**Fetch only GPS data:**
```bash
python fetch_movebank_data.py --sensors gps
```

**Fetch GPS and acceleration data:**
```bash
python fetch_movebank_data.py --sensors gps acceleration
```

**Fetch using sensor IDs:**
```bash
python fetch_movebank_data.py --sensors 653 2365683
```

### Specify Time Range

**Fetch data from specific dates:**
```bash
python fetch_movebank_data.py --start 2024-01-01 --end 2024-12-31
```

**Fetch data with specific times:**
```bash
python fetch_movebank_data.py --start "2024-01-01 00:00:00" --end "2024-01-31 23:59:59"
```

**Fetch data from a start date to present:**
```bash
python fetch_movebank_data.py --start 2024-06-01
```

### Combined Options

**Fetch GPS data from January 2024:**
```bash
python fetch_movebank_data.py --sensors gps --start 2024-01-01 --end 2024-01-31
```

**Fetch multiple sensors from specific time period:**
```bash
python fetch_movebank_data.py --sensors gps acceleration barometer --start 2024-01-01 --end 2024-06-30
```

**Skip metadata and only fetch GPS events:**
```bash
python fetch_movebank_data.py --sensors gps --no-metadata
```

**Change output directory:**
```bash
python fetch_movebank_data.py --output my_data_folder
```

### List Available Sensors

**Check what sensors are in your study:**
```bash
python fetch_movebank_data.py --list-sensors
```

### Date Format Options

All of these work:
- `2024-01-01` (simple date)
- `2024-01-01 12:00:00` (date with time)
- `20240101000000000` (Movebank format)

---

## Programmatic Usage

You can also import and use the fetcher in your own Python scripts.

### Example 1: Fetch Specific Sensors and Time Range

```python
from fetch_movebank_data import MovebankDataFetcher

# Initialize
fetcher = MovebankDataFetcher()

# Fetch GPS data from January 2024
fetcher.fetch_all_study_data(
    study_id=3445611111,
    sensor_types=[653],  # GPS only
    timestamp_start='2024-01-01',
    timestamp_end='2024-01-31',
    output_dir='january_gps_data'
)
```

### Example 2: Fetch Multiple Sensors with Custom Time Range

```python
from fetch_movebank_data import MovebankDataFetcher

fetcher = MovebankDataFetcher()

# Fetch GPS and acceleration from June to December 2024
fetcher.fetch_all_study_data(
    study_id=3445611111,
    sensor_types=[653, 2365683],  # GPS and Acceleration
    timestamp_start='2024-06-01',
    timestamp_end='2024-12-31',
    output_dir='summer_fall_data',
    fetch_metadata=True
)
```

### Example 3: Fetch Individual Event Data

```python
from fetch_movebank_data import MovebankDataFetcher

fetcher = MovebankDataFetcher()

# Get list of individuals first
individuals = fetcher.get_individuals(3445611111)
print(individuals[['id', 'local_identifier']])

# Fetch GPS data for specific individual
individual_id = individuals['id'].iloc[0]
gps_data = fetcher.get_event_data(
    study_id=3445611111,
    sensor_type_id=653,
    individual_id=individual_id,
    timestamp_start='2024-01-01',
    timestamp_end='2024-12-31'
)

# Save to file
gps_data.to_csv('individual_gps_data.csv', index=False)
```

### Example 4: Check Available Sensors Before Fetching

```python
from fetch_movebank_data import MovebankDataFetcher

fetcher = MovebankDataFetcher()

# Check what sensors are available
sensors = fetcher.get_sensor_types(3445611111)
print("Available sensors:")
print(sensors[['sensor_type_id', 'tag_id']])

# Check what attributes are available for GPS data
gps_attributes = fetcher.get_study_attributes(3445611111, sensor_type_id=653)
print("\nAvailable GPS attributes:")
print(gps_attributes['short_name'].tolist())

# Fetch with specific attributes
gps_data = fetcher.get_event_data(
    study_id=3445611111,
    sensor_type_id=653,
    attributes='timestamp,location_lat,location_long,visible,ground_speed,heading'
)
```

### Customization

**Change Study ID:**

Edit the `STUDY_ID` in `fetch_movebank_data.py`:

```python
STUDY_ID = your_study_id  # Change this
```

**Change Output Directory:**

```python
fetcher.fetch_all_study_data(3445611111, output_dir='my_custom_folder')
```

**Select Specific Attributes:**

```python
# Instead of 'all', specify exactly which attributes you need
data = fetcher.get_event_data(
    study_id=3445611111,
    sensor_type_id=653,
    attributes='timestamp,location_long,location_lat,visible,individual_local_identifier'
)
```

---

## Sensor Reference

### Sensor Type IDs

| Sensor Type | ID | Friendly Names |
|------------|-----|----------------|
| GPS | 653 | gps |
| Acceleration | 2365683 | acceleration, acc |
| Bird Ring | 397 | bird_ring |
| Radio Transmitter | 673 | radio |
| Argos Doppler Shift | 82798 | argos |
| Natural Mark | 2365682 | natural_mark |
| Solar Geolocator | 3886361 | geolocator |
| Accessory Measurements | 7842954 | accessory |
| Barometer | 77740391 | barometer |
| Magnetometer | 77740402 | magnetometer |
| Orientation | 819073350 | orientation |
| Gyroscope | 1297673380 | gyroscope |
| Heart Rate | 2206221896 | heart_rate |

You can use friendly names or IDs:
- `gps` or `653`
- `acceleration` or `acc` or `2365683`
- `barometer` or `77740391`
- `magnetometer` or `77740402`
- `gyroscope` or `1297673380`
- `heart_rate` or `2206221896`

---

## Output Files

When you run the script, it creates a folder (default: `movebank_data/`) with the following CSV files:

### Metadata Files (if `--no-metadata` not used)
- **`study_info.csv`** - Study metadata
- **`individuals.csv`** - All animals in the study
- **`tags.csv`** - All tags in the study
- **`deployments.csv`** - All deployments (tag-animal associations)
- **`sensors.csv`** - Available sensor types

### Event Data Files
- **`events_gps.csv`** - GPS tracking data (if GPS data requested/available)
- **`events_acceleration.csv`** - Acceleration data (if acceleration data requested/available)
- **`events_[sensor_name].csv`** - Other sensor data

### Common Attributes in Event Data

#### GPS Data (`events_gps.csv`)
- `timestamp` - Date/time of the location fix
- `location_lat` - Latitude (WGS84)
- `location_long` - Longitude (WGS84)
- `individual_id` - Database ID of the animal
- `individual_local_identifier` - Animal ID defined by researcher
- `visible` - Boolean indicating if point is flagged as outlier
- `ground_speed` - Speed in m/s (if available)
- `heading` - Direction of movement in degrees (if available)
- `height_above_ellipsoid` - Altitude in meters (if available)

#### Acceleration Data
- `timestamp` - Start time of acceleration burst
- `eobs_accelerations_raw` - Raw tri-axial acceleration values
- `eobs_acceleration_sampling_frequency_per_axis` - Sampling rate
- `individual_id` - Animal ID
- `deployment_id` - Deployment ID

---

## Troubleshooting

### "Please set your Movebank credentials"
- If using config.py: Make sure you edited it correctly and saved the file
- If using environment variables: Run the credential setup commands again in your current terminal
- Environment variables must be set in the same terminal session where you run the script

### "Access Denied" Error
- Verify your Movebank credentials are correct
- Check that you have permission to access the study
- Make sure environment variables are set in the current session (if not using config.py)

### "License Terms" Message
- The script automatically accepts license terms
- If it fails, you may need to manually accept terms in Movebank first

### "No data found" / No Data Returned
- Verify the study ID is correct
- Check if the study has data for the sensor type you're requesting
- Confirm your account has download permissions for the study
- Try `--list-sensors` to see what's available
- Check your time range isn't too restrictive

### "conda: command not found"
- Make sure Anaconda or Miniconda is installed
- Make sure conda is in your PATH
- Try restarting your terminal

### "Environment not found"
- Manually create the environment as shown in the Setup Instructions section

### pandas/numpy import errors
- The new environment should fix this
- If issues persist, try: `conda install pandas numpy -c conda-forge --force-reinstall`
- Make sure you've activated the correct environment: `conda activate movebank_env`

### Important Notes for Each Session

1. You must activate the conda environment each time you open a new terminal (if using conda):
   ```bash
   conda activate movebank_env
   ```

2. You must set credentials each time you open a new terminal (if using environment variables method)

3. All setup steps must be done in the same terminal session

---

## Next Steps

After fetching the data, you can:
1. Load CSV files into pandas for analysis
2. Visualize tracks using matplotlib, plotly, or folium
3. Perform movement ecology analysis
4. Export to other formats (GeoJSON, shapefile, etc.)

---

## Support and Resources

- [Movebank API Documentation](https://github.com/movebank/movebank-api-doc/blob/master/movebank-api.md)
- Contact: support@movebank.org
- [Tracking Data Map](https://www.movebank.org/panel_embedded_movebank_webapp)
- [Collaborations using Movebank](https://www.movebank.org/node/30029)

---

## Acknowledgements

[Schäuffelhut Berger Software Engineering](https://www.schaeuffelhut-berger.de)

Thank you to [Xianghui Dong](https://github.com/xhdong-umd) for converting the API documentation to markdown!
