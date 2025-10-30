# Quick Reference - Flight Path Visualization Testing

## 🚀 Fastest Test (30 seconds)

```bash
cd /Users/rileybellin/Desktop/QC\ TOOL\ WEB\ BASED
source venv/bin/activate
python test_visualization.py
open /tmp/test_flight_path.html
```

## 🌐 Full Web App Test

```bash
cd /Users/rileybellin/Desktop/QC\ TOOL\ WEB\ BASED
source venv/bin/activate
python src/backend/app.py
```

Then open: **http://localhost:5000**

## 📋 What to Check

**In the 3D plot, you should see:**
- ✅ Dark black background
- ✅ Green ground plane
- ✅ Colored dots (red/green/blue)
- ✅ Red X for outliers
- ✅ Interactive rotation (click + drag)
- ✅ Zoom (scroll wheel)
- ✅ Hover shows filenames

## 📁 Key Files

| File | Purpose |
|------|---------|
| [site_analysis_service.py](src/backend/services/site_analysis_service.py) | Main implementation |
| [test_visualization.py](test_visualization.py) | Unit test |
| [test_integration.py](test_integration.py) | SFTP integration test |
| [quick_test.sh](quick_test.sh) | Interactive test menu |

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [TESTING_README.md](TESTING_README.md) | **START HERE** - Quick testing guide |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | Comprehensive testing instructions |
| [FLIGHTPATHVIEWER_EXTRACTION.md](FLIGHTPATHVIEWER_EXTRACTION.md) | Technical architecture |
| [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) | Implementation summary |

## 🎯 Expected Results

**Unit Test Output:**
```
✓ Generated HTML (42,721 bytes)
✓ plotly.js CDN
✓ Plot container
✓ 3D scatter traces
✓ Ground surface
✓ Site ID in title
✓ Pilot name in title
✓ Outlier trace present

✅ ALL TESTS PASSED!
```

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "No GPS data found" | Check images have GPS EXIF tags |
| "SFTP connection failed" | Verify credentials |
| "Blank visualization" | All points flagged as outliers |
| "Module not found" | Run `source venv/bin/activate` |

## 📊 Implemented Features

- ✅ GPS extraction (DJI RelativeAltitude)
- ✅ Outlier detection (IQR method, 4.0× multiplier)
- ✅ Ground plane (dark green)
- ✅ Fixed axis ranges (inlier-based)
- ✅ Color-coded folders
- ✅ Dark theme
- ✅ Interactive 3D controls
- ✅ Legend (size + file count)

## 🔗 Quick Commands

```bash
# Run unit test
python test_visualization.py

# Run integration test (with SFTP)
python test_integration.py

# Start Flask server
python src/backend/app.py

# Interactive menu
./quick_test.sh

# View test output
open /tmp/test_flight_path.html

# Check logs
tail -f src/backend/logs/app.log
```

## ✨ That's It!

You now have **identical plotting logic** to FlightPathViewer.py deployed in your web application!

**Next**: Run `python test_visualization.py` to see it in action! 🚁
