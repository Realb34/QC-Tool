"""
SSHFS Mount Manager
Safely manages SSHFS mounts for fast local-like file access.
Falls back to SFTP if mounting fails.
"""
import os
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SSHFSManager:
    """Manages SSHFS mounts with safety checks and auto-fallback"""

    def __init__(self):
        self.mount_base = os.path.join(tempfile.gettempdir(), "qc_tool_sshfs")
        self.active_mounts = {}  # session_id -> mount_path

    def check_sshfs_available(self) -> bool:
        """Check if SSHFS is installed on the system"""
        try:
            result = subprocess.run(
                ['which', 'sshfs'],
                capture_output=True,
                text=True,
                timeout=5
            )
            available = result.returncode == 0
            if available:
                logger.info("✓ SSHFS is available on system")
            else:
                logger.warning("✗ SSHFS not installed - will use SFTP fallback")
            return available
        except Exception as e:
            logger.warning(f"Could not check for SSHFS: {e}")
            return False

    def mount(self, session_id: str, host: str, port: int, username: str,
              password: str, remote_path: str = "/homes") -> Optional[str]:
        """
        Mount remote SFTP server via SSHFS (read-only for safety).

        Returns:
            Mount path if successful, None if failed
        """
        try:
            # Check if SSHFS is available
            if not self.check_sshfs_available():
                logger.warning("SSHFS not available, using SFTP fallback")
                return None

            # Create mount point
            mount_path = os.path.join(self.mount_base, session_id)
            os.makedirs(mount_path, exist_ok=True)

            # Check if already mounted
            if self.is_mounted(mount_path):
                logger.info(f"Already mounted at {mount_path}")
                self.active_mounts[session_id] = mount_path
                return mount_path

            # Build SSHFS command (READ-ONLY for safety)
            logger.info(f"Attempting SSHFS mount: {username}@{host}:{remote_path} -> {mount_path}")

            # Use sshpass to pass password (or use SSH keys in production)
            cmd = [
                'sshfs',
                f'{username}@{host}:{remote_path}',
                mount_path,
                '-o', 'ro',  # READ-ONLY - cannot modify remote files
                '-o', 'reconnect',  # Auto-reconnect on network issues
                '-o', 'ServerAliveInterval=15',  # Keep connection alive
                '-o', 'ServerAliveCountMax=3',  # Retry 3 times
                '-o', f'Port={port}',
                '-o', 'StrictHostKeyChecking=no',  # Auto-accept host key
                '-o', 'UserKnownHostsFile=/dev/null',  # Don't save host key
                '-o', f'password_stdin'  # Read password from stdin
            ]

            # Execute mount command
            result = subprocess.run(
                cmd,
                input=password,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Verify mount succeeded by testing read access
                if self.verify_mount(mount_path):
                    self.active_mounts[session_id] = mount_path
                    logger.info(f"✓ SSHFS mount successful: {mount_path}")
                    return mount_path
                else:
                    logger.error("Mount succeeded but verification failed")
                    self.unmount(session_id)
                    return None
            else:
                logger.error(f"SSHFS mount failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("SSHFS mount timed out after 30 seconds")
            return None
        except Exception as e:
            logger.error(f"SSHFS mount error: {e}", exc_info=True)
            return None

    def verify_mount(self, mount_path: str) -> bool:
        """Verify mount is working by testing read access"""
        try:
            # Check if mount point is accessible
            if not os.path.ismount(mount_path):
                logger.error(f"{mount_path} is not a mount point")
                return False

            # Try to list directory
            items = os.listdir(mount_path)
            logger.debug(f"Mount verification: found {len(items)} items")
            return len(items) > 0

        except Exception as e:
            logger.error(f"Mount verification failed: {e}")
            return False

    def is_mounted(self, mount_path: str) -> bool:
        """Check if a path is currently mounted"""
        try:
            return os.path.ismount(mount_path)
        except Exception:
            return False

    def unmount(self, session_id: str) -> bool:
        """Safely unmount SSHFS mount"""
        try:
            mount_path = self.active_mounts.get(session_id)
            if not mount_path:
                logger.debug(f"No mount found for session {session_id}")
                return True

            if not self.is_mounted(mount_path):
                logger.debug(f"{mount_path} is not mounted")
                self.active_mounts.pop(session_id, None)
                return True

            logger.info(f"Unmounting {mount_path}")

            # Try normal unmount first
            result = subprocess.run(
                ['umount', mount_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.info(f"✓ Unmounted {mount_path}")
                self.active_mounts.pop(session_id, None)

                # Clean up mount directory
                try:
                    os.rmdir(mount_path)
                except Exception:
                    pass

                return True
            else:
                # Try force unmount
                logger.warning(f"Normal unmount failed, trying force unmount")
                result = subprocess.run(
                    ['umount', '-f', mount_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    logger.info(f"✓ Force unmounted {mount_path}")
                    self.active_mounts.pop(session_id, None)
                    return True
                else:
                    logger.error(f"Force unmount failed: {result.stderr}")
                    return False

        except Exception as e:
            logger.error(f"Unmount error: {e}", exc_info=True)
            return False

    def get_mount_path(self, session_id: str) -> Optional[str]:
        """Get mount path for a session if it exists and is healthy"""
        mount_path = self.active_mounts.get(session_id)

        if not mount_path:
            return None

        # Health check - verify mount is still working
        if not self.is_mounted(mount_path):
            logger.warning(f"Mount {mount_path} is no longer active")
            self.active_mounts.pop(session_id, None)
            return None

        return mount_path

    def cleanup_all(self):
        """Cleanup all mounts (call on application shutdown)"""
        logger.info("Cleaning up all SSHFS mounts")
        for session_id in list(self.active_mounts.keys()):
            self.unmount(session_id)


# Global instance
sshfs_manager = SSHFSManager()
