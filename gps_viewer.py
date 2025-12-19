"""
GPS Animal Movement Viewer with Google Earth Engine
This application visualizes GPS tracking data from Movebank with satellite imagery
Requires: tkinter, pandas, matplotlib, folium, earthengine-api
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import webbrowser
import tempfile
from math import radians, cos, sin, asin, sqrt
import pytz
import contextily as ctx
from pyproj import Transformer

try:
    import folium
    from folium import plugins
except ImportError:
    print("Installing folium...")
    os.system(f"{sys.executable} -m pip install folium")
    import folium
    from folium import plugins

try:
    import warnings
    # Suppress Google API warnings about Python version
    warnings.filterwarnings('ignore', category=FutureWarning, module='google.api_core')
    import ee
    EE_AVAILABLE = True
except ImportError:
    EE_AVAILABLE = False
    # Earth Engine is optional, so just note it quietly
    pass
except Exception as e:
    EE_AVAILABLE = False
    pass

try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.animation import FuncAnimation
except ImportError:
    print("Installing matplotlib...")
    os.system(f"{sys.executable} -m pip install matplotlib")
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.animation import FuncAnimation


def convert_to_web_mercator(lons, lats):
    """Convert lat/lon (EPSG:4326) to Web Mercator (EPSG:3857)"""
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    x, y = transformer.transform(lons, lats)
    return x, y

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers using Haversine formula"""
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # Earth radius in kilometers
    r = 6371
    return c * r

def calculate_sunrise_sunset(lat, lon, date):
    """Calculate sunrise and sunset times for a given location and date in Kenyan timezone"""
    try:
        from astral import LocationInfo
        from astral.sun import sun

        # Kenyan timezone (East Africa Time)
        kenyan_tz = pytz.timezone('Africa/Nairobi')

        location = LocationInfo(latitude=lat, longitude=lon)
        s = sun(location.observer, date=date, tzinfo=kenyan_tz)

        # Return sunrise and sunset in Kenyan time
        return s['sunrise'], s['sunset']
    except ImportError:
        # If astral not available, return None
        return None, None
    except Exception as e:
        print(f"Error calculating sunrise/sunset: {e}")
        return None, None

def is_daytime(lat, lon, timestamp):
    """Determine if it's daytime at given location and time"""
    try:
        # Convert timestamp to Kenyan timezone
        kenyan_tz = pytz.timezone('Africa/Nairobi')
        if timestamp.tzinfo is None:
            # Assume UTC if no timezone
            timestamp = pytz.utc.localize(timestamp)
        timestamp_kenyan = timestamp.astimezone(kenyan_tz)

        sunrise, sunset = calculate_sunrise_sunset(lat, lon, timestamp_kenyan.date())
        if sunrise and sunset:
            return sunrise <= timestamp_kenyan <= sunset
        else:
            # Fallback: assume daytime between 6 AM and 6 PM Kenyan time
            hour = timestamp_kenyan.hour
            return 6 <= hour <= 18
    except:
        # Fallback
        hour = timestamp.hour
        return 6 <= hour <= 18

def convert_to_kenyan_time(timestamp):
    """Convert timestamp to Kenyan timezone"""
    try:
        kenyan_tz = pytz.timezone('Africa/Nairobi')
        if timestamp.tzinfo is None:
            # Assume UTC if no timezone
            timestamp = pytz.utc.localize(timestamp)
        return timestamp.astimezone(kenyan_tz)
    except:
        return timestamp

