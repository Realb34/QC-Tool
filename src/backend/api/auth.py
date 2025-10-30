"""
Authentication API
Handles FTP/SFTP server login and session management
"""
import logging
import uuid
from flask import Blueprint, request, jsonify, session

from services.connection_service import connection_service

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login to FTP/SFTP server

    Request JSON:
        {
            "protocol": "sftp|ftp|ftps",
            "host": "server.example.com",
            "port": 22,
            "username": "user",
            "password": "pass"
        }

    Returns:
        {
            "success": true,
            "session_id": "uuid",
            "message": "Connected successfully"
        }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required = ['protocol', 'host', 'port', 'username', 'password']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        protocol = data['protocol']
        host = data['host']
        port = data['port']
        username = data['username']
        password = data['password']

        # Generate session ID
        session_id = str(uuid.uuid4())

        # Attempt connection
        connection = connection_service.connect(
            session_id=session_id,
            protocol=protocol,
            host=host,
            port=port,
            username=username,
            password=password
        )

        # Store session ID in Flask session
        session['session_id'] = session_id
        session['host'] = host
        session['username'] = username
        session['protocol'] = protocol
        session['password'] = password  # Store password for parallel processing connection pooling
        session['port'] = port
        session.permanent = True

        logger.info(f"User logged in: {username}@{host} ({protocol})")

        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Connected successfully',
            'connection': {
                'host': host,
                'port': port,
                'username': username,
                'protocol': protocol
            }
        }), 200

    except ValueError as e:
        logger.warning(f"Login validation error: {e}")
        return jsonify({'error': str(e)}), 400

    except ConnectionError as e:
        logger.error(f"Login connection error: {e}")
        return jsonify({'error': str(e)}), 401

    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({'error': 'Login failed. Please try again.'}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout and close FTP/SFTP connection

    Returns:
        {
            "success": true,
            "message": "Logged out successfully"
        }
    """
    try:
        session_id = session.get('session_id')

        if session_id:
            connection_service.disconnect(session_id)
            logger.info(f"User logged out: session {session_id}")

        # Clear Flask session
        session.clear()

        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200

    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500


@auth_bp.route('/status', methods=['GET'])
def status():
    """
    Get current authentication status

    Returns:
        {
            "authenticated": true,
            "session_id": "uuid",
            "host": "server.example.com",
            "username": "user"
        }
    """
    session_id = session.get('session_id')

    if not session_id:
        return jsonify({
            'authenticated': False
        }), 200

    connection = connection_service.get_connection(session_id)

    if not connection:
        session.clear()
        return jsonify({
            'authenticated': False,
            'message': 'Session expired'
        }), 200

    return jsonify({
        'authenticated': True,
        'session_id': session_id,
        'host': session.get('host'),
        'username': session.get('username'),
        'protocol': session.get('protocol'),
        'connection_age': connection.get_age(),
        'idle_time': connection.get_idle_time()
    }), 200


@auth_bp.route('/validate', methods=['GET'])
def validate():
    """
    Validate current session

    Returns:
        {
            "valid": true
        }
    """
    session_id = session.get('session_id')

    if not session_id:
        return jsonify({'valid': False, 'error': 'No session'}), 401

    connection = connection_service.get_connection(session_id)

    if not connection:
        session.clear()
        return jsonify({'valid': False, 'error': 'Session expired'}), 401

    return jsonify({'valid': True}), 200
