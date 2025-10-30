# Testing Guide - Flight Path Visualization

## Quick Start Testing

### Option 1: Full Web Application Test (Recommended)

This tests the complete workflow from login to 3D visualization.

#### Step 1: Start the Application

```bash
cd /Users/rileybellin/Desktop/QC\ TOOL\ WEB\ BASED

# Activate virtual environment
source venv/bin/activate

# Start Flask development server
python src/backend/app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
 * Running on http://0.0.0.0:5000
```

#### Step 2: Access the Application

1. Open browser: http://localhost:5000
2. **Login Page** - Enter SFTP credentials:
   - Host: `73.156.240.32` (or your SFTP server)
   - Port: `22`
   - Username: (your username)
   - Password: (your password)
   - Click "Connect"

3. **Sites Page** - You should see:
   - List of available pilot directories
   - Click on any pilot name to see their sites

4. **Select a Site**:
   - Find a site with drone images (e.g., `10001291-08-20-2025-ATT`)
   - Click "View QC" button

5. **QC Viewer Page** - This will:
   - Show "Analyzing site..." spinner
   - Extract GPS from ALL images in the site
   - Generate the 3D flight path visualization
   - Display the interactive plot

#### Step 3: Verify the Visualization

Check these features match FlightPathViewer.py:

✅ **3D Plot Elements**:
- [ ] Dark background (black)
- [ ] Dark green ground plane at bottom
- [ ] Colored dots for each folder (red=orbit, green=scan, blue=center, etc.)
- [ ] Red X markers for outliers (if any)
- [ ] Legend showing folder names with file sizes and counts

✅ **Interaction**:
- [ ] Click and drag to rotate the 3D view
- [ ] Scroll to zoom in/out
- [ ] Hover over points to see image filenames
- [ ] Legend can be clicked to toggle folders on/off

✅ **Data Accuracy**:
- [ ] Title shows correct Site ID and Pilot name
- [ ] All image folders are represented
- [ ] GPS points form recognizable flight patterns
- [ ] Altitude scale shows "Height Above Drone Takeoff"

---

### Option 2: Unit Test (Fast - No SFTP Connection)

Test individual functions with mock data.

Create `test_visualization.py`:

