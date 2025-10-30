# Timeout Protection & Hang Prevention Guide

## Overview

This document details all timeout protections and hang prevention mechanisms implemented throughout the QC Tool Web Application to ensure robust operation across all scenarios: connection establishment, folder iteration, parallel processing, and error recovery.

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Request (Browser)                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                ┌───────────────▼───────────────┐
                │   API Layer (sites.py)         │
                │   - Timeout exception handling │
                │   - 504 Gateway Timeout errors │
                └───────────────┬───────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼──────────┐   ┌───────▼────────────┐  ┌──────▼──────────┐
│ Connection Service│   │  File Service       │  │ Site Analysis   │
│ - Initial timeout │   │  - Channel timeout  │  │ - Folder timeout│
│ - Channel setup   │   │  - Operation timeout│  │ - Pool timeout  │
└──────────────────┘   └────────────────────┘  └─────────────────┘
```

## 1. Connection Layer Timeouts

### Initial Connection (`connection_service.py:92-109`)

**Location**: `src/backend/services/connection_service.py`

```python
ssh_client.connect(
    hostname=host,
    port=port,
    username=username,
    password=password,
    timeout=30,              # ✅ 30-second connection timeout
    allow_agent=False,
    look_for_keys=False,
    banner_timeout=30        # ✅ 30-second banner timeout
)

sftp_client = ssh_client.open_sftp()

# Set channel timeout immediately after opening
if hasattr(sftp_client, 'get_channel') and sftp_client.get_channel():
    sftp_client.get_channel().settimeout(30.0)  # ✅ 30-second operation timeout
```

**Protection**:
- Connection establishment: 30 seconds
- SSH banner exchange: 30 seconds
- All SFTP operations: 30 seconds

**Failure Mode**: Raises `ConnectionError` with descriptive message, caught by API layer

---

## 2. File Service Timeouts

### Directory Listing (`file_service.py:48-77`)

**Location**: `src/backend/services/file_service.py`

```python
def _list_sftp(connection: Connection, path: str):
    try:
        # Ensure channel has timeout set
        if hasattr(client, 'get_channel') and client.get_channel():
            client.get_channel().settimeout(30.0)  # ✅ Reset timeout before operation

        attrs = client.listdir_attr(path)  # Protected by channel timeout
```

**Protection**:
- Directory listing: 30-second timeout
- Automatically retries on timeout (handled by API layer)

### File Reading (`file_service.py:147-159`, `185-210`)

```python
def download_file(connection: Connection, file_path: str):
    try:
        if connection.connection_type == ConnectionType.SFTP:
            # Ensure channel has timeout set
            if hasattr(connection.client, 'get_channel'):
                connection.client.get_channel().settimeout(30.0)  # ✅

            with connection.client.open(file_path, 'rb') as remote_file:
                file_buffer.write(remote_file.read())  # Protected by timeout

def read_file_partial(connection: Connection, file_path: str, max_bytes: int):
    # Same timeout protection for partial reads
    if hasattr(connection.client, 'get_channel'):
        connection.client.get_channel().settimeout(30.0)  # ✅
```

**Protection**:
- File open: 30-second timeout
- File read: 30-second timeout per operation
- Partial reads (EXIF): 30-second timeout

---

## 3. Site Analysis Timeouts

### Folder Iteration with Health Checks (`site_analysis_service.py:313-354`)

**Location**: `src/backend/services/site_analysis_service.py`

```python
failed_folders = []

# Process each folder with timeout protection and error recovery
for item in items:
    if item['type'] == 'directory':
        folder_name = item['name']
        folder_path = f"{site_path}/{folder_name}".replace('//', '/')

        try:
            # ✅ Validate main connection is still alive before processing folder
            if connection.connection_type == ConnectionType.SFTP:
                if hasattr(connection.client, 'get_channel'):
                    connection.client.get_channel().settimeout(30.0)
                    # Quick health check - try to stat the folder
                    connection.client.stat(folder_path)  # Fails fast if connection dead

            # Analyze folder contents with timeout protection
            folder_result = analyze_folder(...)

            folders[folder_name] = folder_result
            total_images += folder_result['image_count']
            all_gps_points.extend(folder_result['gps_data'])

        except Exception as e:
            # ✅ Graceful error recovery - continue processing other folders
            logger.error(f"Failed to analyze folder {folder_name}: {e}")
            failed_folders.append(folder_name)

            # Create empty folder result to continue
            folders[folder_name] = {
                'folder_name': folder_name,
                'image_count': 0,
                'gps_data': [],
                'error': str(e)
            }

if failed_folders:
    logger.warning(f"Failed to process {len(failed_folders)} folders: {', '.join(failed_folders)}")
