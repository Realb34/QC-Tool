#!/bin/bash
# Quick deployment script to push to GitHub

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}  QC Tool - GitHub Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Initializing Git repository...${NC}"
    git init
    echo -e "${GREEN}✓ Git initialized${NC}"
else
    echo -e "${GREEN}✓ Git already initialized${NC}"
fi

# Check if remote exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo ""
    echo -e "${YELLOW}GitHub repository URL needed${NC}"
    echo "Create a new repository at: https://github.com/new"
    echo ""
    read -p "Enter your GitHub repository URL: " REPO_URL

    if [ -z "$REPO_URL" ]; then
        echo -e "${RED}Error: Repository URL is required${NC}"
        exit 1
    fi

    git remote add origin "$REPO_URL"
    echo -e "${GREEN}✓ Remote added${NC}"
else
    REPO_URL=$(git remote get-url origin)
    echo -e "${GREEN}✓ Remote already configured: ${REPO_URL}${NC}"
fi

# Stage all files
echo ""
echo -e "${YELLOW}Staging files...${NC}"
git add .
echo -e "${GREEN}✓ Files staged${NC}"

# Commit
echo ""
read -p "Enter commit message (or press Enter for default): " COMMIT_MSG
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Deploy QC Tool Web Application v2.0"
fi

git commit -m "$COMMIT_MSG" || echo "No changes to commit"
echo -e "${GREEN}✓ Changes committed${NC}"

# Push to GitHub
echo ""
echo -e "${YELLOW}Pushing to GitHub...${NC}"
git branch -M main
git push -u origin main

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✓ Successfully pushed to GitHub!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "1. Deploy on Render.com:"
echo "   → Go to https://render.com"
echo "   → Click 'New +' → 'Web Service'"
echo "   → Connect your GitHub repository"
echo "   → Click 'Create Web Service'"
echo ""
echo "2. Or deploy on Railway.app:"
echo "   → Go to https://railway.app"
echo "   → Click 'New Project' → 'Deploy from GitHub'"
echo "   → Select your repository"
echo ""
echo -e "${GREEN}Your app will be live in ~5 minutes!${NC}"
echo ""
