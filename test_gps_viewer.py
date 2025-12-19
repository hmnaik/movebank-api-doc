"""
Quick test script to verify GPS Viewer dependencies
"""

import sys

def test_imports():
    """Test if all required packages can be imported"""

    print("Testing GPS Viewer dependencies...\n")

    results = []

    # Test pandas
    try:
        import pandas as pd
        print(f"✓ pandas {pd.__version__}")
        results.append(True)
    except ImportError as e:
        print(f"✗ pandas - NOT INSTALLED")
        print(f"  Install with: pip install pandas")
        results.append(False)

    # Test numpy
    try:
        import numpy as np
        print(f"✓ numpy {np.__version__}")
        results.append(True)
    except ImportError:
        print(f"✗ numpy - NOT INSTALLED")
        print(f"  Install with: pip install numpy")
        results.append(False)

    # Test matplotlib
    try:
        import matplotlib
        print(f"✓ matplotlib {matplotlib.__version__}")
        results.append(True)
    except ImportError:
        print(f"✗ matplotlib - NOT INSTALLED")
        print(f"  Install with: pip install matplotlib")
        results.append(False)

    # Test tkinter (comes with Python)
    try:
        import tkinter
        print(f"✓ tkinter (built-in)")
        results.append(True)
    except ImportError:
        print(f"✗ tkinter - NOT AVAILABLE")
        print(f"  Usually included with Python. You may need to reinstall Python.")
        results.append(False)

    # Test folium
    try:
        import folium
        print(f"✓ folium {folium.__version__}")
        results.append(True)
    except ImportError:
        print(f"✗ folium - NOT INSTALLED")
        print(f"  Install with: pip install folium")
        results.append(False)

    # Test earthengine (optional)
    try:
        import ee
        print(f"✓ earthengine-api (optional) {ee.__version__}")
        try:
            ee.Initialize()
            print(f"  ✓ Google Earth Engine authenticated")
        except:
            print(f"  ! Not authenticated. Run: earthengine authenticate")
        results.append(True)
    except ImportError:
        print(f"○ earthengine-api - NOT INSTALLED (optional)")
        print(f"  Install with: pip install earthengine-api")
        print(f"  Note: This is optional. App will use other satellite imagery.")
        # Don't add to results since it's optional

    print("\n" + "="*50)

    if all(results):
        print("✓ All required dependencies are installed!")
        print("You can run: python gps_viewer.py")
        return True
    else:
        print("✗ Some dependencies are missing.")
        print("\nQuick fix - install all at once:")
        print("  pip install -r requirements_gps_viewer.txt")
        return False

def check_data_files():
    """Check if required data files exist"""
    from pathlib import Path

    print("\n" + "="*50)
    print("Checking data files...\n")

    data_dir = Path('movebank_data')

    if not data_dir.exists():
        print(f"✗ Data directory not found: {data_dir}")
        print(f"  Run: python fetch_movebank_data.py")
        return False

    gps_file = data_dir / 'events_gps.csv'
    if gps_file.exists():
        print(f"✓ GPS data found: {gps_file}")
        import pandas as pd
        try:
            df = pd.read_csv(gps_file)
            df = df.dropna(subset=['location_lat', 'location_long'])
            print(f"  {len(df)} GPS points available")
            animals = df['individual_local_identifier'].nunique()
            print(f"  {animals} animals tracked")
        except Exception as e:
            print(f"  Warning: Could not read file - {e}")
    else:
        print(f"✗ GPS data not found: {gps_file}")
        print(f"  Run: python fetch_movebank_data.py")
        return False

    individuals_file = data_dir / 'individuals.csv'
    if individuals_file.exists():
        print(f"✓ Individuals data found: {individuals_file}")
    else:
        print(f"○ Individuals data not found (optional): {individuals_file}")

    return True

if __name__ == "__main__":
    print("="*50)
    print("GPS VIEWER DEPENDENCY TEST")
    print("="*50 + "\n")

    deps_ok = test_imports()
    data_ok = check_data_files()

    print("\n" + "="*50)
    if deps_ok and data_ok:
        print("✓ READY TO RUN!")
        print("\nStart the application with:")
        print("  python gps_viewer.py")
    elif deps_ok:
        print("! DEPENDENCIES OK, but data missing")
        print("\nFetch data first:")
        print("  python fetch_movebank_data.py")
    else:
        print("! SETUP REQUIRED")
        print("\nInstall dependencies:")
        print("  pip install -r requirements_gps_viewer.txt")
    print("="*50)