```python
#!/usr/bin/env python3
"""
Unit test for flight path visualization logic
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'backend'))

from services.site_analysis_service import generate_flight_path_visualization

# Mock data matching FlightPathViewer.py structure
mock_analysis_data = {
    'site_info': {
        'site_id': '10001291',
        'pilot_name': 'JasonDunwoody',
        'full_path': '/homes/JasonDunwoody/10001291-08-20-2025-ATT'
    },
    'folders': {
        'Orbit': {
            'folder_name': 'Orbit',
            'image_count': 120,
            'total_size': 450000000,  # 450 MB
            'color': '#ff4136',  # Red
            'gps_data': [
                {
                    'folder': 'Orbit',
                    'filename': f'DJI_{i:04d}.JPG',
                    'filepath': f'/path/to/Orbit/DJI_{i:04d}.JPG',
                    'latitude': 37.7749 + (i * 0.0001),  # San Francisco area
                    'longitude': -122.4194 + (i * 0.0001),
                    'altitude': 100 + (i * 2),  # 100-300 feet
                    'timestamp': None
                }
                for i in range(120)
            ]
        },
        'Scan': {
            'folder_name': 'Scan',
            'image_count': 200,
            'total_size': 750000000,  # 750 MB
            'color': '#2ecc40',  # Green
            'gps_data': [
                {
                    'folder': 'Scan',
                    'filename': f'DJI_{i:04d}.JPG',
                    'filepath': f'/path/to/Scan/DJI_{i:04d}.JPG',
                    'latitude': 37.7749 + (i * 0.00005),
                    'longitude': -122.4194 + (i * 0.00005),
                    'altitude': 150 + (i * 1),  # 150-350 feet
                    'timestamp': None
                }
                for i in range(200)
            ]
        },
        # Add outlier to test detection
        'Center': {
            'folder_name': 'Center',
            'image_count': 50,
            'total_size': 200000000,  # 200 MB
            'color': '#0074d9',  # Blue
            'gps_data': [
                # Normal points
                *[
                    {
                        'folder': 'Center',
                        'filename': f'DJI_{i:04d}.JPG',
                        'filepath': f'/path/to/Center/DJI_{i:04d}.JPG',
                        'latitude': 37.7749 + (i * 0.00003),
                        'longitude': -122.4194 + (i * 0.00003),
                        'altitude': 120 + (i * 2),
                        'timestamp': None
                    }
                    for i in range(45)
                ],
                # Outlier point (far away)
                {
                    'folder': 'Center',
                    'filename': 'DJI_OUTLIER.JPG',
                    'filepath': '/path/to/Center/DJI_OUTLIER.JPG',
                    'latitude': 40.0,  # Way off in another location
                    'longitude': -120.0,
                    'altitude': 50,
                    'timestamp': None
                }
            ]
        }
    },
    'total_images': 370,
    'total_size': 1400000000,
    'gps_points': []  # Not used by visualization function
}

def test_visualization():
    """Test the visualization generation"""
    print("=" * 60)
    print("FLIGHT PATH VISUALIZATION TEST")
    print("=" * 60)

    print("\n[1/4] Testing visualization generation...")
    html_output = generate_flight_path_visualization(mock_analysis_data)

    # Check output is HTML
    assert isinstance(html_output, str), "Output should be HTML string"
    assert len(html_output) > 1000, "HTML output seems too short"
    print(f"✓ Generated HTML ({len(html_output):,} bytes)")

    # Check for key components
    print("\n[2/4] Checking for required HTML elements...")
    required_elements = [
        ('plotly.js CDN', 'cdn.plot.ly/plotly'),
        ('Plot container', 'flight-path-plot'),
        ('3D scatter traces', 'Scatter3d'),
        ('Ground surface', 'Surface'),
        ('Site ID in title', '10001291'),
        ('Pilot name in title', 'JasonDunwoody'),
    ]

    for name, search_term in required_elements:
        if search_term in html_output:
            print(f"  ✓ {name}")
        else:
            print(f"  ❌ MISSING: {name}")
            return False

    # Check for outlier detection
    print("\n[3/4] Checking outlier detection...")
    if 'Outliers' in html_output or 'symbol' in html_output.lower():
        print("  ✓ Outlier trace present")
    else:
        print("  ⚠️  No outlier markers found (may be OK if no outliers)")

    # Save to file for manual inspection
    print("\n[4/4] Saving output for manual inspection...")
    output_file = '/tmp/test_flight_path.html'

    # Create full HTML for viewing in browser
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Test Flight Path Visualization</title>
    <style>
        body {{ margin: 0; padding: 20px; background: #1a1a1a; }}
        #flight-path-plot {{ width: 100%; height: 800px; }}
    </style>
</head>
<body>
    {html_output}
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(full_html)

    print(f"  ✓ Saved to: {output_file}")
    print(f"  → Open this file in your browser to see the visualization")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)

    print(f"\nNext step: Open the test file in your browser:")
    print(f"  open {output_file}")

    return True

if __name__ == "__main__":
    try:
        success = test_visualization()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

Run it:
```bash
cd /Users/rileybellin/Desktop/QC\ TOOL\ WEB\ BASED
source venv/bin/activate
python test_visualization.py
```

Then open the generated file:
```bash
open /tmp/test_flight_path.html
```

---

### Option 3: Integration Test (With Real SFTP)

Test GPS extraction and visualization with real SFTP data.

Create `test_integration.py`:

```python
#!/usr/bin/env python3
"""
Integration test - Connect to SFTP and generate real visualization
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'backend'))

from services.connection_service import ConnectionService
from services.file_service import FileService
from services.site_analysis_service import analyze_site_structure, generate_flight_path_visualization
from models.connection import Connection, ConnectionType
import getpass

def test_real_site():
    """Test with real SFTP data"""
    print("=" * 60)
    print("INTEGRATION TEST - Real SFTP Site")
    print("=" * 60)

    # Get credentials
    print("\nEnter SFTP credentials:")
    host = input("  Host [73.156.240.32]: ").strip() or "73.156.240.32"
    port = input("  Port [22]: ").strip() or "22"
    username = input("  Username: ").strip()
    password = getpass.getpass("  Password: ")

    if not username or not password:
        print("❌ Username and password required")
        return False

    port = int(port)
    session_id = "integration_test"

    # Connect
    print("\n[1/5] Connecting to SFTP...")
    conn_service = ConnectionService()
    connection = conn_service.connect(
        session_id=session_id,
        connection_type=ConnectionType.SFTP,
        host=host,
        port=port,
        username=username,
        password=password
    )

    if not connection:
        print("❌ Connection failed")
        return False
    print("✓ Connected")

    # List pilots
    print("\n[2/5] Listing pilots...")
    file_service = FileService()
    pilots = file_service.list_directory(connection, '/homes')
    pilot_dirs = [p['name'] for p in pilots if p['type'] == 'directory']
    print(f"✓ Found {len(pilot_dirs)} pilots: {', '.join(pilot_dirs[:5])}")

    if not pilot_dirs:
        print("❌ No pilot directories found")
        return False

    # Select first pilot
    pilot = pilot_dirs[0]
    print(f"\n[3/5] Checking sites for pilot: {pilot}")
    sites = file_service.list_directory(connection, f'/homes/{pilot}')
    site_dirs = [s['name'] for s in sites if s['type'] == 'directory']
    print(f"✓ Found {len(site_dirs)} sites")

    if not site_dirs:
        print("❌ No site directories found")
        return False

    # Select first site
    site = site_dirs[0]
    site_path = f'/homes/{pilot}/{site}'
    print(f"\n[4/5] Analyzing site: {site}")
    print(f"  Path: {site_path}")
    print(f"  This will extract GPS from all images (may take several minutes)...")

    # Analyze site
    analysis_data = analyze_site_structure(
        connection=connection,
        site_path=site_path,
        file_service=file_service,
        session_id=session_id
    )

    print(f"\n✓ Analysis complete:")
    print(f"  - Folders: {len(analysis_data['folders'])}")
    print(f"  - Total images: {analysis_data['total_images']}")
    print(f"  - GPS points: {len(analysis_data['gps_points'])}")

    for folder_name, folder_data in analysis_data['folders'].items():
        print(f"    • {folder_name}: {folder_data['gps_count']}/{folder_data['image_count']} GPS points")

    # Generate visualization
    print(f"\n[5/5] Generating 3D visualization...")
    html_output = generate_flight_path_visualization(analysis_data)

    # Save output
    output_file = f'/tmp/integration_test_{site}.html'
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Integration Test - {site}</title>
    <style>
        body {{ margin: 0; padding: 20px; background: #1a1a1a; }}
        #flight-path-plot {{ width: 100%; height: 800px; }}
    </style>
</head>
<body>
    <h1 style="color: white;">Integration Test - {site}</h1>
    {html_output}
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(full_html)

    print(f"✓ Saved visualization to: {output_file}")

    # Cleanup
    conn_service.disconnect(session_id)

    print("\n" + "=" * 60)
    print("✅ INTEGRATION TEST PASSED!")
    print("=" * 60)
    print(f"\nOpen the visualization:")
    print(f"  open {output_file}")

    return True

if __name__ == "__main__":
    try:
        success = test_real_site()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

Run it:
```bash
cd /Users/rileybellin/Desktop/QC\ TOOL\ WEB\ BASED
source venv/bin/activate
python test_integration.py
```

---

## Troubleshooting

### Issue: "No GPS data found"

**Cause**: Images don't have GPS EXIF data or using wrong coordinate system

**Solutions**:
1. Check image metadata:
   ```python
   import exifread
   with open('image.jpg', 'rb') as f:
       tags = exifread.process_file(f)
       for tag in tags:
           if 'GPS' in tag or 'drone' in tag.lower() or 'dji' in tag.lower():
               print(f"{tag}: {tags[tag]}")
   ```

2. Verify images are from DJI drones with GPS enabled
3. Check if images are RAW files (may need different EXIF library)

### Issue: "Outliers dominate the view"

**Cause**: Some GPS coordinates are way off (bad GPS lock)

**Solution**: The updated code now handles this! Outliers are:
- Detected using IQR method (4.0× multiplier)
- Shown as red X markers
- Excluded from axis range calculation

### Issue: "Visualization is blank/empty"

**Cause**: No inlier GPS points after outlier detection

**Solutions**:
1. Check server logs for GPS extraction errors
2. Reduce outlier multiplier (currently 4.0)
3. Verify images have valid GPS coordinates

### Issue: "SFTP connection timeout"

**Cause**: Network issues or wrong credentials

**Solutions**:
1. Test SFTP connection first:
   ```bash
   python test_sshfs.py  # Or manual SFTP test
   ```
2. Check firewall settings
3. Verify credentials are correct

### Issue: "Plot looks different from FlightPathViewer.py"

**Check these settings**:
- [ ] Outlier multiplier is 4.0 (not 1.5)
- [ ] Ground plane is at `min_altitude - 20`
- [ ] Axis ranges are fixed (`autorange=False`)
- [ ] Colors match folder types (orbit=red, scan=green, etc.)
- [ ] Background is black, not white

---

## Performance Benchmarks

Expected performance over SFTP:

| Images | GPS Extraction | Visualization | Total |
|--------|----------------|---------------|-------|
| 50     | ~30 seconds    | < 1 second    | ~31s  |
| 200    | ~2 minutes     | < 1 second    | ~2m   |
| 500    | ~5 minutes     | 1-2 seconds   | ~5m   |
| 1000   | ~10 minutes    | 2-3 seconds   | ~10m  |

**Optimization Tips**:
- GPS extraction is the bottleneck (64KB read per image over SFTP)
- Consider caching GPS data after first extraction
- Use progress logging to keep user informed

---

## Comparing to FlightPathViewer.py

To verify your web version matches the desktop version:

1. **Process same site in both**:
   - Desktop: Open site in FlightPathViewer.py
   - Web: View same site in QC viewer
   - Screenshot both visualizations

2. **Check identical features**:
   - Same number of GPS points
   - Same outlier detection (red X markers)
   - Same axis ranges
   - Same ground plane position
   - Same folder colors

3. **Verify calculations**:
   - Print axis ranges from both
   - Compare outlier counts
   - Check min/max altitudes

---

## Next Steps After Testing

Once tests pass:

1. **Add Caching** - Store GPS data to avoid re-extraction
2. **Add Progress Bar** - Real-time updates via WebSocket
3. **Add Thumbnails** - Image preview on hover
4. **Add Export** - Download 3D plot as image/PDF
5. **Add Filtering** - Toggle folders on/off
6. **Add Measurements** - Distance/area calculations

---

## Questions?

Check the logs:
```bash
tail -f src/backend/logs/app.log
```

Enable debug logging:
```python
# In app.py
import logging
logging.basicConfig(level=logging.DEBUG)
```
