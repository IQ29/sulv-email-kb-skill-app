#!/usr/bin/env python3
"""
Test PDF content to see if it's text-based or scanned.
"""

import sys
from pathlib import Path

print("🔍 TESTING PDF CONTENT")
print("=" * 50)

# Check PDF files
pdf_dir = Path("attachments_downloaded")
pdf_files = list(pdf_dir.glob("*.pdf"))

print(f"Found {len(pdf_files)} PDF files")

for pdf_file in pdf_files:
    print(f"\n📄 Testing: {pdf_file.name}")
    print(f"  Size: {pdf_file.stat().st_size:,} bytes")
    
    try:
        import fitz
        
        doc = fitz.open(str(pdf_file))
        print(f"  Pages: {len(doc)}")
        
        if len(doc) > 0:
            # Try to extract text
            text = ""
            for i in range(min(2, len(doc))):  # Check first 2 pages
                page = doc[i]
                page_text = page.get_text()
                if page_text:
                    text += page_text
            
            if text and len(text.strip()) > 100:  # Reasonable amount of text
                print(f"  ✅ Text-based PDF")
                print(f"  📝 Text sample: {text[:200]}...")
                print(f"  📏 Total text: {len(text):,} characters")
            else:
                print(f"  🔍 Scanned/image PDF (needs OCR)")
                print(f"  📷 Will use Tesseract OCR")
                
                # Check if it's actually an image
                page = doc[0]
                pix = page.get_pixmap()
                print(f"  🖼️  Image dimensions: {pix.width} x {pix.height}")
                
        else:
            print(f"  ⚠️  PDF has 0 pages (might be corrupted)")
        
        doc.close()
        
    except ImportError:
        print("  ❌ PyMuPDF not available")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "=" * 50)
print("🎯 CONCLUSION:")
print("If PDFs are text-based: Direct text extraction")
print("If PDFs are scanned: OCR processing with Tesseract")
print("\nThe KB system handles both automatically!")