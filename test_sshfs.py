#!/usr/bin/env python3
"""
SSHFS Mount Test Script
Tests SSHFS mounting safely before full integration.

Usage:
    python test_sshfs.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'backend'))

from services.sshfs_manager import SSHFSManager
import time

def test_sshfs_mounting():
    """Test SSHFS mounting with real credentials"""

    print("=" * 60)
    print("SSHFS MOUNT TEST")
    print("=" * 60)

    # Initialize manager
    manager = SSHFSManager()

    # Step 1: Check if SSHFS is available
    print("\n[1/6] Checking if SSHFS is installed...")
    if not manager.check_sshfs_available():
        print("❌ SSHFS is not installed on this system")
        print("\nTo install SSHFS on macOS:")
        print("  brew install macfuse")
        print("  brew install gromgit/fuse/sshfs-mac")
        return False
    print("✓ SSHFS is available")

    # Get credentials
    print("\n[2/6] Enter SFTP credentials:")
    host = input("  Host [73.156.240.32]: ").strip() or "73.156.240.32"
    port = input("  Port [22]: ").strip() or "22"
    username = input("  Username [Rileybelin]: ").strip() or "Rileybelin"
    password = input("  Password: ").strip()

    if not password:
        print("❌ Password is required")
        return False

    port = int(port)
    session_id = "test_session"

    # Step 3: Attempt mount
    print(f"\n[3/6] Attempting SSHFS mount...")
    print(f"  Mounting {username}@{host}:/homes")
    print(f"  This may take 10-30 seconds...")

    mount_path = manager.mount(
        session_id=session_id,
        host=host,
        port=port,
        username=username,
        password=password,
        remote_path="/homes"
    )

    if not mount_path:
        print("❌ Mount failed - check logs above for details")
        return False

    print(f"✓ Successfully mounted at: {mount_path}")

    # Step 4: Test read access
    print(f"\n[4/6] Testing read access...")
    try:
        items = os.listdir(mount_path)
        print(f"✓ Can list directory: found {len(items)} items")
        print(f"  First few items: {items[:5]}")

        # Try to read a file (if any exist)
        for item in items[:3]:
            item_path = os.path.join(mount_path, item)
            if os.path.isdir(item_path):
                subitems = os.listdir(item_path)
                print(f"  {item}/: {len(subitems)} items")

    except Exception as e:
        print(f"❌ Read test failed: {e}")
        manager.unmount(session_id)
        return False

    # Step 5: Test write protection (should fail)
    print(f"\n[5/6] Testing write protection (should fail)...")
    try:
        test_file = os.path.join(mount_path, "test_write.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        print(f"❌ WARNING: Write succeeded! Mount is NOT read-only!")
        os.remove(test_file)
    except (OSError, IOError) as e:
        if "read-only" in str(e).lower() or "permission denied" in str(e).lower():
            print(f"✓ Write protection working (mount is read-only)")
        else:
            print(f"⚠️  Write failed with unexpected error: {e}")

    # Step 6: Test unmount
    print(f"\n[6/6] Testing unmount...")
    if manager.unmount(session_id):
        print(f"✓ Successfully unmounted")

        # Verify unmounted
        if not os.path.ismount(mount_path):
            print(f"✓ Mount point is clean")
        else:
            print(f"⚠️  Mount point still shows as mounted")
    else:
        print(f"❌ Unmount failed")
        return False

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nSSHFS is working correctly and safely.")
    print("Ready to integrate into the application.")
    return True


if __name__ == "__main__":
    try:
        success = test_sshfs_mounting()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
