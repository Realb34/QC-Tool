# QC Tool Deployment Guide

## Overview

This guide covers deploying the QC Tool Web Application with 3D flight path visualization and extreme performance optimizations to a production server.

## Quick Start

```bash
# Clone repository
git clone https://github.com/Realb34/QC-Tool.git
cd QC-Tool

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r src/backend/requirements.txt

# Run application
python src/backend/app.py
```

Access at: http://localhost:5000

For production deployment, see full guide below.

---

Full deployment guide continues with Docker, Systemd, Nginx, security, monitoring, etc.

See: https://github.com/Realb34/QC-Tool/blob/main/DEPLOYMENT_GUIDE.md
