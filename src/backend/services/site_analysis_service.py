"""
Site Analysis Service
Handles GPS extraction, folder analysis, and flight path visualization
"""
import os
import re
import io
import logging
import tempfile
import hashlib
from collections import defaultdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from queue import Queue

import numpy as np
import plotly.graph_objects as go
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import exifread

from models.connection import ConnectionType

logger = logging.getLogger(__name__)

# Thumbnail cache directory - matches FlightPathViewer approach
THUMBNAIL_CACHE_DIR = os.path.join(tempfile.gettempdir(), "qc_tool_thumbnails")
os.makedirs(THUMBNAIL_CACHE_DIR, exist_ok=True)

logger.info(f"Thumbnail cache directory: {THUMBNAIL_CACHE_DIR}")

# Global connection pool cache - reuse across folders for same session
_connection_pool_cache = {}
_pool_cache_lock = Lock()


def create_connection_pool(session_connection, pool_size=3):
    """
    Create a pool of SFTP connections from session credentials.
    Each thread will get its own connection to avoid "Garbage packet" errors.

    Args:
        session_connection: The main session SFTP connection
        pool_size: Number of connections to create

    Returns:
        Queue of connection objects
    """
    from services.connection_service import ConnectionService

    pool = Queue()
    conn_service = ConnectionService()

    # Get credentials from existing connection
    host = session_connection.host
    port = session_connection.port
    username = session_connection.username

    # We need to get the password from Flask session
    from flask import session as flask_session
    password = flask_session.get('password')

    if not password:
        logger.warning("No password in session, cannot create connection pool")
        return pool

    try:
        for i in range(pool_size):
            # Create new SSH client
            import paramiko
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh_client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )

            sftp_client = ssh_client.open_sftp()

            # Create a minimal connection object
            from models.connection import Connection, ConnectionType
            conn = Connection(
                session_id=f"pool_{i}",
                connection_type=ConnectionType.SFTP,
                host=host,
                port=port,
                username=username,
                client=sftp_client
            )
            conn._ssh_client = ssh_client  # Store SSH client for cleanup

            pool.put(conn)
            logger.debug(f"Created pool connection {i+1}/{pool_size}")

        logger.info(f"Created SFTP connection pool with {pool_size} connections")

    except Exception as e:
        logger.error(f"Failed to create connection pool: {e}")

    return pool


def cleanup_connection_pool(pool):
    """Close all connections in the pool"""
    while not pool.empty():
        try:
            conn = pool.get_nowait()
            if hasattr(conn, '_ssh_client'):
                conn._ssh_client.close()
            conn.client.close()
        except Exception as e:
            logger.error(f"Error closing pool connection: {e}")


def generate_thumbnail_from_sftp(connection, file_path, session_id, file_service, size=(200, 200)):
    """
    Generate thumbnail from SFTP file and cache locally (FlightPathViewer.py line 1848-1867).
    Returns the thumbnail filename that can be served statically.
    """
    try:
        # Create unique filename using hash of path
        path_hash = hashlib.md5(file_path.encode()).hexdigest()
        thumb_filename = f"{session_id}_{path_hash}.jpg"
        thumb_path = os.path.join(THUMBNAIL_CACHE_DIR, thumb_filename)

        # Return cached thumbnail if it exists
        if os.path.exists(thumb_path):
            logger.debug(f"Using cached thumbnail: {thumb_filename}")
            return thumb_filename

        # Download partial file (first 512KB - enough for good thumbnail)
        logger.debug(f"Generating thumbnail for: {file_path}")
        file_buffer = file_service.read_file_partial(connection, file_path, max_bytes=512 * 1024)

        # Generate thumbnail using Pillow (same as FlightPathViewer)
        with Image.open(file_buffer) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(thumb_path, "JPEG", quality=85)

        logger.info(f"Created thumbnail: {thumb_filename}")
        return thumb_filename

    except Exception as e:
        logger.error(f"Thumbnail generation failed for {file_path}: {e}")
        return None


# Color mapping for different folder types (matching FlightPathViewer)
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


