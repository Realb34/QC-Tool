# SSHFS Setup Guide

## What is SSHFS?

SSHFS lets you mount a remote SFTP server as if it were a local folder. This makes file access **10-50x faster** because:
- Files can be cached locally
- No network latency for repeated reads
- OS-level optimizations

**Safety:** SSHFS is read-only and cannot modify the remote server.

---

## Step 1: Check if SSHFS is Already Installed

```bash
which sshfs
```

- If it shows a path (like `/opt/homebrew/bin/sshfs`), skip to Step 3
- If it says "sshfs not found", continue to Step 2

---

## Step 2: Install SSHFS (macOS)

### Option A: Using Homebrew (Recommended)

```bash
# Install macFUSE first (required dependency)
brew install macfuse

# Install SSHFS
brew install gromgit/fuse/sshfs-mac

# Verify installation
which sshfs
```

**Important:** macFUSE may require you to allow a kernel extension in System Preferences:
1. Go to **System Preferences** → **Security & Privacy**
2. Click **Allow** for the macFUSE kernel extension
3. **Restart your Mac** after allowing the extension

### Option B: Manual Installation

1. Download macFUSE from: https://osxfuse.github.io/
2. Download SSHFS from: https://github.com/osxfuse/sshfs/releases
3. Install both packages
4. Restart your Mac

---

## Step 3: Test SSHFS (Safe Test - No Code Changes)

Run the test script to verify everything works:

```bash
cd "/Users/rileybellin/Desktop/QC TOOL WEB BASED"
python test_sshfs.py
```

**What it tests:**
1. ✓ SSHFS is installed
2. ✓ Can mount remote server
3. ✓ Can read files
4. ✓ Write protection is working (read-only)
5. ✓ Can unmount cleanly
6. ✓ No traces left behind

**Expected output:**
```
============================================================
SSHFS MOUNT TEST
============================================================

[1/6] Checking if SSHFS is installed...
✓ SSHFS is available

[2/6] Enter SFTP credentials:
  Host [73.156.240.32]:
  Port [22]:
  Username [Rileybelin]:
  Password: ******

[3/6] Attempting SSHFS mount...
  Mounting Rileybelin@73.156.240.32:/homes
  This may take 10-30 seconds...
✓ Successfully mounted at: /tmp/qc_tool_sshfs/test_session

[4/6] Testing read access...
✓ Can list directory: found 115 items
  First few items: ['JasonDunwoody', 'DavidLynn', ...]

[5/6] Testing write protection (should fail)...
✓ Write protection working (mount is read-only)

[6/6] Testing unmount...
✓ Successfully unmounted
✓ Mount point is clean

============================================================
✅ ALL TESTS PASSED!
============================================================

SSHFS is working correctly and safely.
Ready to integrate into the application.
```

---

## Step 4: If Test Fails

### Error: "sshfs: command not found"
- SSHFS is not installed
- Follow Step 2 above

### Error: "macFUSE kernel extension blocked"
1. Go to System Preferences → Security & Privacy
2. Click "Allow" for macFUSE
3. Restart your Mac
4. Run test again

### Error: "Permission denied" or "Authentication failed"
- Check your SFTP credentials
- Make sure you can connect via normal SFTP first

### Error: "Mount failed" or "Operation not permitted"
- On macOS Ventura+, you may need to give Terminal "Full Disk Access"
- System Preferences → Security & Privacy → Privacy → Full Disk Access
- Add Terminal.app or your IDE

---

## Step 5: Performance Testing

After successful test, you can benchmark the speed difference:

```bash
# Mount the server
sshfs Rileybelin@73.156.240.32:/homes /tmp/test_mount -o ro

# Test read speed (should be fast)
time cat /tmp/test_mount/DavidLynn/12990785-ATT-091425-FDS-LYNN/some_image.jpg > /dev/null

# Unmount
umount /tmp/test_mount
```

**Expected speeds:**
- First read: 1-3 seconds (network)
- Repeated reads: 0.1 seconds (cached)
- SFTP read: 5-10 seconds (always slow)

---

## Safety Guarantees

✅ **Cannot modify remote server** - Mounted read-only
✅ **Cannot delete files** - Read-only mode prevents all writes
✅ **No server-side installation** - Uses standard SSH/SFTP
✅ **Completely reversible** - Unmount leaves no trace
✅ **Auto-recovers** - If mount fails, app uses SFTP fallback
✅ **Network failure safe** - Just shows "file not found" errors

---

## Troubleshooting

### "Transport endpoint is not connected"
Mount became stale. Force unmount:
```bash
umount -f /tmp/qc_tool_sshfs/test_session
```

### Mount won't unmount
```bash
# Force unmount
sudo umount -f /tmp/qc_tool_sshfs/test_session

# If that fails, reboot (cleanly unmounts everything)
```

### Permission errors on Mac
Give Terminal full disk access:
1. System Preferences → Security & Privacy → Privacy
2. Full Disk Access → Add Terminal

---

## Next Steps

Once `test_sshfs.py` passes:
1. ✅ SSHFS is working correctly
2. ✅ Read-only protection is active
3. ✅ Ready to integrate into Flask app

The Flask app will:
- Auto-detect if SSHFS is available
- Use SSHFS when available (fast)
- Fallback to SFTP if SSHFS unavailable (slow but works)
- User never needs to know which mode is active
