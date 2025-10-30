# QC Viewer MVP - Implementation Summary

## What We Built (Phase 1 - MVP)

### Overview
Created an enhanced QC viewer that replicates core features of the FlightPathViewer desktop application. When a user selects a site, the system now:

1. **Parses site information** - Extracts Site ID and Pilot name from path
2. **Analyzes folder structure** - Counts images, calculates sizes per folder
3. **Extracts GPS data** - Reads EXIF from images to get lat/lon/altitude
4. **Generates 3D visualization** - Interactive Plotly 3D scatter plot showing flight paths
5. **Color-codes folders** - Orbits (red), Scans (green), Center (blue), etc.
6. **Shows statistics** - Total images, folders, size, GPS points

### Key Features Implemented

#### 1. Site Path Parsing
- Extracts pilot name from `/homes/PilotName/...`
- Extracts site ID (8-10 digit number) from path
- Example: `/homes/JasonDunwoody/10001291-08-20-2025-ATT`
  - Pilot: `JasonDunwoody`
  - Site ID: `10001291`

#### 2. GPS Extraction
- Reads EXIF data from JPG/PNG/TIFF images
- Converts GPS coordinates to decimal degrees
- Extracts altitude information
- Samples up to 50 images per folder (for performance)

#### 3. 3D Flight Path Visualization
- **Plotly 3D scatter plot** showing all photo locations
- **Color-coded by folder type**:
  - Orbits: Red (#ff4136)
  - Scans: Green (#2ecc40)
  - Center: Blue (#0074d9)
  - Downlook: Yellow (#ffdc00)
  - Uplook: Purple (#b10dc9)
  - Civil: Orange (#ff851b)
  - Road: Teal (#39cccc)
  - Default: Gray (#aaaaaa)
- **Interactive legend** - Click to show/hide folders
- **Ground plane** - Shows relative altitude
- **Hover tooltips** - Display filename on hover
- **Zoom and rotate** - Full 3D interaction

#### 4. Folder Statistics
- Image count per folder
- Total size per folder (in MB)
- GPS point count per folder
- Visual sidebar with color-coded cards

#### 5. Stats Dashboard
- Total images across site
- Number of folders
- Total site size
- Total GPS points extracted

### File Structure

```
src/backend/
├── api/
│   └── sites.py                    # Added /analyze endpoint
├── services/
│   └── site_analysis_service.py    # NEW: GPS extraction & visualization
└── requirements.txt                # Added Pillow, plotly, numpy

src/frontend/
├── templates/
│   └── qc_viewer.html              # NEW: Enhanced QC viewer page
└── static/
    └── js/
        ├── qc_viewer.js            # NEW: QC viewer logic
        └── sites.js                # Modified to redirect to QC viewer
```

### API Endpoint

**POST /api/sites/analyze**
```json
{
  "site_path": "/homes/PilotName/SiteID-Date"
}
```

**Response:**
```json
{
  "success": true,
  "site_info": {
    "pilot_name": "JasonDunwoody",
    "site_id": "10001291",
    "full_path": "/homes/JasonDunwoody/10001291-08-20-2025-ATT"
  },
  "folders": {
    "Orbits": {
      "image_count": 47,
      "total_size": 15923456,
      "color": "#ff4136",
      "gps_count": 47
    },
    ...
  },
  "total_images": 150,
  "total_size": 102400000,
  "gps_point_count": 142,
  "visualization_html": "<div>...</div>"
}
```

### User Flow

1. User logs in with FTP/SFTP credentials
2. User sees list of site folders (e.g., `10001291-08-20-2025-ATT`)
3. User clicks on a site folder
4. **NEW**: System redirects to `/qc-viewer`
5. **NEW**: Loading screen appears: "Analyzing Site..."
6. **NEW**: Backend:
   - Lists all folders in site
   - Downloads sample images from each folder
   - Extracts GPS/EXIF data
   - Generates 3D Plotly visualization
7. **NEW**: User sees:
   - Site header with Site ID and Pilot name
   - Statistics dashboard
   - Folder list sidebar with colors and stats
   - **3D interactive flight path visualization**

### Technologies Used

- **Backend**: Flask, Pillow (EXIF), NumPy (data processing), Plotly (visualization)
- **Frontend**: Vanilla JavaScript, Plotly.js (embedded)
- **Styling**: Custom CSS with dark theme (matching FlightPathViewer)

---

## Future Phases (Not Yet Implemented)

### Phase 2: Image Gallery & Modal Viewer
- Click on 3D plot points to view images
- Full-screen image modal with zoom/pan
- Thumbnail carousel
- Navigation (prev/next)

### Phase 3: Quality Checks
- Blur detection (OpenCV)
- Corruption detection
- GPS validation
- Progress tracking UI

### Phase 4: Checklist System
- Drag-drop images to checklist items
- Visual confirmation
- Persistence

### Phase 5: Advanced Features
- PDF viewer
- Note extraction
- File operations (rename, delete, convert)
- Matterport integration

### Phase 6: Salesforce Integration
- OAuth authentication
- Fetch site data from Salesforce
- QC Pass workflow
- Status updates

---

## Testing Instructions

### Local Testing

1. **Install dependencies**:
   ```bash
   cd src/backend
   source ../../venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Restart server**:
   ```bash
   cd "/Users/rileybellin/Desktop/QC TOOL WEB BASED"
   ./run.sh
   ```

3. **Test the flow**:
   - Go to http://localhost:5000
   - Login with your FTP credentials (73.156.240.32)
   - Select a site folder (e.g., `10001291-08-20-2025-ATT`)
   - Wait for analysis to complete
   - Verify:
     - Site ID and Pilot name are correct
     - Stats dashboard shows data
     - Folder list appears with colors
     - **3D visualization loads** with colored dots
     - Can interact with 3D plot (zoom, rotate, hover)

### Deployment

1. **Commit changes**:
   ```bash
   git add .
   git commit -m "Add MVP QC Viewer with 3D flight path visualization

   - Extract GPS from images via EXIF
   - Parse site path for pilot name and site ID
   - Generate Plotly 3D scatter visualization
   - Color-code folders (orbits, scans, center, etc.)
   - Display folder statistics and site summary
   - Interactive visualization with zoom, rotate, hover"
   git push
   ```

2. **Render will auto-deploy** and install new dependencies

3. **Monitor deployment**:
   - Check Render dashboard for build logs
   - Verify `Pillow`, `plotly`, and `numpy` are installed
   - Test on live URL

---

## Performance Considerations

- **Sampling**: Only processes up to 50 images per folder (configurable)
- **Progressive loading**: Shows loading state during analysis
- **Caching**: Could add caching for repeated site analyses
- **Optimization**: Future work - thumbnail generation, lazy loading

---

## Known Limitations (MVP)

1. Only samples images (not all) for performance
2. No image caching yet
3. No click-to-view image functionality yet
4. No quality checks yet
5. No Salesforce integration yet
6. Analysis happens on every visit (no caching)

---

## Next Steps

After testing MVP, we can iteratively add:
1. Image modal viewer (click plot points)
2. Thumbnail caching
3. Quality checks (blur, corruption)
4. Checklist system
5. Salesforce integration
6. PDF viewer
7. Full feature parity with FlightPathViewer

---

**Built**: 2025-10-28
**Status**: MVP Ready for Testing
**Version**: 1.0.0 MVP
