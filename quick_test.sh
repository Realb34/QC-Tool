#!/bin/bash
# Quick test script for QC Tool Web Application

set -e  # Exit on error

echo "=================================================="
echo "QC TOOL WEB APPLICATION - QUICK TEST"
echo "=================================================="
echo ""

# Change to project directory
cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: python3 -m venv venv && source venv/bin/activate && pip install -r src/backend/requirements.txt"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Show menu
echo "Select test type:"
echo ""
echo "  1) Unit Test (Fast - Mock data, no SFTP)"
echo "  2) Integration Test (Slow - Real SFTP connection)"
echo "  3) Full Application (Start Flask server)"
echo "  4) Run all tests"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo ""
        echo "Running unit test..."
        python test_visualization.py
        ;;
    2)
        echo ""
        echo "Running integration test..."
        python test_integration.py
        ;;
    3)
        echo ""
        echo "Starting Flask development server..."
        echo "Open browser to: http://localhost:5000"
        echo "Press Ctrl+C to stop"
        echo ""
        python src/backend/app.py
        ;;
    4)
        echo ""
        echo "Running all tests..."
        echo ""
        echo "[1/2] Unit test..."
        python test_visualization.py
        echo ""
        echo "[2/2] Integration test..."
        python test_integration.py
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Done!"