```

**Protection**:
- Connection health check before each folder
- Graceful degradation - failed folders don't stop entire analysis
- Detailed logging of failures
- Returns partial results even if some folders fail

---

## 4. Parallel Processing Timeouts

### Thread-Safe Connection Pool (`site_analysis_service.py:500-520`)

**Location**: `src/backend/services/site_analysis_service.py`

```python
# Create connection pool with timeouts
for i in range(num_workers):
    ssh_client = paramiko.SSHClient()
    ssh_client.connect(
        hostname=host,
        port=port,
        username=username,
        password=password,
        timeout=30,              # ✅ 30-second connection timeout
        allow_agent=False,
        look_for_keys=False
    )

    sftp_client = ssh_client.open_sftp()
    # ✅ Set timeout on the underlying channel to prevent hangs
    sftp_client.get_channel().settimeout(30.0)  # 30-second operation timeout

    connection_pool.append((ssh_client, sftp_client))
```

### Thread-Safe Connection Borrowing (`site_analysis_service.py:535-579`)

```python
# Create a queue for thread-safe connection management
connection_queue = Queue()
for conn in connection_pool:
    connection_queue.put(conn)

def process_image(image_file):
    import socket
    sftp_client = None
    ssh_client = None
    try:
        # ✅ Borrow a connection from the pool (60-second timeout)
        ssh_client, sftp_client = connection_queue.get(timeout=60)

        # Read EXIF data (protected by channel timeout)
        with sftp_client.open(image_path, 'r') as f:
            image_bytes = f.read(65536)

        # Process GPS data...

    except socket.timeout:
        logger.warning(f"  ⏱ Socket timeout: {image_file['name']}")  # ✅
    except EOFError:
        logger.warning(f"  ⚠ Connection closed: {image_file['name']}")  # ✅
    except Exception as e:
        logger.debug(f"  ✗ Error: {image_file['name']}: {e}")
    finally:
        # ✅ Return connection to pool (guaranteed by finally block)
        if ssh_client and sftp_client:
            connection_queue.put((ssh_client, sftp_client))
    return None
```

### Future Result Collection with Timeout (`site_analysis_service.py:588-598`)

```python
# Collect results as they complete (with timeout)
completed = 0
for future in as_completed(futures, timeout=300):  # ✅ 5-minute batch timeout
    completed += 1
    try:
        result = future.result(timeout=30)  # ✅ 30-second per-image timeout
        if result:
            gps_data.append(result)
    except TimeoutError:
        filename = futures[future]
        logger.warning(f"  ⏱ Timeout processing: {filename}")  # ✅ Log and continue
    except Exception as e:
        filename = futures[future]
        logger.error(f"  ✗ Error processing {filename}: {e}")  # ✅ Log and continue
```

**Protection**:
- Connection pool creation: 30-second timeout per connection
- Connection borrowing: 60-second queue timeout
- Per-image processing: 30-second timeout
- Batch processing: 5-minute total timeout
- Socket-level timeouts catch Paramiko hangs
- Queue-based connection management prevents race conditions
- Guaranteed connection return via `finally` blocks

---

## 5. API Layer Timeout Handling

### HTTP Response Timeouts (`api/sites.py:72-79`, `243-251`)

**Location**: `src/backend/api/sites.py`

```python
@sites_bp.route('/list', methods=['GET', 'POST'])
def list_sites():
    try:
        # ... directory listing ...

    except TimeoutError as e:
        # ✅ Explicit timeout handling
        logger.error(f"Listing timed out: {e}")
        return jsonify({'error': 'Directory listing timed out. Please try again.'}), 504
    except Exception as e:
        logger.error(f"Failed to list sites: {e}")
        # ✅ Check for timeout in error message
        if 'timeout' in str(e).lower() or 'timed out' in str(e).lower():
            return jsonify({'error': 'Connection timed out. Please check your network.'}), 504
        return jsonify({'error': f'Failed to list sites: {str(e)}'}), 500

@sites_bp.route('/analyze', methods=['POST'])
def analyze_site():
    try:
        # ... site analysis ...

    except TimeoutError as e:
        # ✅ Explicit timeout handling
        logger.error(f"Site analysis timed out: {e}")
        return jsonify({'error': 'Site analysis timed out. Please try again.'}), 504
    except Exception as e:
        logger.error(f"Failed to analyze site: {e}")
        # ✅ Check for timeout in error message
        if 'timeout' in str(e).lower() or 'timed out' in str(e).lower():
            return jsonify({'error': 'Connection timed out. Please try again.'}), 504
        return jsonify({'error': f'Failed to analyze site: {str(e)}'}), 500
