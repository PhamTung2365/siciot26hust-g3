#!/bin/bash

# ==================== SMART LOCK SETUP ====================
# Create directory structure and initialize project

set -e  # Exit on error

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Project directory: $PROJECT_DIR"

# ==================== CREATE DIRECTORIES ====================
echo ""
echo "📂 Creating directories..."
mkdir -p "$PROJECT_DIR/faces_db"
mkdir -p "$PROJECT_DIR/captures"
mkdir -p "$PROJECT_DIR/data"

echo "✓ Directories created"

# ==================== CREATE VIRTUAL ENV ====================
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo ""
    echo "🐍 Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/venv"
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# ==================== ACTIVATE VENV ====================
echo ""
echo "📦 Activating virtual environment..."
source "$PROJECT_DIR/venv/bin/activate"
echo "✓ Virtual environment activated"

# ==================== INSTALL DEPENDENCIES ====================
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip setuptools wheel > /dev/null
pip install -r "$PROJECT_DIR/requirements.txt"
echo "✓ Dependencies installed"

# ==================== SUMMARY ====================
echo ""
echo "============================================================"
echo "✅ SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "📁 Structure:"
echo "   $PROJECT_DIR/"
echo "   ├── venv/              (Python environment)"
echo "   ├── faces_db/          (Face database)"
echo "   ├── captures/          (Captured images)"
echo "   ├── data/              (User database)"
echo "   ├── face_utils.py      (Model inference)"
echo "   ├── face_db.py         (Database logic)"
echo "   ├── web_stream_face.py (Flask server)"
echo "   ├── requirements.txt   (Dependencies)"
echo "   ├── README.md          (Documentation)"
echo "   └── setup.sh           (This script)"
echo ""
echo "🚀 Quick Start:"
echo "   cd $PROJECT_DIR"
echo "   cp .env.example .env  # Set admin credentials first"
echo "   source venv/bin/activate"
echo "   python3 web_stream_face.py"
echo ""
echo "🌐 Then open:"
echo "   http://localhost:5000"
echo ""
echo "============================================================"
