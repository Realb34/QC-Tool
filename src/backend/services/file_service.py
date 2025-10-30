"""
File Service
Handles file operations on FTP/SFTP servers
"""
import io
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import stat
from models.connection import Connection, ConnectionType

logger = logging.getLogger(__name__)


class FileService:
    """Handles file operations"""

    @staticmethod
    def list_directory(connection: Connection, path: str = '/') -> List[Dict[str, Any]]:
        """
        List directory contents

        Args:
            connection: Active connection object
            path: Directory path to list

        Returns:
            List of file/directory information dictionaries

        Raises:
            Exception: If listing fails
        """
        path = path or '/'
        logger.info(f"Listing directory: {path}")

        try:
            if connection.connection_type == ConnectionType.SFTP:
                return FileService._list_sftp(connection, path)
            else:
                return FileService._list_ftp(connection, path)

        except Exception as e:
            logger.error(f"Failed to list directory {path}: {e}")
            raise

    @staticmethod
    def _list_sftp(connection: Connection, path: str) -> List[Dict[str, Any]]:
        """List SFTP directory"""
        client = connection.client
        items = []

        try:
            # Ensure channel has timeout set
            if hasattr(client, 'get_channel') and client.get_channel():
                client.get_channel().settimeout(30.0)

            # Normalize path
            if path == '.' or path == '':
                path = client.getcwd() or '/'

            attrs = client.listdir_attr(path)

            for attr in attrs:
                # Determine if directory
                is_dir = stat.S_ISDIR(attr.st_mode) if attr.st_mode else False

                items.append({
                    'name': attr.filename,
                    'type': 'directory' if is_dir else 'file',
                    'size': attr.st_size if attr.st_size else 0,
                    'modified': datetime.fromtimestamp(attr.st_mtime).isoformat() if attr.st_mtime else None,
                    'permissions': oct(stat.S_IMODE(attr.st_mode))[-3:] if attr.st_mode else None
                })

        except Exception as e:
            logger.error(f"SFTP list error: {e}")
            raise Exception(f"Failed to list directory: {str(e)}")

        return sorted(items, key=lambda x: (x['type'] != 'directory', x['name'].lower()))

    @staticmethod
    def _list_ftp(connection: Connection, path: str) -> List[Dict[str, Any]]:
        """List FTP directory"""
        client = connection.client
        items = []

        try:
            # Change to directory
            if path != client.pwd():
                client.cwd(path)

            # Get directory listing
            lines = []
            client.retrlines('LIST', lines.append)

            for line in lines:
                parts = line.split(None, 8)
                if len(parts) < 9:
                    continue

                permissions = parts[0]
                size_str = parts[4]
                name = parts[8]

                # Skip . and ..
                if name in ['.', '..']:
                    continue

                is_dir = permissions.startswith('d')
                size = int(size_str) if size_str.isdigit() else 0

                items.append({
                    'name': name,
                    'type': 'directory' if is_dir else 'file',
                    'size': size,
                    'modified': None,
                    'permissions': permissions
                })

        except Exception as e:
            logger.error(f"FTP list error: {e}")
            raise Exception(f"Failed to list directory: {str(e)}")

        return sorted(items, key=lambda x: (x['type'] != 'directory', x['name'].lower()))

    @staticmethod
    def download_file(connection: Connection, file_path: str) -> io.BytesIO:
        """
        Download file from server

        Args:
            connection: Active connection object
            file_path: Path to file on server

        Returns:
            BytesIO buffer containing file contents

        Raises:
            Exception: If download fails
        """
        logger.info(f"Downloading file: {file_path}")

        file_buffer = io.BytesIO()

        try:
            if connection.connection_type == ConnectionType.SFTP:
                # Ensure channel has timeout set
                if hasattr(connection.client, 'get_channel') and connection.client.get_channel():
                    connection.client.get_channel().settimeout(30.0)
                with connection.client.open(file_path, 'rb') as remote_file:
                    file_buffer.write(remote_file.read())
            else:
                connection.client.retrbinary(f'RETR {file_path}', file_buffer.write)

            file_buffer.seek(0)
            logger.info(f"Successfully downloaded {file_path}")
            return file_buffer

        except Exception as e:
            logger.error(f"Download error: {e}")
            raise Exception(f"Failed to download file: {str(e)}")

    @staticmethod
    def read_file_partial(connection: Connection, file_path: str, max_bytes: int = 65536) -> io.BytesIO:
        """
        Read only the first portion of a file (for EXIF extraction)

        Args:
            connection: Active connection object
            file_path: Path to file on server
            max_bytes: Maximum bytes to read (default 64KB, enough for EXIF)

        Returns:
            BytesIO buffer containing partial file contents

        Raises:
            Exception: If read fails
        """
        logger.debug(f"Reading partial file (first {max_bytes} bytes): {file_path}")

        file_buffer = io.BytesIO()

        try:
            if connection.connection_type == ConnectionType.SFTP:
                # Ensure channel has timeout set
                if hasattr(connection.client, 'get_channel') and connection.client.get_channel():
                    connection.client.get_channel().settimeout(30.0)
                with connection.client.open(file_path, 'rb') as remote_file:
                    # Read only the first max_bytes
                    data = remote_file.read(max_bytes)
                    file_buffer.write(data)
            else:
                # For FTP, we need to use a callback that stops after max_bytes
                bytes_read = [0]

                def write_callback(data):
                    if bytes_read[0] < max_bytes:
                        remaining = max_bytes - bytes_read[0]
                        chunk = data[:remaining]
                        file_buffer.write(chunk)
                        bytes_read[0] += len(chunk)
                        if bytes_read[0] >= max_bytes:
                            raise Exception("STOP")  # Stop transfer

                try:
                    connection.client.retrbinary(f'RETR {file_path}', write_callback)
                except Exception as e:
                    if "STOP" not in str(e):
                        raise

            file_buffer.seek(0)
            logger.debug(f"Read {file_buffer.tell()} bytes from {file_path}")
            return file_buffer

        except Exception as e:
            logger.error(f"Partial read error: {e}")
            raise Exception(f"Failed to read file: {str(e)}")

    @staticmethod
    def get_file_info(connection: Connection, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information

        Args:
            connection: Active connection object
            file_path: Path to file

        Returns:
            Dictionary with file information or None

        Raises:
            Exception: If operation fails
        """
        try:
            if connection.connection_type == ConnectionType.SFTP:
                attr = connection.client.stat(file_path)
                return {
                    'name': os.path.basename(file_path),
                    'size': attr.st_size,
                    'modified': datetime.fromtimestamp(attr.st_mtime).isoformat() if attr.st_mtime else None,
                    'is_directory': stat.S_ISDIR(attr.st_mode)
                }
            else:
                # FTP doesn't have a direct stat command, use directory listing
                parent = os.path.dirname(file_path)
                filename = os.path.basename(file_path)
                items = FileService.list_directory(connection, parent)

                for item in items:
                    if item['name'] == filename:
                        return item

                return None

        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            raise

    @staticmethod
    def change_directory(connection: Connection, path: str) -> str:
        """
        Change current directory

        Args:
            connection: Active connection object
            path: New directory path

        Returns:
            New current directory path

        Raises:
            Exception: If operation fails
        """
        try:
            if connection.connection_type == ConnectionType.SFTP:
                connection.client.chdir(path)
                return connection.client.getcwd()
            else:
                connection.client.cwd(path)
                return connection.client.pwd()

        except Exception as e:
            logger.error(f"Failed to change directory to {path}: {e}")
            raise Exception(f"Failed to change directory: {str(e)}")

    @staticmethod
    def get_current_directory(connection: Connection) -> str:
        """
        Get current working directory

        Args:
            connection: Active connection object

        Returns:
            Current directory path
        """
        try:
            if connection.connection_type == ConnectionType.SFTP:
                return connection.client.getcwd() or '/'
            else:
                return connection.client.pwd()

        except Exception as e:
            logger.error(f"Failed to get current directory: {e}")
            return '/'


# Global file service instance
file_service = FileService()
