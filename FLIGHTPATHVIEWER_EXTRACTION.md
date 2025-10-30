# FlightPathViewer.py Logic Extraction for SFTP Server Deployment

## Overview
This document summarizes the key plotting logic extracted from `FlightPathViewer.py` and implemented in the web-based QC Tool for SFTP server deployment.

## Source Analysis
- **Source File**: `/Users/rileybellin/Desktop/QC TOOL/FlightPathViewer.py`
- **Key Function**: `plot_3d_flight_path()` (lines 2931-3091)
- **Total Lines**: 6,727 lines

## Extracted Core Logic Components

### 1. GPS Data Extraction (`get_gps_data()` - lines 1869-1903)

```python
def extract_gps_from_exif(image_bytes):
    """
    Extract GPS coordinates and altitude from image EXIF data using exifread.

    Key Features:
    - Uses DJI 'RelativeAltitude' (preferred for drone altitude AGL)
    - Falls back to GPS Altitude if RelativeAltitude not available
    - Converts coordinates from DMS (degrees, minutes, seconds) to decimal
    - Converts altitude from meters to feet (×3.28084)

    Returns:
        dict: {
            'latitude': float,
            'longitude': float,
            'altitude': float (feet AGL),
            'timestamp': datetime or None
        }
    """
```

**Implementation Details:**
- Checks for `Xmp.drone-dji.RelativeAltitude` or `Xmp.DJI.RelativeAltitude` tags
- Reads GPS coordinates from standard GPS tags
- Handles N/S latitude reference and E/W longitude reference
- Only reads first 64KB of each image (EXIF header only) for performance

### 2. Outlier Detection (lines 2956-3001)

**Algorithm: IQR (Interquartile Range) Method**

```python
# Calculate Q1 and Q3 for latitude and longitude
q1_lat, q3_lat = np.percentile(lats_arr, [25, 75])
q1_lon, q3_lon = np.percentile(lons_arr, [25, 75])
iqr_lat = q3_lat - q1_lat
iqr_lon = q3_lon - q1_lon

# Use 4.0 multiplier for geographic data (wider tolerance)
multiplier = 4.0
bounds = {
    'lat_low': q1_lat - multiplier * iqr_lat,
    'lat_high': q3_lat + multiplier * iqr_lat,
    'lon_low': q1_lon - multiplier * iqr_lon,
    'lon_high': q3_lon + multiplier * iqr_lon
}
```

**Key Points:**
- Excludes 'civil' and 'road' folders from outlier calculation
- Uses 4.0× multiplier (more lenient than standard 1.5×) for geographic spread
- Separates data into inliers and outliers for different visualization
- Outliers displayed as red 'X' markers

### 3. Ground Plane Generation (lines 3011-3020)

```python
# Calculate ground level based on minimum altitude
z_min_rel = min(inlier_agls)
ground_z = z_min_rel - 20  # 20 feet below minimum

# Create 20×20 mesh grid
nx = ny = 20
xs = np.linspace(lon_min, lon_max, nx)
ys = np.linspace(lat_min, lat_max, ny)
x_mesh, y_mesh = np.meshgrid(xs, ys)
z_mesh = np.full_like(x_mesh, ground_z)

# Add dark green ground surface
fig.add_trace(go.Surface(
    x=x_mesh, y=y_mesh, z=z_mesh,
    colorscale=[[0, '#002200'], [1, '#002200']],  # Dark green
    showscale=False,
    opacity=1.0,
    hoverinfo='skip',
    name='Ground'
))
```

### 4. Axis Range Calculation (lines 3003-3009)

**Based on INLIERS ONLY** (excludes outliers for proper visualization):

```python
lat_min, lat_max = min(inlier_lats), max(inlier_lats)
lon_min, lon_max = min(inlier_lons), max(inlier_lons)
data_max = max(inlier_agls)
z_max = max(data_max, 100)  # At least 100 feet
z_min_rel = min(inlier_agls)
ground_z = z_min_rel - 20
```

**Critical Feature:**
- Uses `autorange=False` to lock axes to inlier bounds
- Prevents outliers from distorting the view
- Ensures consistent scale across all axes

### 5. Data Visualization (lines 3022-3073)

**Folder Color Mapping:**
```python
FOLDER_COLORS = {
    'orbit': '#ff4136',     # Red
    'scan': '#2ecc40',      # Green
    'center': '#0074d9',    # Blue
    'downlook': '#ffdc00',  # Yellow
    'uplook': '#b10dc9',    # Purple
    'civil': '#ff851b',     # Orange
    'road': '#39cccc',      # Teal
    'default': '#aaaaaa'    # Gray
}
```

**Trace Configuration:**
- **Inliers**: 6px markers, folder-specific color, 0.95 opacity
- **Outliers**: 8px red 'X' markers with 2px border
- Legend format: `"{folder} ({size} - {count} files)"`
- Hover template shows only filename

### 6. Layout Configuration (lines 3076-3089)

