#!/usr/bin/env bash
# Setup script for Google Takeout Metadata Embedder

set -e  # Exit on error

echo "🚀 Setting up Google Takeout Metadata Embedder..."
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3: https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check for exiftool
if ! command -v exiftool &> /dev/null; then
    echo "❌ Error: exiftool is not installed"
    echo ""
    echo "Install exiftool:"
    echo "  macOS:   brew install exiftool"
    echo "  Linux:   sudo apt install libimage-exiftool-perl"
    echo "  Windows: Download from https://exiftool.org/"
    exit 1
fi

echo "✓ exiftool found: version $(exiftool -ver)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment and install dependencies
echo ""
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "✓ Dependencies installed"
echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the tool:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  python main.py"