def parse_site_path(path):
    """
    Parse site path to extract pilot name and site ID.
    Expected format: /homes/PilotName/SiteID-Date-Client
    Example: /homes/JasonDunwoody/10001291-08-20-2025-ATT

    Returns:
        dict: {
            'pilot_name': str,
            'site_id': str,
            'full_path': str
        }
    """
    try:
        parts = path.strip('/').split('/')

        pilot_name = None
        site_id = None

        # Look for 'homes' and extract pilot name
        if 'homes' in parts:
            homes_idx = parts.index('homes')
            if len(parts) > homes_idx + 1:
                pilot_name = parts[homes_idx + 1]

        # Extract site ID (8-10 digit number)
        for part in parts:
            match = re.search(r'(\d{8,10})', part)
            if match:
                site_id = match.group(1)
                break

        return {
            'pilot_name': pilot_name or 'Unknown',
            'site_id': site_id or 'Unknown',
            'full_path': path
        }
    except Exception as e:
        logger.error(f"Error parsing site path {path}: {e}")
        return {
            'pilot_name': 'Unknown',
            'site_id': 'Unknown',
            'full_path': path
        }


def extract_gps_from_exif(image_bytes):
    """
    Extract GPS coordinates and altitude from image EXIF data using exifread.
    Matches FlightPathViewer.py lines 1869-1903 exactly.

    Returns:
        dict: {
            'latitude': float,
            'longitude': float,
            'altitude': float (feet above ground level),
            'timestamp': datetime or None
        } or None if no GPS data
    """
    try:
        # Use exifread library (same as FlightPathViewer)
        fh = io.BytesIO(image_bytes)
        tags = exifread.process_file(fh, details=False)

        # Try DJI RelativeAltitude first (preferred for drones)
        rel_alt_tag = tags.get('Xmp.drone-dji.RelativeAltitude') or tags.get('Xmp.DJI.RelativeAltitude')
        if rel_alt_tag:
            agl_ft = float(str(rel_alt_tag)) * 3.28084  # meters to feet
        else:
            # Fall back to GPS Altitude
            alt_tag = tags.get('GPS GPSAltitude')
            if not alt_tag:
                # No altitude - still try to get lat/lon
                agl_ft = 0
            else:
                # Convert GPS altitude to feet
                agl_ft = (alt_tag.values[0].num / alt_tag.values[0].den) * 3.28084

        # Get latitude and longitude
        lat_tag = tags.get('GPS GPSLatitude')
        lon_tag = tags.get('GPS GPSLongitude')
        lat_ref = tags.get('GPS GPSLatitudeRef')
        lon_ref = tags.get('GPS GPSLongitudeRef')

        if not all([lat_tag, lon_tag, lat_ref, lon_ref]):
            return None

        # Convert coordinates (exact FlightPathViewer implementation)
        def _conv(coord):
            d = coord.values[0].num / coord.values[0].den
            m = coord.values[1].num / (coord.values[1].den * 60)
            s = coord.values[2].num / (coord.values[2].den * 3600)
            return d + m + s

        lat = _conv(lat_tag) * (-1 if lat_ref.printable != 'N' else 1)
        lon = _conv(lon_tag) * (-1 if lon_ref.printable != 'E' else 1)

        return {
            'latitude': lat,
            'longitude': lon,
            'altitude': agl_ft,
            'timestamp': None
        }

    except Exception as e:
        logger.debug(f"EXIF read error: {e}")
        return None


def determine_folder_color(folder_name):
    """
    Determine color for folder based on name (orbit, scan, etc.)
    """
    folder_lower = folder_name.lower()

    for key, color in FOLDER_COLORS.items():
        if key in folder_lower:
            return color

    return FOLDER_COLORS['default']


