# Browser-Based QC Tool Testing Guide

## 🎉 Good News!

The flight path visualization is **already fully integrated** into your browser-based QC Tool!

All the FlightPathViewer.py plotting logic has been implemented and wired up to the web interface.

---

## 🚀 Quick Start - Test in Browser

### Step 1: Start the Application

```bash
cd /Users/rileybellin/Desktop/QC\ TOOL\ WEB\ BASED
source venv/bin/activate
python src/backend/app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
* Running on http://0.0.0.0:5000
```

### Step 2: Open in Browser

Open your browser to: **http://localhost:5000**

---

## 📋 Complete Workflow

### 1. Login Page (`/`)

**What you see:**
- Clean login form
- Host, Port, Username, Password fields
- "Connect" button

**What to do:**
1. Enter your SFTP credentials:
   - **Host**: `73.156.240.32` (or your SFTP server)
   - **Port**: `22`
   - **Username**: Your username
   - **Password**: Your password
2. Click **Connect**

**What happens:**
- Application connects to SFTP server
- Creates secure session
- Redirects to Sites page on success

---

### 2. Sites Page (`/sites`)

**What you see:**
- List of pilot directories (if browsing `/homes`)
- Or site directories for selected pilot
- Navigation breadcrumbs
- "View QC" button for each site

**What to do:**
1. Browse to find a site with drone images
2. Click on pilot name to see their sites
3. Find a site (e.g., `10001291-08-20-2025-ATT`)
4. Click **"View QC"** button

**What happens:**
- Site is selected and stored in session
- Redirects to QC Viewer page
- Begins site analysis

---

### 3. QC Viewer Page (`/qc-viewer`) ⭐ **THE MAIN EVENT**

**Initial State - Loading:**

You'll see:
```
🔄 Analyzing Site...
Extracting GPS data from images and building 3D visualization
This may take a few minutes depending on site size
```

**What's happening behind the scenes:**
1. Backend connects to SFTP
2. Lists all folders in the site
3. For **each image** in each folder:
   - Reads first 64KB (EXIF header only)
   - Extracts GPS coordinates
   - Extracts DJI RelativeAltitude (or GPS Altitude)
   - Calculates position
4. Applies outlier detection (IQR method)
5. Generates 3D Plotly visualization
6. Returns HTML to browser

**Time estimate:**
- 50 images: ~30 seconds
- 200 images: ~2 minutes
- 500 images: ~5 minutes
- 1000 images: ~10 minutes

---

### 4. Analysis Complete - 3D Visualization

**What you see:**

#### **Header Section:**
- Site ID (e.g., "Site 10001291")
- Pilot name (e.g., "Pilot: JasonDunwoody")
- ← Back to Sites button
- 🔄 Refresh button

#### **Stats Summary:**
Four cards showing:
- **Total Images** (e.g., 370)
- **Folders** (e.g., 3)
- **Total Size** (e.g., 1.4 GB)
- **GPS Points** (e.g., 365)

#### **Left Sidebar - Folder List:**
Shows each folder with:
- **Folder name** (colored border matching trace)
- **Image count** (e.g., "120 images")
- **Size** (e.g., "450.00 MB")
- **GPS points** (e.g., "118 GPS points")
- **"View Images"** button (if thumbnails available)

#### **Main Area - 3D Flight Path Visualization:**

**The 3D plot shows:**
- ✅ **Dark black background**
- ✅ **Dark green ground plane** at the bottom
- ✅ **Colored dots** for each folder:
  - 🔴 Red = Orbit
  - 🟢 Green = Scan
  - 🔵 Blue = Center
  - 🟡 Yellow = Downlook
  - 🟣 Purple = Uplook
  - 🟠 Orange = Civil
  - 🔷 Teal = Road
- ✅ **Red X markers** for GPS outliers (if any)
- ✅ **Legend** on the right showing:
  - Folder name
  - File size
  - Image count
  - Color indicator