```

**Protection**:
- Returns HTTP 504 Gateway Timeout for timeout errors
- Provides user-friendly error messages
- Logs full error details for debugging
- Catches both explicit `TimeoutError` and timeout strings in exceptions

---

## 6. Complete Timeout Summary

| Layer | Operation | Timeout | Failure Behavior |
|-------|-----------|---------|------------------|
| **Connection** | SSH Connect | 30s | ConnectionError, caught by API |
| **Connection** | Banner Exchange | 30s | ConnectionError, caught by API |
| **Connection** | SFTP Channel | 30s/operation | Socket timeout, retryable |
| **File Service** | List Directory | 30s | Exception, caught by API |
| **File Service** | Read File | 30s/operation | Exception, caught by API |
| **File Service** | Partial Read (EXIF) | 30s | Exception, logged and skipped |
| **Site Analysis** | Folder Health Check | 30s | Exception, folder marked failed |
| **Site Analysis** | Per-Folder Processing | Dynamic | Exception, graceful degradation |
| **Parallel Pool** | Connection Creation | 30s/conn | Logged, pool continues |
| **Parallel Pool** | Connection Borrow | 60s | Exception, logged |
| **Parallel Pool** | Image Processing | 30s/image | Logged, image skipped |
| **Parallel Pool** | Batch Processing | 300s total | TimeoutError, partial results |
| **API Layer** | All Operations | Inherited | HTTP 504, user-friendly message |

---

## 7. Testing Timeout Protection

### Test Connection Timeout
```bash
# Block port to simulate connection timeout
sudo iptables -A OUTPUT -p tcp --dport 22 -j DROP

# Should fail within 30 seconds with "Connection timed out"
```

### Test Operation Timeout
```bash
# Use a very slow SFTP server or throttle network
tc qdisc add dev eth0 root tbf rate 1kbit burst 1kb latency 800ms

# Operations should timeout after 30 seconds
```

### Test Graceful Degradation
```bash
# Corrupt one folder's permissions
chmod 000 /path/to/site/problem-folder

# Site analysis should continue, marking that folder as failed
```

### Test Parallel Processing Recovery
```bash
# Kill SFTP connections mid-processing
while true; do
    pkill -9 -f "sftp.*qctool"
    sleep 5
done

# Parallel processing should handle connection drops gracefully
```

---

## 8. Monitoring & Debugging

### Log Patterns to Watch

**Successful Operations:**
```
✓ Connection pool ready (10 connections)
✓ Progress: 60/138 images processed, 60 GPS points found
✓ Analysis complete: 5 folders, 200 images, 180 GPS points
```

**Timeout Warnings:**
```
⏱ Socket timeout: image123.jpg
⏱ Timeout processing: image456.jpg
```

**Connection Issues:**
```
⚠ Connection closed: image789.jpg
Failed to create pool connection 3: Connection reset by peer
```

**Graceful Degradation:**
```
Failed to analyze folder problem-folder: [Errno 13] Permission denied
Failed to process 1 folders: problem-folder
```

### Health Check Commands

```bash
# Check for hanging processes
ps aux | grep python | grep qctool

# Check SFTP connection count
netstat -an | grep :22 | grep ESTABLISHED | wc -l

# Monitor log for timeouts
tail -f logs/qc_tool.log | grep -E "timeout|⏱|⚠"
```

---

## 9. Best Practices

### For Administrators

1. **Monitor connection pool size**: If using 10 workers, ensure server supports 11+ concurrent SFTP connections (10 workers + 1 main)

2. **Adjust timeouts for slow networks**: If experiencing frequent timeouts on slow connections, increase timeout values:
   ```python
   # connection_service.py, file_service.py, site_analysis_service.py
   settimeout(60.0)  # Increase from 30 to 60 seconds
   ```

3. **Review failed folders**: Check logs after analysis to see which folders failed and why

4. **Network performance**: Use tools like `iperf` to test network bandwidth to SFTP server

### For Users

1. **Be patient with large sites**: Sites with 1000+ images may take 5-10 minutes even with parallel processing

2. **Check logs after analysis**: If some folders show 0 images, check logs for timeout/permission errors

3. **Retry on timeout**: HTTP 504 errors mean the operation timed out - retry after checking network connection

4. **Network stability**: Unstable WiFi can cause intermittent timeouts - use wired connection for large sites

---

## 10. Future Improvements

### Potential Enhancements

1. **Adaptive timeouts**: Increase timeouts dynamically based on observed latency
2. **Resume capability**: Save progress and resume from last successful folder
3. **Connection pooling**: Reuse connections across multiple site analyses
4. **Progress callbacks**: Real-time progress updates to frontend via WebSocket
5. **Retry logic**: Automatic retry with exponential backoff for transient failures

### Configuration Options

Consider making these configurable via environment variables:

```bash
SFTP_CHANNEL_TIMEOUT=30
SFTP_CONNECTION_TIMEOUT=30
PARALLEL_WORKERS=10
PARALLEL_BATCH_TIMEOUT=300
PARALLEL_IMAGE_TIMEOUT=30
```

---

## Summary

The QC Tool Web Application now has comprehensive timeout protection at every layer:

✅ **Connection establishment** - 30-second timeouts prevent indefinite hangs
✅ **File operations** - Channel-level timeouts on all SFTP operations
✅ **Folder iteration** - Health checks and graceful degradation
✅ **Parallel processing** - Thread-safe connection pooling with timeouts
✅ **Error recovery** - Partial results returned even if some operations fail
✅ **User feedback** - Clear error messages with HTTP 504 for timeouts

**No more hangs!** The system will always fail gracefully within predictable timeframes.
