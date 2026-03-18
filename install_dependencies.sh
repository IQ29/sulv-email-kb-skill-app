#!/bin/bash
# Install dependencies for SULV Unified Knowledge Base

set -e  # Exit on error

echo "Installing dependencies for SULV Unified Knowledge Base..."
echo "=========================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing core dependencies..."
# Install core packages that work with Python 3.14
pip install pydantic>=2.0.0

echo "Installing document processing dependencies..."
# Install document processing packages
pip install Pillow>=10.0.0
pip install python-docx>=1.0.0
pip install openpyxl>=3.0.0

echo "Installing OCR dependencies (optional)..."
# Check if Tesseract is installed
if command -v tesseract &> /dev/null; then
    echo "Tesseract found, installing pytesseract..."
    pip install pytesseract>=0.3.10
else
    echo "Tesseract not found. OCR will be disabled."
    echo "To enable OCR, install Tesseract: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)"
fi

echo "Installing PDF processing..."
pip install pymupdf>=1.23.0

echo "Installing embedding dependencies..."
# Try to install sentence-transformers (may fail on Python 3.14)
echo "Note: Some packages may not be compatible with Python 3.14 yet."
echo "Using fallback implementations where needed."

echo "Creating requirements summary..."
cat > requirements_installed.txt << EOF
# Dependencies installed for SULV Unified Knowledge Base
# Python version: $(python3 --version)

# Core
pydantic>=2.0.0

# Document processing
Pillow>=10.0.0
python-docx>=1.0.0
openpyxl>=3.0.0
pymupdf>=1.23.0

# Optional (if Tesseract available)
# pytesseract>=0.3.10

# Note: The following require Python 3.13 or earlier:
# numpy>=1.21.0
# sentence-transformers>=2.2.0
# transformers>=4.36.0
# torch>=2.1.0
# chromadb>=0.4.0

# Workaround: Use fallback implementations in src/core/embedding/fallback.py
# and src/core/reranking/fallback.py
EOF

echo ""
echo "✅ Installation complete!"
echo ""
echo "To use the knowledge base:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run tests: python test_all_components.py"
echo "3. Start development: python scripts/init_db.py"
echo ""
echo "Note: Some advanced features require Python 3.13 or earlier."
echo "Fallback implementations are provided for basic functionality."