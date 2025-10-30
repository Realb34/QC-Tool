# How to Test the Flight Path Visualization

## TL;DR - Quick Start

```bash
# Fastest way to test (mock data):
./quick_test.sh
# Select option 1

# Open the generated visualization:
open /tmp/test_flight_path.html
```

You should see a 3D interactive plot with:
- Dark background
- Green ground plane
- Colored dots (red, green, blue) for different folders
- Red X markers for outliers
- Interactive rotation and zoom

---

## Three Testing Options

### 1️⃣ Unit Test (Recommended First)
**Time**: ~2 seconds
**Requirements**: None (uses mock data)

```bash
cd /Users/rileybellin/Desktop/QC\ TOOL\ WEB\ BASED
source venv/bin/activate
python test_visualization.py
```

**What it tests:**
- ✅ Visualization generation with mock GPS data
- ✅ Outlier detection (IQR method)
- ✅ Ground plane rendering
- ✅ Color-coded folder traces
- ✅ HTML output structure

**Output**: `/tmp/test_flight_path.html` - Open this in your browser!

---

### 2️⃣ Integration Test
**Time**: 5-15 minutes (depends on site size)
**Requirements**: SFTP credentials

```bash
cd /Users/rileybellin/Desktop/QC\ TOOL\ WEB\ BASED
source venv/bin/activate
python test_integration.py
```

You'll be prompted for:
- Host (default: 73.156.240.32)
- Port (default: 22)
- Username
- Password

**What it tests:**
- ✅ SFTP connection
- ✅ Real GPS extraction from drone images
- ✅ Complete workflow (connect → list → analyze → visualize)
- ✅ DJI RelativeAltitude extraction
- ✅ Outlier detection on real data

**Output**: `/tmp/integration_test_<site>.html`

---

### 3️⃣ Full Application Test
**Time**: Ongoing (runs server)
**Requirements**: SFTP credentials

```bash
cd /Users/rileybellin/Desktop/QC\ TOOL\ WEB\ BASED
source venv/bin/activate
python src/backend/app.py
```

Then open browser: **http://localhost:5000**

**Complete workflow:**
1. **Login page** → Enter SFTP credentials
2. **Sites page** → Browse pilots and sites
3. **QC Viewer** → Click "View QC" on any site
4. **3D Visualization** → See the flight path plot!

**What it tests:**
- ✅ Full user workflow
- ✅ Session management
- ✅ Real-time GPS extraction progress
- ✅ Multiple site viewing
- ✅ Browser compatibility

---

## What to Look For

### Visual Checklist ✓

When viewing the 3D plot, verify:

**Plot Elements:**
- [ ] Dark black background
- [ ] Dark green ground plane at the bottom
- [ ] Colored markers for each folder:
  - Red = Orbit
  - Green = Scan
  - Blue = Center
  - Yellow = Downlook
  - Purple = Uplook
- [ ] Red X markers for outliers (if any)
- [ ] Legend showing folder names with sizes/counts

**Interactivity:**
- [ ] Click and drag to rotate view
- [ ] Scroll wheel to zoom in/out
- [ ] Hover over points shows image filenames
- [ ] Legend items clickable to toggle folders

**Data Accuracy:**
- [ ] Title shows correct Site ID and Pilot
- [ ] All image folders represented
- [ ] GPS points form recognizable patterns (orbits, scans, etc.)
- [ ] Altitude axis labeled "Height Above Drone Takeoff"

---

## Troubleshooting

### "No GPS data found"
**Cause**: Images lack GPS EXIF data

**Solution**:
```python
# Check a sample image for GPS tags:
import exifread
with open('sample_image.jpg', 'rb') as f:
    tags = exifread.process_file(f)
    gps_tags = {k: v for k, v in tags.items() if 'GPS' in k or 'drone' in k.lower()}
    print(gps_tags)
```

### "SFTP connection failed"
**Cause**: Wrong credentials or network issue

**Solution**:
1. Test SFTP manually: `sftp username@73.156.240.32`
2. Check firewall settings
3. Verify credentials

### "Visualization is blank"
**Cause**: All points detected as outliers

**Check**:
```bash
# Look at server logs:
tail -f src/backend/logs/app.log
```

Look for outlier detection messages like:
```
✓ Generated visualization: 250 inliers, 5 outliers
```

If you see "0 inliers", the IQR bounds may be too strict.

---

## Performance Expectations

| Site Size | GPS Extraction | Visualization | Total Time |
|-----------|----------------|---------------|------------|
| 50 images | ~30 seconds   | < 1 sec       | ~30s       |
| 200 images | ~2 minutes    | < 1 sec       | ~2m        |
| 500 images | ~5 minutes    | 1-2 sec       | ~5m        |
| 1000 images | ~10 minutes  | 2-3 sec       | ~10m       |

**Note**: GPS extraction reads 64KB per image over SFTP, which is the main bottleneck.

---

## Comparing to FlightPathViewer.py

To verify the web version matches the desktop version:

1. **Same site in both applications**:
   - Open same site in FlightPathViewer.py (desktop)
   - Open same site in QC Viewer (web)

2. **Compare visually**:
   - Screenshot both
   - Check colors match
   - Verify same outliers detected
   - Compare axis ranges

3. **Verify calculations**:
   - Check logs for GPS point counts
   - Compare outlier counts
   - Verify altitude ranges

Should be **identical** - same outlier detection, same colors, same layout!

---

## Next Steps After Testing

Once tests pass:

1. **Add caching** - Store GPS data to avoid re-extraction
2. **Add progress bar** - Real-time updates via WebSocket
3. **Add thumbnails** - Image preview on point hover
4. **Add export** - Download plot as PNG/PDF
5. **Add filtering** - Toggle folders, filter by altitude/time
6. **Add measurements** - Distance, area, volume calculations

---

## Need Help?

**Check logs:**
```bash
tail -f src/backend/logs/app.log
```

**Enable debug mode:**
```python
# In app.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Read full testing guide:**
```bash
cat TESTING_GUIDE.md
```

**Review architecture:**
```bash
cat FLIGHTPATHVIEWER_EXTRACTION.md
```

---

## Quick Reference

```bash
# Unit test (fast)
python test_visualization.py

# Integration test (real SFTP)
python test_integration.py

# Start web server
python src/backend/app.py

# Run interactive menu
./quick_test.sh

# View test output
open /tmp/test_flight_path.html
```

That's it! Happy testing! 🚁📊