class GPSViewer:
    def __init__(self, root, data_dir='movebank_data'):
        self.root = root
        self.root.title("GPS Animal Movement Viewer")
        self.root.geometry("1400x900")

        self.data_dir = Path(data_dir)
        self.gps_data = None
        self.filtered_data = None
        self.individuals_data = None
        self.current_map_file = None

        # Animation variables
        self.animation_playing = False
        self.animation_index = 0
        self.animation_timer = None

        # Earth Engine initialization (optional feature)
        self.ee_initialized = False
        if EE_AVAILABLE:
            try:
                ee.Initialize()
                self.ee_initialized = True
                print("Google Earth Engine: Ready")
            except Exception as e:
                # Earth Engine not authenticated - that's fine, we have alternatives
                pass

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Create the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="GPS Animal Movement Viewer",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Left panel - Controls
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)

        # Animal selection
        ttk.Label(control_frame, text="Select Animal:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.animal_var = tk.StringVar()
        self.animal_combo = ttk.Combobox(control_frame, textvariable=self.animal_var,
                                        width=25, state='readonly')
        self.animal_combo.grid(row=1, column=0, pady=5)
        self.animal_combo.bind('<<ComboboxSelected>>', self.on_animal_selected)

        # Date range
        ttk.Label(control_frame, text="Start Date:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.start_date_var = tk.StringVar()
        self.start_date_entry = ttk.Entry(control_frame, textvariable=self.start_date_var, width=27)
        self.start_date_entry.grid(row=3, column=0, pady=5)

        ttk.Label(control_frame, text="End Date:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.end_date_var = tk.StringVar()
        self.end_date_entry = ttk.Entry(control_frame, textvariable=self.end_date_var, width=27)
        self.end_date_entry.grid(row=5, column=0, pady=5)

        # Map options
        ttk.Label(control_frame, text="Base Map:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.map_type_var = tk.StringVar(value="OpenStreetMap")
        map_types = ["OpenStreetMap", "Satellite (Esri)", "Terrain"]
        if self.ee_initialized:
            map_types.insert(1, "Satellite (GEE)")
        self.map_type_combo = ttk.Combobox(control_frame, textvariable=self.map_type_var,
                                          values=map_types, width=25, state='readonly')
        self.map_type_combo.grid(row=7, column=0, pady=5)

        # Trail length control
        ttk.Label(control_frame, text="Trail Length:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.trail_length_var = tk.IntVar(value=50)
        self.trail_scale = ttk.Scale(control_frame, from_=0, to=200,
                                     variable=self.trail_length_var, orient=tk.HORIZONTAL)
        self.trail_scale.grid(row=9, column=0, sticky=(tk.W, tk.E), pady=5)

        # Position slider for manual control
        ttk.Label(control_frame, text="Track Position:").grid(row=10, column=0, sticky=tk.W, pady=5)
        self.position_var = tk.IntVar(value=0)
        self.position_slider = ttk.Scale(control_frame, from_=0, to=100,
                                        variable=self.position_var, orient=tk.HORIZONTAL,
                                        command=self.on_position_changed)
        self.position_slider.grid(row=11, column=0, sticky=(tk.W, tk.E), pady=5)

        # Buttons
        ttk.Button(control_frame, text="Generate Map",
                  command=self.generate_map).grid(row=12, column=0, pady=10, sticky=(tk.W, tk.E))

        ttk.Button(control_frame, text="Save Map as Image",
                  command=self.save_map_image).grid(row=13, column=0, pady=5, sticky=(tk.W, tk.E))

        ttk.Button(control_frame, text="Open in Browser",
                  command=self.open_in_browser).grid(row=14, column=0, pady=5, sticky=(tk.W, tk.E))

        # Animation controls
        anim_frame = ttk.LabelFrame(control_frame, text="Animation", padding="5")
        anim_frame.grid(row=15, column=0, pady=10, sticky=(tk.W, tk.E))

        self.play_button = ttk.Button(anim_frame, text="Play",
                                     command=self.toggle_animation)
        self.play_button.grid(row=0, column=0, padx=2)

        ttk.Button(anim_frame, text="Reset",
                  command=self.reset_animation).grid(row=0, column=1, padx=2)

        ttk.Label(anim_frame, text="Speed:").grid(row=1, column=0, sticky=tk.W)
        self.anim_speed_var = tk.IntVar(value=100)
        self.anim_speed_scale = ttk.Scale(anim_frame, from_=10, to=1000,
                                         variable=self.anim_speed_var, orient=tk.HORIZONTAL)
        self.anim_speed_scale.grid(row=1, column=1, sticky=(tk.W, tk.E))

        # Stats panel
        stats_frame = ttk.LabelFrame(control_frame, text="Statistics", padding="5")
        stats_frame.grid(row=16, column=0, pady=10, sticky=(tk.W, tk.E))

        self.stats_text = ScrolledText(stats_frame, width=30, height=8, wrap=tk.WORD)
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Center panel - Map preview (expanded to take full width)
        map_frame = ttk.LabelFrame(main_frame, text="GPS Track Map", padding="10")
        map_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(1, weight=1)

        # Create matplotlib figure for map preview
        self.map_fig = Figure(figsize=(10, 8), dpi=100)
        self.map_canvas = FigureCanvasTkAgg(self.map_fig, master=map_frame)
        self.map_canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        map_frame.columnconfigure(0, weight=1)
        map_frame.rowconfigure(0, weight=1)

        # Initial message on map preview
        self.map_ax = self.map_fig.add_subplot(111)
        self.map_ax.text(0.5, 0.5, 'Click "Generate Map"\nto preview GPS track',
                        ha='center', va='center', fontsize=14, transform=self.map_ax.transAxes)
        self.map_ax.axis('off')
        self.map_canvas.draw()

        # Store animation elements
        self.current_position_marker = None
        self.trail_line = None
        self.track_line = None

        # Day/night and distance info
        self.total_distance = 0
        self.show_preview_var = tk.BooleanVar(value=True)
        self.show_track_var = tk.BooleanVar(value=True)
        self.show_markers_var = tk.BooleanVar(value=True)
        self.show_heatmap_var = tk.BooleanVar(value=False)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

    def load_data(self):
        """Load GPS data and individual information"""
        try:
            # Load GPS data
            gps_file = self.data_dir / 'events_gps.csv'
            if not gps_file.exists():
                messagebox.showerror("Error", f"GPS data file not found: {gps_file}")
                return

            self.status_var.set("Loading GPS data...")
            self.root.update()

            print(f"Loading GPS data from: {gps_file}")
            # Force individual_local_identifier to be read as string to avoid type issues
            self.gps_data = pd.read_csv(gps_file, dtype={'individual_local_identifier': str})
            print(f"Loaded {len(self.gps_data)} rows")

            # Convert timestamp to datetime
            print("Converting timestamps...")
            self.gps_data['timestamp'] = pd.to_datetime(self.gps_data['timestamp'])

            # Filter out rows without coordinates
            print("Filtering rows without coordinates...")
            before_filter = len(self.gps_data)
            self.gps_data = self.gps_data.dropna(subset=['location_lat', 'location_long'])
            print(f"Filtered from {before_filter} to {len(self.gps_data)} rows")

            # Load individuals data if available
            individuals_file = self.data_dir / 'individuals.csv'
            if individuals_file.exists():
                print(f"Loading individuals data from: {individuals_file}")
                self.individuals_data = pd.read_csv(individuals_file)

            # Populate animal dropdown
            print("Populating animal list...")
            animals = self.gps_data['individual_local_identifier'].dropna().unique()
            # Convert all to strings to avoid type comparison errors when sorting
            animals_str = sorted([str(a) for a in animals])
            self.animal_combo['values'] = animals_str
            print(f"Found {len(animals)} animals")

            if len(animals_str) > 0:
                self.animal_combo.current(0)
                print(f"Auto-selecting first animal: {animals_str[0]}")
                self.on_animal_selected()

            self.status_var.set(f"Loaded {len(self.gps_data)} GPS points from {len(animals_str)} animals")
            print("Data loading complete!")

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR during data loading:")
            print(error_details)
            messagebox.showerror("Error", f"Failed to load data: {str(e)}\n\nSee console for details.")
            self.status_var.set("Error loading data")

    def on_animal_selected(self, event=None):
        """Handle animal selection"""
        animal = self.animal_var.get()
        if not animal or self.gps_data is None:
            return

        # Filter data for selected animal (convert to string to ensure matching)
        animal_data = self.gps_data[self.gps_data['individual_local_identifier'].astype(str) == str(animal)]

        if len(animal_data) == 0:
            return

        # Set date range
        min_date = animal_data['timestamp'].min()
        max_date = animal_data['timestamp'].max()
        self.start_date_var.set(min_date.strftime('%Y-%m-%d'))
        self.end_date_var.set(max_date.strftime('%Y-%m-%d'))

        # Update filtered data
        self.filter_data()

        # Update map preview
        self.update_map_preview()

        # Update statistics
        self.update_statistics()

    def calculate_total_distance(self):
        """Calculate total distance traveled in kilometers"""
        if self.filtered_data is None or len(self.filtered_data) < 2:
            return 0

        total = 0
        for i in range(1, len(self.filtered_data)):
            lat1 = self.filtered_data['location_lat'].iloc[i-1]
            lon1 = self.filtered_data['location_long'].iloc[i-1]
            lat2 = self.filtered_data['location_lat'].iloc[i]
            lon2 = self.filtered_data['location_long'].iloc[i]
            total += haversine_distance(lat1, lon1, lat2, lon2)

        return total

    def on_position_changed(self, value):
        """Handle manual position slider changes"""
        if self.filtered_data is None or len(self.filtered_data) == 0:
            return

        # Stop animation if playing
        if self.animation_playing:
            self.toggle_animation()

        # Calculate position index from slider value
        position = int(float(value))
        max_index = len(self.filtered_data) - 1
        index = int((position / 100) * max_index)
        index = max(1, min(index, max_index))

        # Update the display
        self.animation_index = index
        self.update_map_preview_animated(index)

    def filter_data(self):
        """Filter data based on animal and date range"""
        if self.gps_data is None:
            return

        animal = self.animal_var.get()
        if not animal:
            return

        # Filter by animal (convert to string to ensure matching)
        data = self.gps_data[self.gps_data['individual_local_identifier'].astype(str) == str(animal)].copy()

        # Filter by date range
        try:
            start_date = pd.to_datetime(self.start_date_var.get())
            end_date = pd.to_datetime(self.end_date_var.get()) + timedelta(days=1)
            data = data[(data['timestamp'] >= start_date) & (data['timestamp'] < end_date)]
        except:
            pass

        # Sort by timestamp
        data = data.sort_values('timestamp')

        self.filtered_data = data


    def update_map_preview_animated(self, num_points):
        """Update map preview - move point along fixed trajectory with trail"""
        if self.filtered_data is None or len(self.filtered_data) == 0:
            return

        if not self.show_preview_var.get():
            return

        try:
            # Get current position
            current_lat = self.filtered_data['location_lat'].iloc[num_points - 1]
            current_lon = self.filtered_data['location_long'].iloc[num_points - 1]
            current_time = self.filtered_data['timestamp'].iloc[num_points - 1]

            # Convert to Kenyan time
            current_time_kenyan = convert_to_kenyan_time(current_time)

            # Calculate distance traveled so far
            distance_so_far = 0
            for i in range(1, num_points):
                lat1 = self.filtered_data['location_lat'].iloc[i-1]
                lon1 = self.filtered_data['location_long'].iloc[i-1]
                lat2 = self.filtered_data['location_lat'].iloc[i]
                lon2 = self.filtered_data['location_long'].iloc[i]
                distance_so_far += haversine_distance(lat1, lon1, lat2, lon2)

            # Determine day/night
            is_day = is_daytime(current_lat, current_lon, current_time)
            day_night_text = "☀️ Day" if is_day else "🌙 Night"

            # Get sunrise/sunset times in Kenyan time
            sunrise, sunset = calculate_sunrise_sunset(current_lat, current_lon, current_time_kenyan.date())
            sun_info = ""
            if sunrise and sunset:
                sun_info = f" | Sunrise: {sunrise.strftime('%H:%M')} Sunset: {sunset.strftime('%H:%M')} EAT"

            # Remove old trail if it exists
            if self.trail_line:
                self.trail_line.remove()

            # Draw trail (path traveled so far) - convert to Web Mercator
            trail_length = self.trail_length_var.get()
            if trail_length > 0:
                start_idx = max(0, num_points - trail_length)
                trail_lats = self.filtered_data['location_lat'].iloc[start_idx:num_points]
                trail_lons = self.filtered_data['location_long'].iloc[start_idx:num_points]

                # Convert to Web Mercator for display
                trail_x, trail_y = convert_to_web_mercator(trail_lons, trail_lats)

                self.trail_line = self.map_ax.plot(
                    trail_x, trail_y, 'orange',
                    linewidth=4, alpha=0.8, zorder=8
                )[0]

            # Remove old position marker if it exists
            if self.current_position_marker:
                self.current_position_marker.remove()

            # Convert current position to Web Mercator
            current_x, current_y = convert_to_web_mercator(current_lon, current_lat)

            # Draw new position marker (large dot, color based on day/night)
            marker_color = 'yellow' if is_day else 'navy'
            edge_color = 'orange' if is_day else 'cyan'
            self.current_position_marker = self.map_ax.plot(
                current_x, current_y, 'o',
                color=marker_color,
                markersize=20,
                markeredgecolor=edge_color,
                markeredgewidth=3,
                zorder=10
            )[0]

            # Update title with progress and info in Kenyan time
            progress = int(100 * num_points / len(self.filtered_data))
            self.map_ax.set_title(
                f'{self.animal_var.get()} - GPS Track\n'
                f'{num_points}/{len(self.filtered_data)} ({progress}%) | '
                f'Distance: {distance_so_far:.2f}/{self.total_distance:.2f} km | {day_night_text}\n'
                f'{current_time_kenyan.strftime("%Y-%m-%d %H:%M:%S EAT")}{sun_info}',
                fontsize=10, fontweight='bold'
            )

            # Update position slider
            slider_pos = int((num_points / len(self.filtered_data)) * 100)
            self.position_var.set(slider_pos)

            # Redraw only the changed elements (faster)
            self.map_canvas.draw_idle()

        except Exception as e:
            import traceback
            print(f"ERROR in animated map preview:")
            print(traceback.format_exc())


    def update_statistics(self):
        """Update statistics display"""
        if self.filtered_data is None or len(self.filtered_data) == 0:
            return

        stats = []
        stats.append(f"Animal: {self.animal_var.get()}\n")
        stats.append(f"Total Points: {len(self.filtered_data)}\n\n")

        # Calculate and display total distance
        self.total_distance = self.calculate_total_distance()
        stats.append(f"Distance Traveled:\n")
        stats.append(f"  {self.total_distance:.2f} km\n")
        stats.append(f"  {self.total_distance * 0.621371:.2f} miles\n\n")

        stats.append(f"Date Range:\n  {self.filtered_data['timestamp'].min().strftime('%Y-%m-%d')}\n  to {self.filtered_data['timestamp'].max().strftime('%Y-%m-%d')}\n")
        duration_days = (self.filtered_data['timestamp'].max() - self.filtered_data['timestamp'].min()).days
        stats.append(f"Duration: {duration_days} days\n")

        if duration_days > 0:
            avg_per_day = self.total_distance / duration_days
            stats.append(f"Avg: {avg_per_day:.2f} km/day\n")

        # Bounding box
        lat_min = self.filtered_data['location_lat'].min()
        lat_max = self.filtered_data['location_lat'].max()
        lon_min = self.filtered_data['location_long'].min()
        lon_max = self.filtered_data['location_long'].max()
        stats.append(f"\nBounding Box:\n")
        stats.append(f"  Lat: {lat_min:.4f}°\n       to {lat_max:.4f}°\n")
        stats.append(f"  Lon: {lon_min:.4f}°\n       to {lon_max:.4f}°\n")

        # Speed statistics
        if 'ground_speed' in self.filtered_data.columns:
            speeds = self.filtered_data['ground_speed'].dropna()
            if len(speeds) > 0:
                stats.append(f"\nSpeed (m/s):\n")
                stats.append(f"  Mean: {speeds.mean():.2f}\n")
                stats.append(f"  Max: {speeds.max():.2f}\n")

        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, ''.join(stats))

    def update_map_preview(self):
        """Update map preview with FULL GPS track ON OpenStreetMap"""
        if self.filtered_data is None or len(self.filtered_data) == 0:
            return

        if not self.show_preview_var.get():
            return

        try:
            print("Updating map preview with OpenStreetMap...")
            self.map_fig.clear()
            self.map_ax = self.map_fig.add_subplot(111)

            # Get coordinates
            lats = self.filtered_data['location_lat']
            lons = self.filtered_data['location_long']

            # Calculate total distance
            self.total_distance = self.calculate_total_distance()

            # Convert to Web Mercator (EPSG:3857) for contextily
            x, y = convert_to_web_mercator(lons, lats)

            # Plot the FULL track in Web Mercator coordinates
            self.map_ax.plot(x, y, 'b-', linewidth=3, alpha=0.7, label='GPS Track', zorder=5)

            # Plot start and end points (x, y are numpy arrays)
            self.map_ax.plot(x[0], y[0], 'go', markersize=14, label='Start', zorder=6)
            self.map_ax.plot(x[-1], y[-1], 'r^', markersize=14, label='End', zorder=6)

            # Add OpenStreetMap basemap
            print("Fetching OpenStreetMap tiles...")
            ctx.add_basemap(
                self.map_ax,
                source=ctx.providers.OpenStreetMap.Mapnik,
                zoom='auto',
                attribution_size=6
            )

            # Set title
            self.map_ax.set_title(
                f'{self.animal_var.get()} - GPS Track on OpenStreetMap\n'
                f'{len(self.filtered_data)} points | Total Distance: {self.total_distance:.2f} km',
                fontsize=12, fontweight='bold'
            )

            # Add legend with better positioning
            self.map_ax.legend(loc='upper left', fontsize=10, framealpha=0.95,
                             edgecolor='black', fancybox=True)

            # Remove axis labels (they're in Web Mercator, not meaningful)
            self.map_ax.set_xlabel('')
            self.map_ax.set_ylabel('')

            # Set axis limits with margin (in Web Mercator) - x, y are numpy arrays
            import numpy as np
            x_margin = (np.max(x) - np.min(x)) * 0.1
            y_margin = (np.max(y) - np.min(y)) * 0.1
            self.map_ax.set_xlim(np.min(x) - x_margin, np.max(x) + x_margin)
            self.map_ax.set_ylim(np.min(y) - y_margin, np.max(y) + y_margin)

            self.map_fig.tight_layout()
            self.map_canvas.draw()

            # Reset markers and position slider
            self.current_position_marker = None
            self.trail_line = None
            self.position_var.set(0)

            print("Map preview with OpenStreetMap updated successfully!")

        except Exception as e:
            import traceback
            print(f"ERROR updating map preview:")
            print(traceback.format_exc())
            messagebox.showwarning("Map Error",
                f"Could not load OpenStreetMap tiles. Check internet connection.\n{str(e)}")

    def generate_map(self):
        """Generate interactive map with GPS tracks"""
        self.filter_data()

        if self.filtered_data is None or len(self.filtered_data) == 0:
            messagebox.showwarning("Warning", "No data to display")
            return

        self.status_var.set("Generating map...")
        self.root.update()

        # Update map preview first
        self.update_map_preview()

        try:
            # Calculate center
            center_lat = self.filtered_data['location_lat'].mean()
            center_lon = self.filtered_data['location_long'].mean()

            # Create base map
            map_type = self.map_type_var.get()

            if map_type == "Satellite (GEE)" and self.ee_initialized:
                m = self.create_gee_map(center_lat, center_lon)
            else:
                # Use folium for other map types
                if map_type == "Satellite (Esri)":
                    tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
                    attr = 'Esri'
                elif map_type == "Terrain":
                    tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}'
                    attr = 'Esri'
                else:
                    tiles = 'OpenStreetMap'
                    attr = None

                m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

                if tiles != 'OpenStreetMap':
                    folium.TileLayer(tiles=tiles, attr=attr, name='basemap').add_to(m)

            # Add GPS track line
            if self.show_track_var.get():
                points = [[row['location_lat'], row['location_long']]
                         for _, row in self.filtered_data.iterrows()]
                folium.PolyLine(points, color='blue', weight=2, opacity=0.7,
                              popup=f"Track: {self.animal_var.get()}").add_to(m)

            # Add point markers
            if self.show_markers_var.get():
                # Sample points if too many
                display_data = self.filtered_data
                if len(display_data) > 500:
                    display_data = display_data.iloc[::len(display_data)//500]

                for idx, row in display_data.iterrows():
                    popup_text = f"""
                    <b>Time:</b> {row['timestamp']}<br>
                    <b>Lat:</b> {row['location_lat']:.6f}<br>
                    <b>Lon:</b> {row['location_long']:.6f}<br>
                    """
                    if 'ground_speed' in row and pd.notna(row['ground_speed']):
                        popup_text += f"<b>Speed:</b> {row['ground_speed']:.2f} m/s<br>"

                    folium.CircleMarker(
                        location=[row['location_lat'], row['location_long']],
                        radius=3,
                        popup=folium.Popup(popup_text, max_width=200),
                        color='red',
                        fill=True,
                        fillColor='red',
                        fillOpacity=0.6
                    ).add_to(m)

            # Add heatmap
            if self.show_heatmap_var.get():
                heat_data = [[row['location_lat'], row['location_long']]
                           for _, row in self.filtered_data.iterrows()]
                plugins.HeatMap(heat_data).add_to(m)

            # Add start and end markers
            if len(self.filtered_data) > 0:
                start = self.filtered_data.iloc[0]
                end = self.filtered_data.iloc[-1]

                folium.Marker(
                    [start['location_lat'], start['location_long']],
                    popup=f"Start: {start['timestamp']}",
                    icon=folium.Icon(color='green', icon='play')
                ).add_to(m)

                folium.Marker(
                    [end['location_lat'], end['location_long']],
                    popup=f"End: {end['timestamp']}",
                    icon=folium.Icon(color='red', icon='stop')
                ).add_to(m)

            # Save map
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html')
            self.current_map_file = temp_file.name
            m.save(self.current_map_file)

            self.status_var.set(f"Map generated with {len(self.filtered_data)} points - Preview updated")

            # Do NOT auto-open browser - user can click "Open in Browser" if needed

        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate map: {str(e)}")
            self.status_var.set("Error generating map")
            import traceback
            traceback.print_exc()

    def create_gee_map(self, center_lat, center_lon):
        """Create map with Google Earth Engine satellite imagery"""
        try:
            # Get Landsat or Sentinel imagery
            # Define region of interest
            point = ee.Geometry.Point([center_lon, center_lat])
            region = point.buffer(5000)  # 5km buffer

            # Get recent Sentinel-2 imagery
            image = ee.ImageCollection('COPERNICUS/S2_SR') \
                .filterBounds(region) \
                .filterDate('2024-01-01', '2025-12-31') \
                .sort('CLOUDY_PIXEL_PERCENTAGE') \
                .first()

            # Visualization parameters
            vis_params = {
                'min': 0,
                'max': 3000,
                'bands': ['B4', 'B3', 'B2']
            }

            # Get tile URL
            map_id = image.getMapId(vis_params)
            tiles_url = map_id['tile_fetcher'].url_format

            # Create folium map with GEE layer
            m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
            folium.TileLayer(
                tiles=tiles_url,
                attr='Google Earth Engine',
                name='Satellite (GEE)',
                overlay=True,
                control=True
            ).add_to(m)

            return m

        except Exception as e:
            print(f"Failed to create GEE map: {e}")
            # Fallback to regular satellite map
            m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
            tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
            folium.TileLayer(tiles=tiles, attr='Esri', name='Satellite').add_to(m)
            return m

    def save_map_image(self):
        """Save the map preview as an image file"""
        if self.filtered_data is None or len(self.filtered_data) == 0:
            messagebox.showwarning("Warning", "Please generate a map first")
            return

        try:
            # Ask user for filename
            from tkinter import filedialog
            default_name = f"{self.animal_var.get()}_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                initialfile=default_name,
                filetypes=[
                    ("PNG Image", "*.png"),
                    ("JPEG Image", "*.jpg"),
                    ("PDF Document", "*.pdf"),
                    ("All Files", "*.*")
                ]
            )

            if filename:
                # Save the current map preview
                self.map_fig.savefig(filename, dpi=300, bbox_inches='tight')
                self.status_var.set(f"Map saved to: {filename}")
                messagebox.showinfo("Success", f"Map saved successfully!\n\n{filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save map: {str(e)}")

    def open_in_browser(self):
        """Open current map in web browser"""
        if self.current_map_file and os.path.exists(self.current_map_file):
            webbrowser.open('file://' + self.current_map_file)
        else:
            messagebox.showwarning("Warning", "Please generate a map first")

    def toggle_animation(self):
        """Start/stop animation"""
        if self.animation_playing:
            self.animation_playing = False
            self.play_button.config(text="Play")
            if self.animation_timer:
                self.root.after_cancel(self.animation_timer)
        else:
            self.animation_playing = True
            self.play_button.config(text="Pause")
            self.animate_step()

    def reset_animation(self):
        """Reset animation to start"""
        self.animation_index = 0
        self.animation_playing = False
        self.play_button.config(text="Play")
        if self.animation_timer:
            self.root.after_cancel(self.animation_timer)

        # Restore map preview to full view
        self.update_map_preview()

        # Restore normal status message
        if self.filtered_data is not None:
            self.status_var.set(f"Animation reset - {len(self.filtered_data)} points ready")

    def animate_step(self):
        """Perform one animation step"""
        if not self.animation_playing or self.filtered_data is None:
            return

        if self.animation_index >= len(self.filtered_data):
            self.reset_animation()
            return

        # Update visualization to show data up to current index
        self.animation_index += 1

        # Update map preview with moving point
        self.update_map_preview_animated(self.animation_index)

        # Update status
        progress = int(100 * self.animation_index / len(self.filtered_data))
        self.status_var.set(f"Animation: {progress}% ({self.animation_index}/{len(self.filtered_data)} points)")

        # Schedule next step
        delay = max(10, int(1000 / self.anim_speed_var.get()))  # Minimum 10ms delay
        self.animation_timer = self.root.after(delay, self.animate_step)


def main():
    """Main entry point"""
    root = tk.Tk()

    # Set default data directory
    data_dir = 'movebank_data'
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]

    app = GPSViewer(root, data_dir)
    root.mainloop()


if __name__ == "__main__":
    main()
