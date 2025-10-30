#!/usr/bin/env python3
"""
Debug visualization generation - check what's actually being produced
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'backend'))

from services.site_analysis_service import generate_flight_path_visualization

# Simulate real data structure from your logs
mock_analysis_data = {
    'site_info': {
        'site_id': '10069746',
        'pilot_name': 'Unknown',
        'full_path': '/homes/00 - QA Passed/01 - Ericsson/01 - AT&T/10069746'
    },
    'folders': {
        '10069746-10-28-2025- Overall': {
            'folder_name': '10069746-10-28-2025- Overall',
            'image_count': 5,
            'total_size': 5000000,
            'color': '#aaaaaa',  # default gray
            'gps_data': [
                {
                    'folder': '10069746-10-28-2025- Overall',
                    'filename': f'IMG_{i:04d}.JPG',
                    'filepath': f'/test/IMG_{i:04d}.JPG',
                    'latitude': 37.7749 + (i * 0.00001),
                    'longitude': -122.4194 + (i * 0.00001),
                    'altitude': 100 + (i * 10),
                    'timestamp': None
                }
                for i in range(5)
            ]
        },
        '10069746-10-28-2025-Cable Run': {
            'folder_name': '10069746-10-28-2025-Cable Run',
            'image_count': 52,
            'total_size': 52000000,
            'color': '#2ecc40',  # green (scan)
            'gps_data': [
                {
                    'folder': '10069746-10-28-2025-Cable Run',
                    'filename': f'IMG_{i:04d}.JPG',
                    'filepath': f'/test/IMG_{i:04d}.JPG',
                    'latitude': 37.7749 + (i * 0.00002),
                    'longitude': -122.4194 + (i * 0.00002),
                    'altitude': 120 + (i * 5),
                    'timestamp': None
                }
                for i in range(52)
            ]
        },
        '10069746-10-28-2025-Civil': {
            'folder_name': '10069746-10-28-2025-Civil',
            'image_count': 153,
            'total_size': 153000000,
            'color': '#ff851b',  # orange (civil)
            'gps_data': [
                {
                    'folder': '10069746-10-28-2025-Civil',
                    'filename': f'IMG_{i:04d}.JPG',
                    'filepath': f'/test/IMG_{i:04d}.JPG',
                    'latitude': 37.7749 + (i * 0.000005),
                    'longitude': -122.4194 + (i * 0.000005),
                    'altitude': 5 + (i * 0.5),  # Ground level
                    'timestamp': None
                }
                for i in range(153)
            ]
        },
        '10069746-10-29-2025-Tower-Scans': {
            'folder_name': '10069746-10-29-2025-Tower-Scans',
            'image_count': 513,
            'total_size': 513000000,
            'color': '#2ecc40',  # green (scan)
            'gps_data': [
                {
                    'folder': '10069746-10-29-2025-Tower-Scans',
                    'filename': f'IMG_{i:04d}.JPG',
                    'filepath': f'/test/IMG_{i:04d}.JPG',
                    'latitude': 37.7749 + (i * 0.00001),
                    'longitude': -122.4194 + (i * 0.00001),
                    'altitude': 150 + (i * 0.5),
                    'timestamp': None
                }
                for i in range(513)
            ]
        }
    },
    'total_images': 723,
    'total_size': 723000000,
    'gps_points': []
}

print("=" * 60)
print("DEBUG VISUALIZATION GENERATION")
print("=" * 60)

print("\n[1/5] Testing with mock data structure...")
print(f"  Total folders: {len(mock_analysis_data['folders'])}")
for fname, fdata in mock_analysis_data['folders'].items():
    print(f"    {fname}: {len(fdata['gps_data'])} GPS points, color={fdata['color']}")

print("\n[2/5] Generating visualization...")
html_output = generate_flight_path_visualization(mock_analysis_data)

print(f"\n[3/5] HTML generated: {len(html_output)} bytes")

print("\n[4/5] Checking HTML content...")
checks = [
    ('Plotly CDN', 'cdn.plot.ly' in html_output.lower()),
    ('Scatter3d traces', 'scatter3d' in html_output.lower()),
    ('Surface trace', 'surface' in html_output.lower()),
    ('Has data', '"data":[' in html_output.lower() or '"data": [' in html_output.lower()),
    ('Has layout', '"layout":' in html_output.lower() or '"layout": ' in html_output.lower()),
    ('Site ID', '10069746' in html_output),
]

for name, passed in checks:
    status = "✓" if passed else "❌"
    print(f"  {status} {name}")

print("\n[5/5] Extracting Plotly data...")
# Find the Plotly data section
import re

# Look for the data array
data_match = re.search(r'"data"\s*:\s*\[([^\]]+)\]', html_output, re.DOTALL)
if data_match:
    data_str = data_match.group(1)
    # Count traces
    trace_count = data_str.count('"type"')
    print(f"  Found {trace_count} traces in data")

    # Check for scatter3d
    scatter3d_count = data_str.lower().count('scatter3d')
    print(f"  Found {scatter3d_count} scatter3d traces")

    # Check for surface
    surface_count = data_str.lower().count('surface')
    print(f"  Found {surface_count} surface traces")
else:
    print("  ❌ Could not find data array in HTML!")
    print("\n  First 1000 chars of HTML:")
    print(html_output[:1000])

# Save for inspection
output_file = '/tmp/debug_viz.html'
full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Debug Visualization</title>
    <style>
        body {{ margin: 0; padding: 20px; background: #1a1a1a; }}
        #flight-path-plot {{ width: 100%; height: 800px; }}
    </style>
</head>
<body>
    <h1 style="color: white;">Debug Visualization Test</h1>
    {html_output}
</body>
</html>
"""

with open(output_file, 'w') as f:
    f.write(full_html)

print(f"\n✓ Saved to: {output_file}")
print(f"  Open with: open {output_file}")

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)
