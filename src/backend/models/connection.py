"""
Connection model
Represents an active FTP/SFTP connection
"""
from enum import Enum
from datetime import datetime, timedelta
from typing import Any, Optional


class ConnectionType(Enum):
    """Supported connection types"""
    SFTP = 'sftp'
    FTP = 'ftp'
    FTPS = 'ftps'


class Connection:
    """
    Represents an active server connection

    Attributes:
        session_id: Unique session identifier
        connection_type: Type of connection (SFTP, FTP, FTPS)
        host: Server hostname
        port: Server port
        username: Username for authentication
        client: Underlying client object (SFTP/FTP)
        created_at: Connection creation time
        last_activity: Last activity timestamp
        metadata: Additional connection metadata
    """

    def __init__(self,
                 session_id: str,
                 connection_type: ConnectionType,
                 host: str,
                 port: int,
                 username: str,
                 client: Any,
                 timeout: int = 14400):  # 4 hours default
        """
        Initialize connection

        Args:
            session_id: Unique session ID
            connection_type: Connection type enum
            host: Server hostname
            port: Server port
            username: Username
            client: FTP/SFTP client object
            timeout: Connection timeout in seconds
        """
        self.session_id = session_id
        self.connection_type = connection_type
        self.host = host
        self.port = port
        self.username = username
        self.client = client
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.timeout = timeout
        self.metadata = {}

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()

    def is_expired(self) -> bool:
        """
        Check if connection has expired

        Returns:
            True if connection is expired, False otherwise
        """
        elapsed = (datetime.now() - self.last_activity).total_seconds()
        return elapsed > self.timeout

    def get_age(self) -> int:
        """
        Get connection age in seconds

        Returns:
            Connection age in seconds
        """
        return int((datetime.now() - self.created_at).total_seconds())

    def get_idle_time(self) -> int:
        """
        Get idle time in seconds

        Returns:
            Idle time in seconds
        """
        return int((datetime.now() - self.last_activity).total_seconds())

    def to_dict(self) -> dict:
        """
        Convert connection to dictionary (without sensitive data)

        Returns:
            Dictionary representation
        """
        return {
            'session_id': self.session_id,
            'connection_type': self.connection_type.value,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'age_seconds': self.get_age(),
            'idle_seconds': self.get_idle_time(),
            'is_expired': self.is_expired()
        }

    def __repr__(self) -> str:
        return (f"Connection(session_id='{self.session_id}', "
                f"type={self.connection_type.value}, "
                f"host='{self.host}', "
                f"user='{self.username}')")
