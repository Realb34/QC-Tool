"""
Sites API
Handles site/directory browsing and selection
"""
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, session

from services.connection_service import connection_service
from services.file_service import file_service

logger = logging.getLogger(__name__)

sites_bp = Blueprint('sites', __name__)


def get_or_create_connection(session_id):
    """
    Get existing connection or create new one from session credentials.
    This handles multiple Gunicorn workers where connections aren't shared.
    """
    connection = connection_service.get_connection(session_id)
    if not connection:
        # Connection doesn't exist in this worker - reconnect using session credentials
        host = session.get('host')
        username = session.get('username')
        protocol = session.get('protocol')
        password = session.get('password')
        port = session.get('port')

        if not all([host, username, protocol, password, port]):
            return None

        logger.info(f"Reconnecting to {host} for session {session_id} (different worker)")
        connection = connection_service.connect(
            session_id=session_id,
            protocol=protocol,
            host=host,
            port=port,
            username=username,
            password=password
        )
    return connection


@sites_bp.route('/list', methods=['GET', 'POST'])
def list_sites():
    """
    List available sites (directories) at the root or specified path

    Query Parameters or JSON:
        path: Directory path to list (default: root)

    Returns:
        {
            "success": true,
            "path": "/",
            "items": [
                {
                    "name": "Site001",
                    "type": "directory",
                    "size": 0,
                    "modified": "2024-01-01T12:00:00"
                }
            ]
        }
    """
    try:
        # Get session
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'Not authenticated'}), 401

        connection = get_or_create_connection(session_id)
        if not connection:
            return jsonify({'error': 'Session expired. Please login again.'}), 401

        # Get path from query or JSON
        if request.method == 'POST':
            data = request.get_json() or {}
            path = data.get('path', '/')
        else:
            path = request.args.get('path', '/')

        # List directory
        items = file_service.list_directory(connection, path)

        # Filter to only show directories if at root level
        if path in ['/', '.', '']:
            items = [item for item in items if item['type'] == 'directory']

        logger.info(f"Listed {len(items)} items in {path}")

        return jsonify({
            'success': True,
            'path': path,
            'items': items,
            'count': len(items)
        }), 200

    except TimeoutError as e:
        logger.error(f"Listing timed out: {e}")
        return jsonify({'error': 'Directory listing timed out. Please try again.'}), 504
    except Exception as e:
        logger.error(f"Failed to list sites: {e}")
        if 'timeout' in str(e).lower() or 'timed out' in str(e).lower():
            return jsonify({'error': 'Connection timed out. Please check your network and try again.'}), 504
        return jsonify({'error': f'Failed to list sites: {str(e)}'}), 500


@sites_bp.route('/select', methods=['POST'])
def select_site():
    """
    Select a site for viewing

    Request JSON:
        {
            "site_name": "Site001",
            "site_path": "/Site001"
        }

    Returns:
        {
            "success": true,
            "site": {
                "name": "Site001",
                "path": "/Site001"
            }
        }
    """
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'Not authenticated'}), 401

        connection = get_or_create_connection(session_id)
        if not connection:
            return jsonify({'error': 'Session expired'}), 401

        data = request.get_json()
        site_name = data.get('site_name')
        site_path = data.get('site_path')

        if not site_name or not site_path:
            return jsonify({'error': 'Site name and path required'}), 400

        # Verify site exists and is accessible
        try:
            file_service.change_directory(connection, site_path)
        except Exception as e:
            return jsonify({'error': f'Cannot access site: {str(e)}'}), 400

        # Store selected site in session
        session['selected_site'] = site_name
        session['selected_site_path'] = site_path

        logger.info(f"Site selected: {site_name} at {site_path}")

        return jsonify({
            'success': True,
            'site': {
                'name': site_name,
                'path': site_path
            }
        }), 200

    except Exception as e:
        logger.error(f"Failed to select site: {e}")
        return jsonify({'error': f'Failed to select site: {str(e)}'}), 500


@sites_bp.route('/current', methods=['GET'])
def current_site():
    """
    Get currently selected site

    Returns:
        {
            "site": {
                "name": "Site001",
                "path": "/Site001"
            }
        }
    """
    site_name = session.get('selected_site')
    site_path = session.get('selected_site_path')

    if not site_name or not site_path:
        return jsonify({'site': None}), 200

    return jsonify({
        'site': {
            'name': site_name,
            'path': site_path
        }
    }), 200


@sites_bp.route('/analyze', methods=['POST'])
def analyze_site():
    """
    Analyze site structure and generate flight path visualization.
    This extracts GPS data from images and generates a 3D Plotly visualization.

    Request JSON:
        {
            "site_path": "/homes/PilotName/SiteID-Date"
        }

    Returns:
        {
            "success": true,
            "site_info": {
                "pilot_name": "PilotName",
                "site_id": "12345678",
                "full_path": "/homes/PilotName/SiteID-Date"
            },
            "folders": {...},
            "total_images": 150,
            "total_size": 1024000,
            "visualization_html": "<div>...</div>"
        }
    """
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'Not authenticated'}), 401

        connection = get_or_create_connection(session_id)
        if not connection:
            return jsonify({'error': 'Session expired'}), 401

        data = request.get_json()
        site_path = data.get('site_path') or session.get('selected_site_path')

        if not site_path:
            return jsonify({'error': 'Site path required'}), 400

        # Import site analysis service
        from services.site_analysis_service import analyze_site_structure, generate_flight_path_visualization

        # Analyze site structure (now generates thumbnails!)
        logger.info(f"Starting site analysis for: {site_path}")
        analysis_data = analyze_site_structure(connection, site_path, file_service, session_id)

        # Generate visualization
        visualization_html = generate_flight_path_visualization(analysis_data)

        # Store analysis in session for quick retrieval
        session['site_analysis'] = {
            'timestamp': datetime.now().isoformat(),
            'site_path': site_path
        }

        logger.info(f"Site analysis complete: {analysis_data['total_images']} images, {len(analysis_data['folders'])} folders")

        return jsonify({
            'success': True,
            'site_info': analysis_data['site_info'],
            'folders': {
                name: {
                    'folder_name': folder['folder_name'],
                    'image_count': folder['image_count'],
                    'total_size': folder['total_size'],
                    'color': folder['color'],
                    'gps_count': len(folder['gps_data']),
                    'sample_images': folder['sample_images']  # Include sample images for carousel
                }
                for name, folder in analysis_data['folders'].items()
            },
            'total_images': analysis_data['total_images'],
            'total_size': analysis_data['total_size'],
            'gps_point_count': len(analysis_data['gps_points']),
            'visualization_html': visualization_html
        }), 200

    except TimeoutError as e:
        logger.error(f"Site analysis timed out: {e}", exc_info=True)
        return jsonify({'error': 'Site analysis timed out. The server may be slow or the site is very large. Please try again.'}), 504
    except Exception as e:
        logger.error(f"Failed to analyze site: {e}", exc_info=True)
        # Check if it's a socket timeout
        if 'timeout' in str(e).lower() or 'timed out' in str(e).lower():
            return jsonify({'error': 'Connection timed out. Please check your network and try again.'}), 504
        return jsonify({'error': f'Failed to analyze site: {str(e)}'}), 500