**Dark Theme Settings:**
```python
fig.update_layout(
    title=dict(
        text="Site {site_id} - Pilot: {pilot_name}",
        x=0.12,  # Left-aligned
        xanchor='left',
        font=dict(size=20, color='#e0e0e0')
    ),
    scene=dict(
        xaxis=dict(
            title='Longitude',
            gridcolor='gray',
            zerolinecolor='gray',
            tickfont=dict(color='#e0e0e0'),
            autorange=False,  # CRITICAL: Fixed range
            range=[lon_min, lon_max]
        ),
        yaxis=dict(
            title='Latitude',
            gridcolor='gray',
            zerolinecolor='gray',
            tickfont=dict(color='#e0e0e0'),
            autorange=False,
            range=[lat_min, lat_max]
        ),
        zaxis=dict(
            title='Height Above Drone Takeoff',
            gridcolor='gray',
            zerolinecolor='gray',
            tickfont=dict(color='#e0e0e0'),
            autorange=False,
            range=[ground_z, z_max]
        ),
        bgcolor='black',
        camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
    ),
    template='plotly_dark',
    margin=dict(l=0, r=0, b=0, t=80),
    showlegend=True,
    legend=dict(
        orientation="v",
        x=0,
        y=1,
        font=dict(size=12),
        bgcolor="rgba(0,0,0,0)"  # Transparent background
    ),
    height=800
)
```

### 7. HTML Export (line 3091)

```python
html = fig.to_html(
    full_html=False,
    include_plotlyjs=True,  # In desktop version
    # For web: include_plotlyjs='cdn'  # CDN version for innerHTML compatibility
    config={'scrollZoom': True, 'displayModeBar': True, 'responsive': True},
    div_id='flight-path-plot'
)
```

## Implementation for Web/SFTP Environment

### Key Adaptations for Server Deployment

1. **File Access via SFTP**
   - Read only first 64KB per image for EXIF data
   - No full image downloads for GPS extraction
   - Connection pooling avoided due to SFTP threading issues

2. **Performance Optimizations**
   - Sequential EXIF processing (safer with SFTP)
   - Progress logging every 20 images
   - Thumbnail generation disabled for initial MVP

3. **Data Structure Changes**
   ```python
   # Desktop version uses tuples:
   point = (lat, lon, agl, timestamp, date_obj, rel_path, thumb_path)

   # Web version uses dicts for clarity:
   point = {
       'folder': folder_name,
       'filename': image_file['name'],
       'filepath': image_path,
       'latitude': lat,
       'longitude': lon,
       'altitude': agl,
       'timestamp': timestamp
   }
   ```

4. **HTML Delivery**
   - Desktop: Opens local HTML file in browser
   - Web: Returns HTML fragment for Flask template insertion
   - Uses CDN for Plotly.js (required for `innerHTML` insertion)

## Files Modified in Web Application

1. **[site_analysis_service.py](src/backend/services/site_analysis_service.py)**
   - `extract_gps_from_exif()` - GPS extraction logic
   - `generate_flight_path_visualization()` - Complete plotting logic
   - `format_size_bytes()` - File size formatting
   - `analyze_folder()` - Folder analysis with GPS extraction

2. **Frontend Integration** (already implemented)
   - [qc_viewer.html](src/frontend/templates/qc_viewer.html)
   - [qc_viewer.js](src/frontend/static/js/qc_viewer.js)

## Testing Checklist

- [ ] GPS extraction from DJI drone images (RelativeAltitude)
- [ ] GPS extraction from non-DJI images (GPSAltitude fallback)
- [ ] Outlier detection with 4.0× multiplier
- [ ] Ground plane at correct altitude (min - 20ft)
- [ ] Fixed axis ranges (no autorange)
- [ ] Folder color mapping
- [ ] Legend with file sizes and counts
- [ ] Outlier markers (red X)
- [ ] Dark theme rendering
- [ ] Interactive 3D rotation
- [ ] Scroll zoom functionality

## Performance Metrics

**Desktop Version** (FlightPathViewer.py):
- Reads from local filesystem
- Can process 1000+ images in ~30 seconds
- Uses threading for thumbnail generation

**Web/SFTP Version** (site_analysis_service.py):
- Reads 64KB per image over SFTP
- Sequential processing (SFTP-safe)
- ~1-2 seconds per image (network dependent)
- Progress logging for user feedback

## Key Differences from Desktop Version

| Feature | Desktop | Web/SFTP |
|---------|---------|----------|
| File Access | Local filesystem | SFTP connection |
| Thumbnails | Pre-generated | Disabled (MVP) |
| Threading | Multi-threaded | Sequential |
| Cache | JSON file cache | No cache (MVP) |
| UI Framework | Tkinter | Flask/HTML/JS |
| Plotly.js | Bundled | CDN |
| Progress | Progress bar | Server logs |

## Future Enhancements

1. **Caching System**
   - Store GPS data in session/database
   - Avoid re-processing same images

2. **Thumbnail Support**
   - Partial file reads (512KB) for thumbnails
   - Local cache directory on server

3. **Multi-threaded SFTP**
   - Connection pooling with proper cleanup
   - Parallel GPS extraction

4. **Real-time Progress**
   - WebSocket updates to frontend
   - Live progress bar during analysis

## Conclusion

The web-based QC Tool now implements the identical plotting logic from FlightPathViewer.py:
- ✅ Exact outlier detection algorithm
- ✅ Identical ground plane calculation
- ✅ Same axis range logic (inlier-based)
- ✅ Matching color scheme and styling
- ✅ Proper GPS extraction from DJI metadata
- ✅ SFTP-compatible implementation

The visualization should now produce identical results to the desktop version when viewing the same site data.