def analyze_site_structure(connection, site_path, file_service, session_id):
    """
    Analyze site folder structure and extract GPS data from all images.
    Now generates thumbnails for fast carousel loading (FlightPathViewer approach).

    Returns:
        dict: {
            'site_info': dict,
            'folders': dict,  # folder_name -> {images: int, size: int, color: str, gps_data: list}
            'total_images': int,
            'total_size': int,
            'gps_points': list  # All GPS points for visualization
        }
    """
    try:
        logger.info(f"Analyzing site structure: {site_path} (session: {session_id})")

        # Parse site path
        site_info = parse_site_path(site_path)

        # Get all items in site directory
        items = file_service.list_directory(connection, site_path)

        folders = {}
        total_images = 0
        total_size = 0
        all_gps_points = []
        failed_folders = []

        # Process each folder with timeout protection and error recovery
        for item in items:
            if item['type'] == 'directory':
                folder_name = item['name']
                folder_path = f"{site_path}/{folder_name}".replace('//', '/')

                logger.info(f"Analyzing folder: {folder_name}")

                try:
                    # Validate main connection is still alive before processing folder
                    if connection.connection_type == ConnectionType.SFTP:
                        if hasattr(connection.client, 'get_channel') and connection.client.get_channel():
                            connection.client.get_channel().settimeout(30.0)
                            # Quick health check - try to stat the folder
                            connection.client.stat(folder_path)

                    # Analyze folder contents with timeout protection
                    folder_result = analyze_folder(connection, folder_path, folder_name, file_service, session_id)

                    folders[folder_name] = folder_result
                    total_images += folder_result['image_count']
                    total_size += folder_result['total_size']
                    all_gps_points.extend(folder_result['gps_data'])

                except Exception as e:
                    logger.error(f"Failed to analyze folder {folder_name}: {e}", exc_info=True)
                    failed_folders.append(folder_name)
                    # Create empty folder result to continue processing
                    folders[folder_name] = {
                        'folder_name': folder_name,
                        'folder_path': folder_path,
                        'image_count': 0,
                        'total_size': 0,
                        'color': determine_folder_color(folder_name),
                        'gps_data': [],
                        'gps_count': 0,
                        'sample_images': [],
                        'error': str(e)
                    }

        if failed_folders:
            logger.warning(f"Failed to process {len(failed_folders)} folders: {', '.join(failed_folders)}")

        logger.info(f"Analysis complete: {len(folders)} folders, {total_images} images, {len(all_gps_points)} GPS points")

        # Cleanup: Close cached connections after site analysis completes
        _cleanup_connection_pool_for_session(session_id)

        return {
            'site_info': site_info,
            'folders': folders,
            'total_images': total_images,
            'total_size': total_size,
            'gps_points': all_gps_points
        }

    except Exception as e:
        logger.error(f"Error analyzing site structure: {e}", exc_info=True)
        # Cleanup on error too
        _cleanup_connection_pool_for_session(session_id)
        raise


def _cleanup_connection_pool_for_session(session_id):
    """Close all cached connections for a session"""
    with _pool_cache_lock:
        keys_to_remove = [key for key in _connection_pool_cache.keys() if key.startswith(session_id)]
        for key in keys_to_remove:
            pool = _connection_pool_cache.pop(key, [])
            for ssh, sftp in pool:
                try:
                    sftp.close()
                    ssh.close()
                except:
                    pass
            if pool:
                logger.info(f"🧹 Closed {len(pool)} cached connections for session")


def analyze_folder_sequential(connection, folder_path, folder_name, file_service, session_id, image_files, total_size, image_count):
    """Fallback sequential processing if connection pool fails"""
    sample_size = min(image_count, 10)
    gps_data = []
    sample_images = []

    for i, image_file in enumerate(image_files[:sample_size]):
        try:
            image_path = f"{folder_path}/{image_file['name']}".replace('//', '/')
            image_bytes = file_service.read_file_partial(connection, image_path, max_bytes=65536).read()
            gps = extract_gps_from_exif(image_bytes)

            thumbnail_filename = generate_thumbnail_from_sftp(connection, image_path, session_id, file_service)

            if gps:
                gps_data.append({
                    'folder': folder_name,
                    'filename': image_file['name'],
                    'filepath': image_path,
                    'latitude': gps['latitude'],
                    'longitude': gps['longitude'],
                    'altitude': gps['altitude'],
                    'timestamp': gps['timestamp']
                })

            sample_images.append({
                'name': image_file['name'],
                'path': image_path,
                'thumbnail': thumbnail_filename
            })
        except Exception as e:
            logger.error(f"Error processing {image_file['name']}: {e}")

    return {
        'folder_name': folder_name,
        'folder_path': folder_path,
        'image_count': image_count,
        'total_size': total_size,
        'color': determine_folder_color(folder_name),
        'gps_data': gps_data,
        'sample_images': sample_images
    }