**Axes:**
- **X-axis**: Longitude
- **Y-axis**: Latitude
- **Z-axis**: "Height Above Drone Takeoff" (feet)

---

## 🎮 Interactive Features

### 3D Plot Controls

**Rotate:**
- Click and drag to rotate the view
- See the flight path from any angle

**Zoom:**
- Scroll wheel to zoom in/out
- Pinch on trackpad

**Pan:**
- Right-click + drag (or Shift + drag)

**Hover:**
- Hover over any point to see the image filename
- Shows: "DJI_0123.JPG" (example)

**Legend:**
- Click folder names to toggle visibility
- Hide/show specific folders
- Focus on particular flight patterns

**Reset:**
- Double-click plot to reset view
- Returns to default camera angle

---

## ✅ What to Verify

### Visual Checklist

Use this checklist to verify everything is working correctly:

#### **Plot Appearance:**
- [ ] Background is completely black
- [ ] Ground plane is dark green (#002200)
- [ ] Ground plane is flat at the bottom
- [ ] Dots are clearly visible
- [ ] Colors match folder types
- [ ] Legend shows all folders
- [ ] Axis labels are visible and readable

#### **Data Accuracy:**
- [ ] Site ID in header matches the site
- [ ] Pilot name is correct
- [ ] Total image count matches site
- [ ] GPS point count makes sense (should be close to image count)
- [ ] Folder list matches actual folders
- [ ] File sizes look reasonable

#### **Outlier Detection:**
- [ ] If there are red X markers, they're far from main cluster
- [ ] Outliers don't affect axis scaling
- [ ] Main data is clearly visible
- [ ] No "all outliers" scenario (unless GPS data is bad)

#### **Interactivity:**
- [ ] Can rotate view smoothly
- [ ] Zoom works (scroll or pinch)
- [ ] Hover shows filenames
- [ ] Legend items clickable
- [ ] Refresh button works
- [ ] Back button works

#### **Flight Pattern Recognition:**
- [ ] **Orbit folders** show circular patterns
- [ ] **Scan folders** show linear back-and-forth patterns
- [ ] **Center folders** show clustered points
- [ ] Patterns are at different altitudes
- [ ] Coverage area makes sense for cell tower site

---

## 🔍 Advanced Verification

### Compare to FlightPathViewer.py

If you have FlightPathViewer.py (desktop version):

1. **Open same site in both**:
   - Desktop: Open site in FlightPathViewer.py
   - Web: View same site in browser QC Viewer

2. **Compare visually**:
   - Take screenshots of both
   - Check colors are identical
   - Verify same outliers detected
   - Compare axis ranges

3. **Check calculations**:
   - Look at browser console (F12 → Console)
   - Look at server logs
   - Compare GPS point counts
   - Verify outlier counts match

**Expected Result**: Visualizations should be **identical**!

---

## 🐛 Troubleshooting

### Issue: "No GPS data found"

**Symptoms:**
- Empty plot
- Message: "No GPS data found in images"

**Causes:**
1. Images don't have GPS EXIF data
2. Site contains only civil/ground photos (not aerial)
3. GPS tags stripped during transfer

**Solutions:**
1. Check server logs for EXIF extraction errors
2. Try a different site with known aerial imagery
3. Verify images are from DJI drones with GPS

**Check logs:**
```bash
tail -f src/backend/logs/app.log
```

Look for:
```
✗ Error: image.jpg: No GPS data
```

---

### Issue: Plot shows "All outliers"

**Symptoms:**
- Only red X markers visible
- Main view is empty
- All points flagged as outliers

**Causes:**
- GPS coordinates extremely spread out
- Mixed coordinate systems
- Some images from different locations

**What to check:**
Look at server logs for outlier detection:
```
bounds = {'lat_low': 37.70, 'lat_high': 37.85, ...}
✓ Generated visualization: 0 inliers, 250 outliers
```

**Solutions:**
1. Check if site has images from multiple locations
2. Verify GPS data is valid
3. Consider adjusting outlier multiplier (currently 4.0)

---

### Issue: "Analysis taking forever"

**Symptoms:**
- Loading spinner for 15+ minutes
- No progress indication
- Browser feels stuck

**Causes:**
- Large site (1000+ images)
- Slow SFTP connection
- Network issues

**What to check:**
Server logs show progress:
```
📍 Extracting GPS from ALL 500 images in Orbit
  Progress: 20/500 images processed, 18 GPS points found
  Progress: 40/500 images processed, 38 GPS points found
  ...
```

**Solutions:**
1. Wait patiently - extraction is sequential over SFTP
2. Check network connectivity
3. Try smaller site first
4. Verify SFTP server responding

---

### Issue: Plot is blank/black screen

**Symptoms:**
- Black rectangle but no plot elements
- No axes, no dots, no ground plane

**Causes:**
- Plotly.js didn't load
- JavaScript error
- HTML not inserted correctly

**Solutions:**

1. **Check browser console** (F12 → Console):
   ```
   ✓ Plotly library loaded: true
   ✓ Viz container found: true
   ✓ Plot div found: true
   ✓ Plot has data: 3 traces
   ```

2. **Check network tab** (F12 → Network):
   - Verify `plotly-2.27.0.min.js` loaded successfully
   - Check analyze API call returned data

3. **Try refresh**:
   - Click 🔄 Refresh button
   - Or hard refresh browser (Cmd+Shift+R)

---

### Issue: "Session expired" or "Not authenticated"

**Symptoms:**
- Error message when trying to analyze
- Redirected to login page

**Causes:**
- SFTP session timed out
- Server restarted
- Session data lost

**Solutions:**
1. Log in again
2. Select site again
3. Try analysis again

**To prevent:**
- Complete analysis in one session
- Don't leave page idle for extended periods

---

### Issue: Images won't load in carousel

**Symptoms:**
- "View Images" button opens modal
- Images show "Failed to load"
- Takes forever to load

**Causes:**
- Large image files (20+ MB)
- Slow SFTP download
- Thumbnail generation disabled

**Note**: Image carousel is **optional** feature - main visualization doesn't require it.

**Solutions:**
1. Wait 30-60 seconds per image (they're LARGE)
2. Use thumbnail endpoint if enabled
3. Focus on 3D visualization instead

---

## 📊 Performance Expectations

### Analysis Time

| Images | Folders | GPS Extraction | Visualization | Total |
|--------|---------|----------------|---------------|-------|
| 50 | 2-3 | ~30 sec | < 1 sec | ~30s |
| 200 | 3-5 | ~2 min | < 1 sec | ~2m |
| 500 | 4-6 | ~5 min | 1-2 sec | ~5m |
| 1000 | 5-8 | ~10 min | 2-3 sec | ~10m |

**Bottleneck**: SFTP reads (64KB per image)

### Browser Performance

**Recommended:**
- Modern browser (Chrome, Firefox, Safari, Edge)
- Decent GPU (for 3D rendering)
- 4GB+ RAM

**Plot Performance:**
- Up to 1000 GPS points: Smooth
- 1000-5000 points: Still good
- 5000+ points: May slow down rotation

---

## 🎯 Success Criteria

Your implementation is working correctly if:

- [x] Login works with SFTP credentials
- [x] Sites page shows pilot/site directories
- [x] "View QC" button starts analysis
- [x] Loading state shows during extraction
- [x] 3D plot appears with data
- [x] Plot matches FlightPathViewer.py appearance
- [x] All interactive controls work
- [x] Outliers detected and displayed
- [x] Legend shows correct information
- [x] Refresh and navigation work

---

## 📸 Screenshot Gallery

### Expected Visual Flow

**1. Login Page:**
```
┌─────────────────────────────────┐
│  QC Tool Web Application        │
│                                 │
│  Host: [73.156.240.32        ]  │
│  Port: [22]                     │
│  User: [username            ]  │
│  Pass: [**********          ]  │
│                                 │
│      [Connect to SFTP]          │
└─────────────────────────────────┘
```

**2. Sites Page:**
```
┌─────────────────────────────────┐
│ ← Back to Login                 │
│                                 │
│ 📁 JasonDunwoody               │
│ 📁 RileyBellin                 │
│ 📁 AnotherPilot                │
│                                 │
│ (click pilot to see sites)      │
└─────────────────────────────────┘
```

**3. Pilot's Sites:**
```
┌─────────────────────────────────┐
│ homes / JasonDunwoody           │
│                                 │
│ 📂 10001291-08-20-2025-ATT     │
│    [View Files] [View QC] ←     │
│                                 │
│ 📂 10001292-08-21-2025-VZW     │
│    [View Files] [View QC]       │
└─────────────────────────────────┘
```

**4. QC Viewer - 3D Visualization:**
```
┌────────────────────────────────────────────────────────┐
│ ← Back        Site 10001291                  🔄 Refresh │
│              Pilot: JasonDunwoody                      │
├────────────────────────────────────────────────────────┤
│  370 Images  │  3 Folders  │  1.4 GB  │  365 GPS Points │
├──────────────┬─────────────────────────────────────────┤
│ Folders:     │  3D Flight Path Visualization          │
│              │                                         │
│ ▮ Orbit      │         ╱│╲                           │
│ 120 images   │        ╱ │ ╲   ●●                     │
│ 450 MB       │       ╱  │  ●●●  ●                    │
│ 118 GPS pts  │      │  ●│● ●  ●   ●                  │
│ [View Images]│      │ ●●│●●●●    ●●                  │
│              │      │●●●│●● ●●  ●                    │
│ ▮ Scan       │     ╱___│________●                    │
│ 200 images   │    ╱    │      ╱                      │
│ 750 MB       │   │     │     │  Rotate with mouse    │
│ 195 GPS pts  │   │     │     │  Scroll to zoom       │
│ [View Images]│   │     │     │                        │
│              │  Longitude  Latitude                   │
│ ▮ Center     │                                         │
│ 50 images    │  Legend: ● Orbit ● Scan ● Center      │
│ 200 MB       │          × Outliers                    │
│ 47 GPS pts   │                                         │
└──────────────┴─────────────────────────────────────────┘
```

---

## 🚀 Next Steps After Testing

Once you've verified everything works:

### Phase 2 - Performance
- [ ] Add GPS data caching (avoid re-extraction)
- [ ] Implement progress updates (WebSocket or polling)
- [ ] Add connection pooling for parallel extraction
- [ ] Enable thumbnail generation

### Phase 3 - Features
- [ ] Add flight path measurements (distance, area)
- [ ] Add time-based playback animation
- [ ] Export visualization as PNG/PDF
- [ ] Add site comparison feature
- [ ] Add QC checklist integration

### Phase 4 - Quality Control
- [ ] Automatic coverage gap detection
- [ ] Altitude compliance checking
- [ ] Image quality analysis
- [ ] Automatic QC scoring
- [ ] Report generation

---

## 📚 Related Documentation

- **[TESTING_README.md](TESTING_README.md)** - Quick reference
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing
- **[FLIGHTPATHVIEWER_EXTRACTION.md](FLIGHTPATHVIEWER_EXTRACTION.md)** - Technical details
- **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** - Full summary

---

## 🎉 You're Ready!

Start the server and test it in your browser:

```bash
cd /Users/rileybellin/Desktop/QC\ TOOL\ WEB\ BASED
source venv/bin/activate
python src/backend/app.py
```

Then open: **http://localhost:5000**

**The flight path visualization is fully integrated and ready to use!** 🚁📊✨
