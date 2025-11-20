#!/bin/bash

# Hyperliquid Dashboard Launcher
# This script sets up and runs the dashboard

echo "======================================"
echo "   Hyperliquid Trading Dashboard"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed!"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Check if requirements are installed
echo "Checking dependencies..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo "Dependencies already installed"
fi

echo ""
echo "Starting Hyperliquid Dashboard..."
echo "Dashboard will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
cd backend
python3 server.py
