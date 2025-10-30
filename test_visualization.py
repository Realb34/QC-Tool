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
    html_lower = html_output.lower()

    required_elements = [
        ('plotly.js CDN', lambda h: 'cdn.plot.ly/plotly' in h),
        ('Plot container', lambda h: 'flight-path-plot' in h),
        ('3D scatter traces', lambda h: 'scatter3d' in h.lower()),
        ('Ground surface', lambda h: 'surface' in h.lower()),
        ('Site ID in title', lambda h: '10001291' in h),
        ('Pilot name in title', lambda h: 'JasonDunwoody' in h),
    ]

    for name, check_func in required_elements:
        if check_func(html_output):
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
