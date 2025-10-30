# QC Tool Web Implementation Plan
## Based on FlightPathViewer.py Analysis

## KEY INSIGHTS FROM FlightPathViewer.py

### How It Works:
1. **Runs LOCALLY** - all files on disk, no SFTP during viewing
2. **Pre-generates thumbnails** to `/tmp` folder (line 1848-1867)
3. **Caches thumbnails** with `file://` URIs
4. **Includes full Plotly.js** in HTML (`include_plotlyjs=True`)
5. **No HTTP requests** during viewing - everything cached first

### Critical Functions:
- `generate_thumbnail()` (line 1848): Creates 200x200 thumbnails in `/tmp`
- `scan_images()` (line 1913): Scans all images, extracts GPS, generates thumbnails
- `build_plotly_html()` (line 2956): Builds visualization with full Plotly.js included

## IMPLEMENTATION FOR WEB VERSION

### Phase 1: Server-Side Thumbnail Generation

**File: `src/backend/services/site_analysis_service.py`**

Add thumbnail generation function:
```python
def generate_thumbnail_from_sftp(connection, file_path, session_id, size=(200, 200)):
    """
    Generate thumbnail from SFTP file and cache it locally.
    Matches FlightPathViewer approach but works with SFTP.
    """
    # Create unique filename using hash
    path_hash = hashlib.md5(file_path.encode()).hexdigest()
    thumb_filename = f"{session_id}_{path_hash}.jpg"
    thumb_path = os.path.join(THUMBNAIL_CACHE_DIR, thumb_filename)

    # Return cached if exists
    if os.path.exists(thumb_path):
        return thumb_filename

    # Download partial file (first 512KB for thumbnail quality)
    file_buffer = file_service.read_file_partial(connection, file_path, max_bytes=512 * 1024)

    # Generate thumbnail
    with Image.open(file_buffer) as img:
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(thumb_path, "JPEG", quality=85)

    return thumb_filename
```

Modify `analyze_folder()` to generate thumbnails:
```python
# In the image processing loop:
for img_file in image_files[:10]:  # First 10 for samples
    image_path = f"{folder_path}/{img_file['name']}"

    # Extract GPS
    gps_data = extract_gps_from_exif(...)

    # Generate thumbnail (do this sequentially to avoid SFTP errors)
    try:
        thumb_filename = generate_thumbnail_from_sftp(
            connection, image_path, session_id
        )
        sample_images.append({
            'name': img_file['name'],
            'path': image_path,
            'thumbnail': thumb_filename  # Add thumbnail reference
        })
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        sample_images.append({
            'name': img_file['name'],
            'path': image_path,
            'thumbnail': None
        })
```

### Phase 2: Thumbnail Serving Endpoint

**File: `src/backend/api/files.py`**

Add static thumbnail endpoint:
```python
@files_bp.route('/thumbnail/<filename>', methods=['GET'])
def serve_thumbnail(filename):
    """
    Serve cached thumbnail file.
    This is fast because files are already on disk.
    """
    try:
        thumb_path = os.path.join(THUMBNAIL_CACHE_DIR, filename)

        if not os.path.exists(thumb_path):
            return jsonify({'error': 'Thumbnail not found'}), 404

        return send_file(thumb_path, mimetype='image/jpeg')

    except Exception as e:
        logger.error(f"Error serving thumbnail {filename}: {e}")
        return jsonify({'error': str(e)}), 500
```

### Phase 3: Fix Plotly Visualization

**File: `src/backend/services/site_analysis_service.py`**

Change line ~409:
```python
# BEFORE:
html = fig.to_html(
    full_html=False,
    include_plotlyjs=False,  # ❌ WRONG - requires external CDN
    ...
)

# AFTER (matching FlightPathViewer):
html = fig.to_html(
    full_html=False,
    include_plotlyjs=True,  # ✅ Include full library
    config={'scrollZoom': True, 'displayModeBar': True, 'responsive': True},
    div_id='flight-path-plot'
)
```

**File: `src/frontend/templates/qc_viewer.html`**

REMOVE the Plotly CDN script (not needed anymore):
```html
<!-- DELETE THIS: -->
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
```

### Phase 4: Update Carousel to Use Cached Thumbnails

**File: `src/frontend/static/js/qc_viewer.js`**

Change carousel to show actual thumbnails:
```javascript
function buildImageThumbnailGrid() {
    const container = document.getElementById('carouselThumbnails');
    container.innerHTML = '';

    // Build grid of actual thumbnail images
    currentCarouselImages.forEach((img, index) => {
        const thumbDiv = document.createElement('div');
        thumbDiv.className = 'carousel-thumbnail';
        thumbDiv.style.cssText = `
            width: 100px;
            height: 80px;
            cursor: pointer;
            border: 2px solid ${index === currentCarouselIndex ? '#2ecc40' : 'transparent'};
        `;

        const thumbImg = document.createElement('img');
        // Use cached thumbnail - loads instantly!
        if (img.thumbnail) {
            thumbImg.src = `/api/files/thumbnail/${img.thumbnail}`;
        } else {
            thumbImg.src = 'data:image/svg+xml,...';  // Placeholder
        }
        thumbImg.style.cssText = 'width:100%;height:100%;object-fit:cover;';

        thumbDiv.appendChild(thumbImg);
        thumbDiv.onclick = () => showCarouselImage(index);
        container.appendChild(thumbDiv);
    });
}
```

### Phase 5: Session Cleanup

**File: `src/backend/services/connection_service.py`**

Add cleanup on logout:
```python
def cleanup_session_thumbnails(session_id):
    """Clean up thumbnails when session ends"""
    import glob
    pattern = os.path.join(THUMBNAIL_CACHE_DIR, f"{session_id}_*.jpg")
    for thumb_file in glob.glob(pattern):
        try:
            os.remove(thumb_file)
        except:
            pass
```

## IMPLEMENTATION ORDER

1. ✅ Add thumbnail generation to `site_analysis_service.py`
2. ✅ Add `/thumbnail/<filename>` endpoint to `files.py`
3. ✅ Change Plotly to `include_plotlyjs=True`
4. ✅ Remove Plotly CDN from template
5. ✅ Update carousel JavaScript to use thumbnails
6. ✅ Add session cleanup
7. ✅ Test!

## WHY THIS WORKS

### FlightPathViewer Approach:
- Files on disk → instant access
- Thumbnails pre-generated → instant display
- file:// URIs → no HTTP overhead

### Our Web Approach:
- SFTP files → download once to /tmp
- Thumbnails pre-generated → cached on server
- HTTP endpoint → serves from /tmp (fast!)
- Same user experience, different backend

## PERFORMANCE COMPARISON

### Before (Current):
- Carousel opens → 10 simultaneous SFTP requests → ERROR
- Each image → 30-60 seconds → User waits forever
- Plotly → CDN might not load → Blank screen

### After (FlightPathViewer approach):
- Analysis → Generates 10 thumbnails sequentially (2-3 minutes total)
- Carousel opens → 10 cached thumbnails load in < 1 second
- Click image → Still takes 30-60s (SFTP download)
- Plotly → Includes library → Always works

## CRITICAL FIXES

1. **Thumbnails**: Pre-generate and cache (like FlightPathViewer)
2. **Plotly**: Include full library in HTML (like FlightPathViewer)
3. **No concurrent SFTP**: Generate thumbnails sequentially
4. **Cache everything**: Use /tmp directory on server

This matches exactly how FlightPathViewer works, adapted for web/SFTP.