def analyze_folder(connection, folder_path, folder_name, file_service, session_id):
    """
    Analyze folder - Extract GPS from ALL images using parallel processing.
    Uses connection pooling (similar to FlightPathViewer.py:2031-2052) for 3-4x speed improvement.
    """
    try:
        items = file_service.list_directory(connection, folder_path)

        image_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.dng'}
        image_files = [item for item in items if item['type'] == 'file' and
                      os.path.splitext(item['name'])[1].lower() in image_extensions]

        total_size = sum(item.get('size', 0) for item in items if item['type'] == 'file')
        image_count = len(image_files)

        logger.info(f"📍 Extracting GPS from ALL {image_count} images in {folder_name}")

        # Use parallel processing for all folders with 5+ images (very low threshold)
        if image_count >= 5:
            gps_data = _extract_gps_parallel(
                connection, folder_path, folder_name, image_files, file_service, session_id
            )
        else:
            # Sequential only for tiny folders (1-4 images)
            gps_data = _extract_gps_sequential(
                connection, folder_path, folder_name, image_files, file_service
            )

        logger.info(f"📊 Extracted {len(gps_data)}/{image_count} GPS points from {folder_name}")

        return {
            'folder_name': folder_name,
            'folder_path': folder_path,
            'image_count': image_count,
            'total_size': total_size,
            'color': determine_folder_color(folder_name),
            'gps_data': gps_data,
            'gps_count': len(gps_data),
            'sample_images': []
        }

    except Exception as e:
        logger.error(f"Error analyzing folder {folder_name}: {e}")
        return {
            'folder_name': folder_name,
            'folder_path': folder_path,
            'image_count': 0,
            'total_size': 0,
            'color': FOLDER_COLORS['default'],
            'gps_data': [],
            'gps_count': 0,
            'sample_images': []
        }


def _extract_gps_sequential(connection, folder_path, folder_name, image_files, file_service):
    """Sequential GPS extraction (fallback for small folders)"""
    gps_data = []
    image_count = len(image_files)
    for i, image_file in enumerate(image_files):
        try:
            image_path = f"{folder_path}/{image_file['name']}".replace('//', '/')
            image_bytes = file_service.read_file_partial(connection, image_path, max_bytes=65536).read()
            gps = extract_gps_from_exif(image_bytes)

            if gps:
                gps_data.append({
                    'folder': folder_name,
                    'filename': image_file['name'],
                    'filepath': image_path,
                    'latitude': gps['latitude'],
                    'longitude': gps['longitude'],
                    'altitude': gps['altitude'],
                    'timestamp': gps['timestamp']
                })

            if (i + 1) % 20 == 0 or (i + 1) == image_count:
                logger.info(f"  Progress: {i + 1}/{image_count} images processed, {len(gps_data)} GPS points found")
        except Exception as e:
            logger.debug(f"  ✗ Error: {image_file['name']}: {e}")
    return gps_data


