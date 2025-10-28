"""
Sites API
Handles site/directory browsing and selection
"""
import logging
from flask import Blueprint, request, jsonify, session

from services.connection_service import connection_service
from services.file_service import file_service

logger = logging.getLogger(__name__)

sites_bp = Blueprint('sites', __name__)


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

        connection = connection_service.get_connection(session_id)
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

    except Exception as e:
        logger.error(f"Failed to list sites: {e}")
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

        connection = connection_service.get_connection(session_id)
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
