#!/bin/bash
# Development server startup script

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  QC Tool Web Application${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/update dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -q -r src/backend/requirements.txt

# Check for .env file
if [ ! -f "src/backend/.env" ]; then
    echo -e "${GREEN}Creating .env file from template...${NC}"
    cp src/backend/.env.example src/backend/.env
    echo -e "${BLUE}Please edit src/backend/.env and set your SECRET_KEY${NC}"
    echo -e "${BLUE}Generate one with: python3 -c 'import secrets; print(secrets.token_hex(32))'${NC}"
fi

# Create necessary directories
mkdir -p src/backend/logs
mkdir -p src/backend/flask_session

# Start server
echo ""
echo -e "${GREEN}Starting development server...${NC}"
echo -e "${BLUE}Access the application at: http://localhost:5000${NC}"
echo ""

cd src/backend
export FLASK_ENV=development
export PYTHONPATH=$(pwd)
python app.py
