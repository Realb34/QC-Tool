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
