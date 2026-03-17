#!/bin/bash
# SULV Email + KB Skill App - Setup Script

set -e

echo "========================================="
echo "SULV Email + KB Skill App Setup"
echo "========================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python $PYTHON_VERSION detected"

# Check directory structure
echo "Checking project structure..."
if [ ! -d "src/skill" ]; then
    echo "❌ Skill directory not found"
    exit 1
fi

if [ ! -d "src/kb" ]; then
    echo "❌ KB directory not found"
    exit 1
fi

if [ ! -d "src/tests" ]; then
    echo "❌ Tests directory not found"
    exit 1
fi

echo "✓ Project structure looks good"

# Create necessary directories
echo "Creating working directories..."
mkdir -p logs data/{emails,attachments,kb_processed} config

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip

if [ -f "src/kb/requirements.txt" ]; then
    echo "Installing KB dependencies..."
    pip install -r src/kb/requirements.txt
fi

# Make scripts executable
echo "Making scripts executable..."
chmod +x src/tests/run_full_test_suite.sh 2>/dev/null || true
chmod +x setup.sh

# Run initial test
echo "Running initial system check..."
python3 src/tests/check_test_status.py

echo ""
echo "========================================="
echo "Setup Complete! 🎉"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Review the README.md for usage instructions"
echo "2. Run tests: ./src/tests/run_full_test_suite.sh"
echo "3. Check status: python src/tests/check_test_status.py"
echo ""
echo "For SULV project deployment:"
echo "- Set up Google Workspace credentials"
echo "- Configure environment variables"
echo "- Test with real email data"
echo ""
echo "Ready for SULV project automation! 🦞"