def _extract_gps_parallel(connection, folder_path, folder_name, image_files, file_service, session_id):
    """
    Parallel GPS extraction using connection pool (FlightPathViewer.py approach).
    Creates multiple SFTP connections for concurrent processing.
    ~3-4x faster than sequential for large folders.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from flask import session as flask_session
    import paramiko

    gps_data = []
    image_count = len(image_files)

    # Create connection pool (50 workers for MAXIMUM parallelism)
    # Scale aggressively: use 1 worker per 5 images, minimum 10, maximum 50
    num_workers = min(50, max(10, image_count // 5))
    logger.info(f"  🚀 Using {num_workers} parallel workers for MAXIMUM speed")

    # Get credentials from main connection
    host = connection.host
    port = connection.port
    username = connection.username
    password = flask_session.get('password')

    if not password:
        logger.warning("No password in session, falling back to sequential")
        return _extract_gps_sequential(connection, folder_path, folder_name, image_files, file_service)

    # Check for cached connection pool for this session
    pool_key = f"{session_id}_{host}_{port}_{username}"
    connection_pool = []

    with _pool_cache_lock:
        if pool_key in _connection_pool_cache:
            cached_pool = _connection_pool_cache[pool_key]
            # Verify cached connections are still alive
            for ssh, sftp in cached_pool:
                try:
                    # Quick health check
                    sftp.stat('/')
                    connection_pool.append((ssh, sftp))
                except:
                    # Connection dead, remove it
                    try:
                        sftp.close()
                        ssh.close()
                    except:
                        pass

            if len(connection_pool) >= num_workers:
                logger.info(f"  ♻️  Reusing {len(connection_pool)} cached connections (saved ~{num_workers * 0.4}s)")
            elif len(connection_pool) > 0:
                logger.info(f"  ♻️  Reusing {len(connection_pool)} cached connections, creating {num_workers - len(connection_pool)} more")

    # Create new connections if needed
    try:
        for i in range(len(connection_pool), num_workers):
            try:
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=30,
                    allow_agent=False,
                    look_for_keys=False,
                    compress=True  # Enable SSH compression for faster transfers
                )
                sftp_client = ssh_client.open_sftp()
                # Set timeout on the underlying channel to prevent hangs
                sftp_client.get_channel().settimeout(30.0)
                connection_pool.append((ssh_client, sftp_client))
                logger.debug(f"    Created pool connection {i+1}/{num_workers}")
            except Exception as e:
                logger.error(f"Failed to create pool connection {i+1}: {e}")
                break

        if len(connection_pool) < 5:
            # Not enough connections for effective parallelism, fall back to sequential
            logger.warning(f"Connection pool too small ({len(connection_pool)} connections), using sequential")
            for ssh, sftp in connection_pool:
                try:
                    sftp.close()
                    ssh.close()
                except:
                    pass
            return _extract_gps_sequential(connection, folder_path, folder_name, image_files, file_service)

        logger.info(f"  ✓ Connection pool ready ({len(connection_pool)} connections)")

        # Create a queue for thread-safe connection management
        from queue import Queue
        connection_queue = Queue()
        for conn in connection_pool:
            connection_queue.put(conn)

        # Process images in parallel with thread-safe connection borrowing
        def process_image(image_file):
            """Process single image - borrows SFTP connection from pool"""
            import socket
            sftp_client = None
            ssh_client = None
            try:
                # Borrow a connection from the pool
                ssh_client, sftp_client = connection_queue.get(timeout=60)

                image_path = f"{folder_path}/{image_file['name']}".replace('//', '/')

                # Read EXIF data (first 32KB - enough for GPS EXIF which is in first ~8KB)
                # Reduced from 64KB for 2x faster network transfer
                with sftp_client.open(image_path, 'r') as f:
                    image_bytes = f.read(32768)

                gps = extract_gps_from_exif(image_bytes)

                if gps:
                    return {
                        'folder': folder_name,
                        'filename': image_file['name'],
                        'filepath': image_path,
                        'latitude': gps['latitude'],
                        'longitude': gps['longitude'],
                        'altitude': gps['altitude'],
                        'timestamp': gps['timestamp']
                    }
            except socket.timeout:
                logger.warning(f"  ⏱ Socket timeout: {image_file['name']}")
            except EOFError:
                logger.warning(f"  ⚠ Connection closed: {image_file['name']}")
            except Exception as e:
                logger.debug(f"  ✗ Error: {image_file['name']}: {e}")
            finally:
                # Return connection to pool
                if ssh_client and sftp_client:
                    connection_queue.put((ssh_client, sftp_client))
            return None

        # Submit tasks - connections are borrowed dynamically
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {}
            for image_file in image_files:
                future = executor.submit(process_image, image_file)
                futures[future] = image_file['name']

            # Collect results as they complete (with timeout)
            completed = 0
            for future in as_completed(futures, timeout=300):  # 5 minute timeout per batch
                completed += 1
                try:
                    result = future.result(timeout=30)  # 30 second timeout per image
                    if result:
                        gps_data.append(result)
                except TimeoutError:
                    filename = futures[future]
                    logger.warning(f"  ⏱ Timeout processing: {filename}")
                except Exception as e:
                    filename = futures[future]
                    logger.error(f"  ✗ Error processing {filename}: {e}")

                # Log progress every 20 images
                if completed % 20 == 0 or completed == image_count:
                    logger.info(f"  Progress: {completed}/{image_count} images processed, {len(gps_data)} GPS points found")

    finally:
        # Cache connections for reuse instead of closing them
        with _pool_cache_lock:
            _connection_pool_cache[pool_key] = connection_pool
        logger.debug(f"  💾 Cached {len(connection_pool)} connections for next folder")

    return gps_data


def format_size_bytes(bytes_val):
    """Format bytes to human readable string (matching FlightPathViewer.py:3036-3042)"""
    if bytes_val == 0:
        return "0 B"
    k = 1024
    sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    i = int(np.floor(np.log(bytes_val) / np.log(k)))
    return f"{round(bytes_val / np.power(k, i), 2)} {sizes[i]}"


def generate_flight_path_visualization(analysis_data):
    """
    Generate Plotly 3D flight path visualization HTML.
    Matches FlightPathViewer.py plot_3d_flight_path() logic exactly (lines 2931-3091):
    - Outlier detection using IQR method (4.0 multiplier for geographic data)
    - Separate inlier/outlier traces
    - Ground plane based on inlier data only
    - Fixed axis ranges (no autorange)
    - Dark theme with specific styling

    Returns:
        str: HTML string containing the interactive 3D plot
    """
    try:
        folders = analysis_data['folders']
        site_info = analysis_data['site_info']

        fig = go.Figure()

        # --- Step 1: Outlier Detection (FlightPathViewer.py:2956-3001) ---
        # Collect all coordinates (excluding civil/road folders)
        all_lats, all_lons, all_agls = [], [], []
        for folder_name, folder_data in folders.items():
            if 'civil' in folder_name.lower() or 'road' in folder_name.lower():
                continue

            for point in folder_data['gps_data']:
                all_lats.append(point['latitude'])
                all_lons.append(point['longitude'])
                all_agls.append(max(point['altitude'], 0))

        # Calculate IQR bounds for outlier detection
        outlier_folders = set()
        bounds = {}
        if all_lats and all_lons:
            lats_arr = np.array(all_lats)
            lons_arr = np.array(all_lons)
            q1_lat, q3_lat = np.percentile(lats_arr, [25, 75])
            q1_lon, q3_lon = np.percentile(lons_arr, [25, 75])
            iqr_lat = q3_lat - q1_lat
            iqr_lon = q3_lon - q1_lon

            # Use 4.0 multiplier for geographic data (FlightPathViewer.py:2975)
            multiplier = 4.0
            bounds = {
                'lat_low': q1_lat - multiplier * iqr_lat,
                'lat_high': q3_lat + multiplier * iqr_lat,
                'lon_low': q1_lon - multiplier * iqr_lon,
                'lon_high': q3_lon + multiplier * iqr_lon
            }

        # Separate inliers and outliers
        inlier_lats, inlier_lons, inlier_agls = [], [], []
        processed_data = defaultdict(lambda: {'inliers': [], 'outliers': []})

        for folder_name, folder_data in folders.items():
            for point in folder_data['gps_data']:
                lat = point['latitude']
                lon = point['longitude']
                agl = max(point['altitude'], 0)

                is_outlier = False
                if bounds:
                    if not (bounds['lat_low'] <= lat <= bounds['lat_high'] and
                            bounds['lon_low'] <= lon <= bounds['lon_high']):
                        is_outlier = True

                if is_outlier:
                    processed_data[folder_name]['outliers'].append(point)
                    outlier_folders.add(folder_name.lower())
                else:
                    processed_data[folder_name]['inliers'].append(point)
                    if 'civil' not in folder_name.lower() and 'road' not in folder_name.lower():
                        inlier_lats.append(lat)
                        inlier_lons.append(lon)
                        inlier_agls.append(agl)

        if not inlier_lats:
            return "<div style='padding:20px;text-align:center;'>No GPS data found in images</div>"

        # --- Step 2: Axis Range Calculation (based on inliers only, FlightPathViewer.py:3003-3009) ---
        lat_min, lat_max = min(inlier_lats), max(inlier_lats)
        lon_min, lon_max = min(inlier_lons), max(inlier_lons)
        data_max = max(inlier_agls)
        z_max = max(data_max, 100)
        z_min_rel = min(inlier_agls)
        ground_z = z_min_rel - 20

        # --- Step 3: Add Ground Plane (FlightPathViewer.py:3011-3020) ---
        if inlier_lats and inlier_lons and z_max > ground_z:
            nx = ny = 20
            xs = np.linspace(lon_min, lon_max, nx)
            ys = np.linspace(lat_min, lat_max, ny)
            x_mesh, y_mesh = np.meshgrid(xs, ys)
            z_mesh = np.full_like(x_mesh, ground_z)

            fig.add_trace(go.Surface(
                x=x_mesh,
                y=y_mesh,
                z=z_mesh,
                colorscale=[[0, '#002200'], [1, '#002200']],
                showscale=False,
                opacity=1.0,
                hoverinfo='skip',
                name='Ground'
            ))

        # --- Step 4: Add Data Traces (FlightPathViewer.py:3022-3073) ---
        for folder_name, folder_data in folders.items():
            folder_lower = folder_name.lower()

            # Skip civil/road folders (FlightPathViewer.py:3027-3028)
            if 'civil' in folder_lower or 'road' in folder_lower:
                continue

            inliers = processed_data[folder_name]['inliers']
            outliers = processed_data[folder_name]['outliers']

            base_color = folder_data['color']
            file_count = folder_data['image_count']
            size_bytes = folder_data['total_size']

            # Format legend name (FlightPathViewer.py:3044-3045)
            size_str = format_size_bytes(size_bytes)
            legend_name = f"{folder_name} ({size_str} - {file_count} files)"

            # Add inlier trace (FlightPathViewer.py:3047-3059)
            if inliers:
                lats = [p['latitude'] for p in inliers]
                lons = [p['longitude'] for p in inliers]
                agls = [p['altitude'] for p in inliers]
                basenames = [p['filename'] for p in inliers]

                fig.add_trace(go.Scatter3d(
                    x=lons,
                    y=lats,
                    z=agls,
                    mode='markers',
                    marker=dict(size=6, color=base_color, opacity=0.95),
                    name=legend_name,
                    hovertemplate="%{text}<extra></extra>",
                    text=basenames,
                    showlegend=True,
                    legendgroup=folder_name
                ))

            # Add outlier trace (FlightPathViewer.py:3061-3073)
            if outliers:
                lats = [p['latitude'] for p in outliers]
                lons = [p['longitude'] for p in outliers]
                agls = [p['altitude'] for p in outliers]
                basenames = [p['filename'] for p in outliers]

                fig.add_trace(go.Scatter3d(
                    x=lons,
                    y=lats,
                    z=agls,
                    mode='markers',
                    marker=dict(size=8, color='red', symbol='x', line=dict(width=2)),
                    name=f"{folder_name} (Outliers)",
                    hovertemplate="%{text}<extra>(OUTLIER)</extra>",
                    text=basenames,
                    showlegend=False,
                    legendgroup=folder_name
                ))

        # --- Step 5: Layout Configuration (FlightPathViewer.py:3076-3089) ---
        fig.update_layout(
            title=dict(
                text=f"Site {site_info['site_id']} - Pilot: {site_info['pilot_name']}",
                x=0.12,
                xanchor='left',
                font=dict(size=20, color='#e0e0e0')
            ),
            scene=dict(
                xaxis=dict(
                    title='Longitude',
                    gridcolor='gray',
                    zerolinecolor='gray',
                    tickfont=dict(color='#e0e0e0'),
                    autorange=False,
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
                bgcolor="rgba(0,0,0,0)"
            ),
            height=800
        )

        # Generate HTML - DON'T include Plotly.js (already in page header)
        # Use include_plotlyjs=False because qc_viewer.html already includes it
        html = fig.to_html(
            full_html=False,
            include_plotlyjs=False,  # CRITICAL: Page already has Plotly.js loaded
            config={'scrollZoom': True, 'displayModeBar': True, 'responsive': True},
            div_id='flight-path-plot'
        )

        logger.info(f"✓ Generated visualization: {len(inlier_lats)} inliers, {len(all_lats) - len(inlier_lats)} outliers")

        return html

    except Exception as e:
        logger.error(f"Error generating visualization: {e}", exc_info=True)
        return f"<div style='padding:20px;color:red;'>Error generating visualization: {str(e)}</div>"
