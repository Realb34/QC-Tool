#!/usr/bin/env bash
# Render build script

set -e

echo "==> Upgrading pip..."
pip install --upgrade pip wheel setuptools

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Build complete!"
