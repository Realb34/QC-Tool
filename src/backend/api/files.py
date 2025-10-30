"""
Files API
Handles file browsing, viewing, and downloading
"""
import logging
import os
from flask import Blueprint, request, jsonify, session, send_file

from services.connection_service import connection_service
from services.file_service import file_service

logger = logging.getLogger(__name__)

files_bp = Blueprint('files', __name__)


@files_bp.route('/browse', methods=['GET', 'POST'])
def browse():
    """
    Browse files in the current or specified directory

    Query Parameters or JSON:
        path: Directory path to browse

    Returns:
        {
            "success": true,
            "path": "/Site001/Images",
            "items": [...]
        }
    """
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'Not authenticated'}), 401

        connection = connection_service.get_connection(session_id)
        if not connection:
            return jsonify({'error': 'Session expired'}), 401

        # Get path
        if request.method == 'POST':
            data = request.get_json() or {}
            path = data.get('path')
        else:
            path = request.args.get('path')

        # Default to selected site path if no path provided
        if not path:
            path = session.get('selected_site_path', '/')

        # List directory contents
        items = file_service.list_directory(connection, path)

        logger.info(f"Browsed {len(items)} items in {path}")

        return jsonify({
            'success': True,
            'path': path,
            'items': items,
            'count': len(items)
        }), 200

    except Exception as e:
        logger.error(f"Browse error: {e}")
        return jsonify({'error': f'Failed to browse directory: {str(e)}'}), 500


@files_bp.route('/download', methods=['POST'])
def download():
    """
    Download a file

    Request JSON:
        {
            "file_path": "/Site001/file.jpg"
        }

    Returns:
        Binary file data
    """
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'Not authenticated'}), 401

        connection = connection_service.get_connection(session_id)
        if not connection:
            return jsonify({'error': 'Session expired'}), 401

        data = request.get_json()
        file_path = data.get('file_path')

        if not file_path:
            return jsonify({'error': 'File path required'}), 400

        # Download file
        file_buffer = file_service.download_file(connection, file_path)

        # Get filename
        filename = os.path.basename(file_path)

        logger.info(f"Downloaded file: {file_path}")

        return send_file(
            file_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': f'Failed to download file: {str(e)}'}), 500


@files_bp.route('/info', methods=['POST'])
def file_info():
    """
    Get file information

    Request JSON:
        {
            "file_path": "/Site001/file.jpg"
        }

    Returns:
        {
            "success": true,
            "file": {
                "name": "file.jpg",
                "size": 1024,
                "modified": "2024-01-01T12:00:00"
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
        file_path = data.get('file_path')

        if not file_path:
            return jsonify({'error': 'File path required'}), 400

        # Get file info
        info = file_service.get_file_info(connection, file_path)

        if not info:
            return jsonify({'error': 'File not found'}), 404

        return jsonify({
            'success': True,
            'file': info
        }), 200

    except Exception as e:
        logger.error(f"File info error: {e}")
        return jsonify({'error': f'Failed to get file info: {str(e)}'}), 500


@files_bp.route('/thumbnail', methods=['GET'])
def generate_thumbnail():
    """
    Generate thumbnail on-demand from SFTP file with caching.
    Checks cache first, generates only if needed.

    Query params:
        file_path: Full path to image file on SFTP server

    Returns:
        Thumbnail image (200x200 JPEG)
    """
    try:
        import tempfile
        import hashlib
        from PIL import Image

        file_path = request.args.get('file_path')
        if not file_path:
            return jsonify({'error': 'file_path required'}), 400

        # Create cache directory
        thumb_dir = os.path.join(tempfile.gettempdir(), "qc_tool_thumbnails")
        os.makedirs(thumb_dir, exist_ok=True)

        # Generate cache filename from file path hash
        path_hash = hashlib.md5(file_path.encode()).hexdigest()
        session_id = session.get('session_id', 'default')
        thumb_filename = f"{session_id}_{path_hash}.jpg"
        thumb_path = os.path.join(thumb_dir, thumb_filename)

        # Serve from cache if exists
        if os.path.exists(thumb_path):
            logger.debug(f"Serving cached thumbnail: {thumb_filename}")
            return send_file(thumb_path, mimetype='image/jpeg')

        # Generate new thumbnail
        connection = get_sftp_connection()

        # Read partial file (first 512KB for thumbnail)
        file_buffer = file_service.read_file_partial(connection, file_path, max_bytes=512 * 1024)

        # Generate thumbnail
        with Image.open(file_buffer) as img:
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            img.save(thumb_path, "JPEG", quality=85)

        logger.info(f"Generated thumbnail: {thumb_filename}")

        return send_file(thumb_path, mimetype='image/jpeg')

    except Exception as e:
        logger.error(f"Error generating thumbnail for {file_path}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@files_bp.route('/preview', methods=['POST', 'GET'])
def preview():
    """
    Preview a file (return file content for display)

    Query params (GET) or Request JSON (POST):
        {
            "file_path": "/Site001/file.jpg",
            "max_size": 10485760  // 10MB max for preview
        }

    Returns:
        Binary file data with appropriate mimetype
    """
    try:
        session_id = session.get('session_id')
        if not session_id:
            return jsonify({'error': 'Not authenticated'}), 401

        connection = connection_service.get_connection(session_id)
        if not connection:
            return jsonify({'error': 'Session expired'}), 401

        # Get parameters
        if request.method == 'GET':
            file_path = request.args.get('file_path')
            max_size = int(request.args.get('max_size', 10 * 1024 * 1024))
        else:
            data = request.get_json()
            file_path = data.get('file_path')
            max_size = data.get('max_size', 10 * 1024 * 1024)

        if not file_path:
            return jsonify({'error': 'File path required'}), 400

        # Check file size first
        info = file_service.get_file_info(connection, file_path)
        if info and info.get('size', 0) > max_size:
            return jsonify({'error': 'File too large for preview'}), 400

        # Download file
        file_buffer = file_service.download_file(connection, file_path)

        # Determine mimetype based on extension
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        mimetype_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.csv': 'text/csv'
        }

        mimetype = mimetype_map.get(ext, 'application/octet-stream')

        return send_file(
            file_buffer,
            mimetype=mimetype
        )

    except Exception as e:
        logger.error(f"Preview error: {e}")
        return jsonify({'error': f'Failed to preview file: {str(e)}'}), 500
