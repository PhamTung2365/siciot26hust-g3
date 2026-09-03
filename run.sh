#!/bin/bash

# ==================== SMART LOCK RUN SCRIPT ====================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Authentication is intentionally configured by the deployer, never by a default password.
if [ ! -f ".env" ]; then
    echo "❌ Missing .env configuration"
    echo "Run: cp .env.example .env, then set the admin username, password, and secret."
    exit 1
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: bash setup.sh"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check if model is downloaded
if [ ! -d "$HOME/.insightface/models/buffalo_l" ]; then
    echo ""
    echo "📥 Downloading InsightFace model (first run)..."
    echo "This may take a few minutes..."
    echo ""
fi

# Run server
echo ""
echo "🚀 Starting Smart Lock server..."
echo ""
python3 web_stream_face.py
