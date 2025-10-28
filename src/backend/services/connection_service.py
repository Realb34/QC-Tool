"""
FTP/SFTP Connection Service
Handles establishing and managing server connections
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import paramiko
from ftplib import FTP, FTP_TLS

from models.connection import Connection, ConnectionType

logger = logging.getLogger(__name__)


class ConnectionService:
    """Manages FTP/SFTP connections"""

    def __init__(self):
        self.active_connections: Dict[str, Connection] = {}

    def connect(self, session_id: str, protocol: str, host: str, port: int,
                username: str, password: str) -> Connection:
        """
        Establish a new FTP/SFTP connection

        Args:
            session_id: Unique session identifier
            protocol: Connection protocol (sftp, ftp, ftps)
            host: Server hostname or IP
            port: Server port
            username: Username for authentication
            password: Password for authentication

        Returns:
            Connection object

        Raises:
            ValueError: If connection parameters are invalid
            ConnectionError: If connection fails
        """
        # Validate protocol
        try:
            conn_type = ConnectionType(protocol.lower())
        except ValueError:
            raise ValueError(f"Invalid protocol: {protocol}. Must be sftp, ftp, or ftps")

        # Validate parameters
        if not host or not username:
            raise ValueError("Host and username are required")

        if not (1 <= port <= 65535):
            raise ValueError("Port must be between 1 and 65535")

        logger.info(f"Attempting {protocol.upper()} connection to {host}:{port} as {username}")

        try:
            if conn_type == ConnectionType.SFTP:
                client = self._connect_sftp(host, port, username, password)
            elif conn_type == ConnectionType.FTPS:
                client = self._connect_ftps(host, port, username, password)
            else:  # FTP
                client = self._connect_ftp(host, port, username, password)

            # Create connection object
            connection = Connection(
                session_id=session_id,
                connection_type=conn_type,
                host=host,
                port=port,
                username=username,
                client=client
            )

            # Store connection
            self.active_connections[session_id] = connection

            logger.info(f"Successfully connected to {host}:{port} ({protocol})")
            return connection

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise ConnectionError(f"Failed to connect: {str(e)}")

    def _connect_sftp(self, host: str, port: int, username: str, password: str):
        """Establish SFTP connection"""
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
                banner_timeout=30
            )

            sftp_client = ssh_client.open_sftp()
            # Store SSH client reference to prevent garbage collection
            sftp_client._ssh_client = ssh_client

            return sftp_client

        except paramiko.AuthenticationException:
            raise ConnectionError("Authentication failed. Check username and password.")
        except paramiko.SSHException as e:
            raise ConnectionError(f"SSH error: {str(e)}")
        except Exception as e:
            raise ConnectionError(f"SFTP connection error: {str(e)}")

    def _connect_ftp(self, host: str, port: int, username: str, password: str):
        """Establish FTP connection"""
        try:
            ftp_client = FTP()
            ftp_client.connect(host=host, port=port, timeout=30)
            ftp_client.login(user=username, passwd=password)
            return ftp_client

        except Exception as e:
            raise ConnectionError(f"FTP connection error: {str(e)}")

    def _connect_ftps(self, host: str, port: int, username: str, password: str):
        """Establish FTPS connection"""
        try:
            ftps_client = FTP_TLS()
            ftps_client.connect(host=host, port=port, timeout=30)
            ftps_client.login(user=username, passwd=password)
            ftps_client.prot_p()  # Secure data connection
            return ftps_client

        except Exception as e:
            raise ConnectionError(f"FTPS connection error: {str(e)}")

    def get_connection(self, session_id: str) -> Optional[Connection]:
        """
        Get active connection by session ID

        Args:
            session_id: Session identifier

        Returns:
            Connection object or None if not found
        """
        connection = self.active_connections.get(session_id)

        if connection and connection.is_expired():
            logger.info(f"Connection {session_id} expired, cleaning up")
            self.disconnect(session_id)
            return None

        if connection:
            connection.update_activity()

        return connection

    def disconnect(self, session_id: str) -> bool:
        """
        Close and remove connection

        Args:
            session_id: Session identifier

        Returns:
            True if connection was found and closed, False otherwise
        """
        connection = self.active_connections.get(session_id)

        if not connection:
            return False

        try:
            if connection.connection_type == ConnectionType.SFTP:
                # Close SFTP and SSH
                ssh_client = getattr(connection.client, '_ssh_client', None)
                connection.client.close()
                if ssh_client:
                    ssh_client.close()
            else:
                # Close FTP/FTPS
                try:
                    connection.client.quit()
                except:
                    connection.client.close()

            logger.info(f"Disconnected session {session_id}")

        except Exception as e:
            logger.error(f"Error closing connection {session_id}: {e}")

        finally:
            del self.active_connections[session_id]

        return True

    def cleanup_expired(self) -> int:
        """
        Clean up expired connections

        Returns:
            Number of connections cleaned up
        """
        expired = [
            sid for sid, conn in self.active_connections.items()
            if conn.is_expired()
        ]

        for session_id in expired:
            self.disconnect(session_id)

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired connections")

        return len(expired)

    def get_active_count(self) -> int:
        """Get count of active connections"""
        return len(self.active_connections)


# Global connection service instance
connection_service = ConnectionService()
