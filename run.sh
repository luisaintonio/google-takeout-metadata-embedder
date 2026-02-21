#!/usr/bin/env bash
# Run script for Google Takeout Metadata Embedder

set -e  # Exit on error

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment and run
source venv/bin/activate
python main.py
