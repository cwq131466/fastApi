#!/bin/bash
# Frontend build and deployment script for web_frontend
# This script should be run on a machine with Node.js installed

set -e

echo "========================================="
echo "Vue FastAPI Admin - Frontend Build Script"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Please install Node.js first:"
    echo "  Ubuntu/Debian: sudo apt-get install -y nodejs npm"
    echo "  Using nvm: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash && nvm install --lts"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Node.js version: $(node -v)"
echo -e "${GREEN}✓${NC} npm version: $(npm -v)"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "Project directory: $SCRIPT_DIR"
echo ""

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${GREEN}✓${NC} Dependencies already installed"
fi

# Clean previous build
if [ -d "dist" ]; then
    echo "Cleaning previous build..."
    rm -rf dist
    echo -e "${GREEN}✓${NC} Previous build cleaned"
fi

# Build the project
echo ""
echo -e "${YELLOW}Building frontend application...${NC}"
npm run build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Build successful!"
else
    echo -e "${RED}✗${NC} Build failed!"
    exit 1
fi

# Verify build output
echo ""
echo "Build output verification:"
echo "------------------------"
ls -lh dist/
echo ""
echo "Assets directory:"
ls -lh dist/assets/ 2>/dev/null || echo "No assets directory found"
echo ""

# Check index.html content
echo "Checking index.html resource paths:"
echo "------------------------"
grep -E "(src|href)=.*assets" dist/index.html || echo "No asset references found in index.html"
echo ""

# Verify base path is correct (should be absolute paths starting with /)
if grep -q 'src="./assets' dist/index.html; then
    echo -e "${RED}⚠ Warning: Found relative paths in index.html${NC}"
    echo "This may cause issues with SPA routing."
    echo "Please check vite.config.js base configuration."
elif grep -q 'src="/assets' dist/index.html; then
    echo -e "${GREEN}✓${NC} Using absolute paths (correct for SPA)"
fi

echo ""
echo "========================================="
echo -e "${GREEN}Build completed successfully!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Deploy the 'dist' folder to your server:"
echo "   scp -r dist/* user@your-server:/var/www/vue-admin/web/"
echo ""
echo "2. Or use the deployment script:"
echo "   ./deploy_web.sh"
echo ""
