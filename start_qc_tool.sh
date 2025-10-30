#!/bin/bash
# Quick start script for QC Tool Web Application

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║        QC TOOL WEB APPLICATION                            ║"
echo "║        Flight Path Visualization                          ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo ""
    echo "Please create it first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r src/backend/requirements.txt"
    echo ""
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies installed
if ! python -c "import flask" 2>/dev/null; then
    echo "❌ Flask not installed!"
    echo ""
    echo "Please install dependencies:"
    echo "  pip install -r src/backend/requirements.txt"
    echo ""
    exit 1
fi

echo "✅ Environment ready"
echo ""

# Display info
echo "┌────────────────────────────────────────────────────────────┐"
echo "│  Starting Flask development server...                      │"
echo "│                                                            │"
echo "│  📍 URL: http://localhost:5000                            │"
echo "│  🔐 Login with your SFTP credentials                      │"
echo "│  🚁 View flight paths in 3D!                              │"
echo "│                                                            │"
echo "│  Press Ctrl+C to stop the server                          │"
echo "└────────────────────────────────────────────────────────────┘"
echo ""

# Wait a moment for user to read
sleep 2

# Start Flask app
echo "🚀 Launching application..."
echo ""

# Run the app
python src/backend/app.py

# Cleanup message if server stops
echo ""
echo "👋 Server stopped. Goodbye!"
