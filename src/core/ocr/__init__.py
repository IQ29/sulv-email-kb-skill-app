"""
OCR (Optical Character Recognition) for extracting text from images and PDFs.
Uses Tesseract with optimizations for document processing.
"""

import logging
import tempfile
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
import subprocess
import shutil

logger = logging.getLogger(__name__)


class OCRProcessor:
    """OCR processor for extracting text from images and scanned PDFs."""
    
    def __init__(self, tesseract_path: Optional[str] = None, language: str = "eng"):
        """
        Initialize OCR processor.
        
        Args:
            tesseract_path: Path to tesseract executable (auto-detected if None)
            language: OCR language code (eng, chi_sim, etc.)
        """
        self.tesseract_path = tesseract_path or self._find_tesseract()
        self.language = language
        self.supported_formats = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.pdf']
        
        if not self.tesseract_path:
            logger.warning("Tesseract not found. OCR will be disabled.")
    
    def _find_tesseract(self) -> Optional[str]:
        """Find tesseract executable path."""
        # Common paths (including miniforge installation)
        common_paths = [
            '/usr/local/Caskroom/miniforge/base/bin/tesseract',  # Miniforge installation
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract',
            'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
            shutil.which('tesseract')
        ]
        
        for path in common_paths:
            if path and Path(path).exists():
                logger.info(f"Found tesseract at: {path}")
                return path
        
        return None
    
    def is_available(self) -> bool:
        """Check if OCR is available."""
        return self.tesseract_path is not None
    
    def extract_text(self, file_path: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from an image or PDF file.
        
        Args:
            file_path: Path to the file
            **kwargs: Additional OCR parameters
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        if not self.is_available():
            return "", {"error": "OCR not available", "success": False}
        
        file_path = Path(file_path)
        if not file_path.exists():
            return "", {"error": f"File not found: {file_path}", "success": False}
        
        if file_path.suffix.lower() not in self.supported_formats:
            return "", {"error": f"Unsupported format: {file_path.suffix}", "success": False}
        
        try:
            if file_path.suffix.lower() == '.pdf':
                return self._process_pdf(file_path, **kwargs)
            else:
                return self._process_image(file_path, **kwargs)
        except Exception as e:
            logger.error(f"OCR processing failed for {file_path}: {e}")
            return "", {"error": str(e), "success": False}
    
    def _process_image(self, image_path: Path, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Process a single image file."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            output_path = tmp_file.name
        
        try:
            # Build tesseract command
            cmd = [
                self.tesseract_path,
                str(image_path),
                output_path[:-4],  # Remove .txt suffix
                '-l', self.language,
                '--oem', '1',  # LSTM engine
                '--psm', '3'   # Fully automatic page segmentation
            ]
            
            # Add custom config if provided
            if 'config' in kwargs:
                cmd.extend(kwargs['config'])
            
            # Run tesseract
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                return "", {
                    "error": f"Tesseract failed: {result.stderr}",
                    "success": False,
                    "returncode": result.returncode
                }
            
            # Read output
            with open(output_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Clean up
            Path(output_path).unlink()
            
            return text, {
                "success": True,
                "language": self.language,
                "engine": "tesseract",
                "file_size": image_path.stat().st_size,
                "characters_extracted": len(text)
            }
            
        except subprocess.TimeoutExpired:
            return "", {"error": "OCR timeout", "success": False}
        finally:
            # Ensure temp file is cleaned up
            if Path(output_path).exists():
                Path(output_path).unlink()
    
    def _process_pdf(self, pdf_path: Path, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Process a PDF file (may contain scanned pages)."""
        try:
            # First, try to extract text directly (for text-based PDFs)
            direct_text, has_text = self._extract_pdf_text_directly(pdf_path)
            
            if has_text and len(direct_text.strip()) > 100:
                # PDF has sufficient text content, use it
                return direct_text, {
                    "success": True,
                    "method": "direct_extraction",
                    "file_size": pdf_path.stat().st_size,
                    "characters_extracted": len(direct_text),
                    "note": "Text-based PDF, no OCR needed"
                }
            
            # PDF is scanned or has little text, use OCR
            return self._ocr_pdf_pages(pdf_path, **kwargs)
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return "", {"error": str(e), "success": False}
    
    def _extract_pdf_text_directly(self, pdf_path: Path) -> Tuple[str, bool]:
        """Extract text directly from PDF (for text-based PDFs)."""
        try:
            # Try PyMuPDF first (faster)
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(str(pdf_path))
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                return text, True
            except ImportError:
                pass
            
            # Fallback to pdfplumber
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                return text, True
            except ImportError:
                pass
            
            # No PDF library available
            return "", False
            
        except Exception as e:
            logger.debug(f"Direct PDF extraction failed: {e}")
            return "", False
    
    def _ocr_pdf_pages(self, pdf_path: Path, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """OCR each page of a PDF."""
        try:
            # Convert PDF to images first
            images = self._pdf_to_images(pdf_path)
            if not images:
                return "", {"error": "Failed to convert PDF to images", "success": False}
            
            # OCR each image
            all_text = []
            metadata = {
                "success": True,
                "method": "ocr",
                "pages": len(images),
                "file_size": pdf_path.stat().st_size,
                "language": self.language,
                "engine": "tesseract"
            }
            
            for i, image_path in enumerate(images):
                page_text, page_meta = self._process_image(image_path, **kwargs)
                if page_meta.get('success'):
                    all_text.append(f"--- Page {i+1} ---\n{page_text}\n")
                
                # Clean up temp image
                if Path(image_path).exists():
                    Path(image_path).unlink()
            
            full_text = "\n".join(all_text)
            metadata["characters_extracted"] = len(full_text)
            metadata["pages_processed"] = len(images)
            
            return full_text, metadata
            
        except Exception as e:
            logger.error(f"PDF OCR failed: {e}")
            return "", {"error": str(e), "success": False}
    
    def _pdf_to_images(self, pdf_path: Path) -> List[str]:
        """Convert PDF pages to images for OCR."""
        try:
            # Try pdf2image first
            try:
                from pdf2image import convert_from_path
                import tempfile
                
                temp_dir = tempfile.mkdtemp()
                images = convert_from_path(
                    str(pdf_path),
                    output_folder=temp_dir,
                    fmt='png',
                    thread_count=2
                )
                
                image_paths = []
                for i, image in enumerate(images):
                    image_path = Path(temp_dir) / f"page_{i+1}.png"
                    image.save(image_path, 'PNG')
                    image_paths.append(str(image_path))
                
                return image_paths
                
            except ImportError:
                logger.warning("pdf2image not installed. Install with: pip install pdf2image")
                pass
            
            # Fallback: Use PyMuPDF to extract images
            try:
                import fitz
                import tempfile
                from PIL import Image
                import io
                
                temp_dir = tempfile.mkdtemp()
                doc = fitz.open(str(pdf_path))
                image_paths = []
                
                for i in range(len(doc)):
                    page = doc.load_page(i)
                    pix = page.get_pixmap()
                    
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    image_path = Path(temp_dir) / f"page_{i+1}.png"
                    img.save(image_path)
                    image_paths.append(str(image_path))
                
                doc.close()
                return image_paths
                
            except ImportError:
                logger.warning("PyMuPDF or PIL not installed for PDF conversion")
                pass
            
            return []
            
        except Exception as e:
            logger.error(f"PDF to image conversion failed: {e}")
            return []


class OCRFactory:
    """Factory for OCR processors."""
    
    @staticmethod
    def create_processor(engine: str = "tesseract", **kwargs) -> OCRProcessor:
        """
        Create an OCR processor.
        
        Args:
            engine: OCR engine ("tesseract" only for now)
            **kwargs: Engine-specific parameters
            
        Returns:
            OCRProcessor instance
        """
        if engine == "tesseract":
            return OCRProcessor(**kwargs)
        else:
            raise ValueError(f"Unsupported OCR engine: {engine}")
    
    @staticmethod
    def get_supported_languages() -> List[str]:
        """Get list of supported OCR languages."""
        # Common languages supported by Tesseract
        return [
            "eng",  # English
            "chi_sim",  # Chinese Simplified
            "chi_tra",  # Chinese Traditional
            "fra",  # French
            "deu",  # German
            "jpn",  # Japanese
            "kor",  # Korean
            "spa",  # Spanish
            "rus",  # Russian
            "ara",  # Arabic
        ]


# Test the OCR module
if __name__ == "__main__":
    import sys
    
    print("Testing OCR module...")
    
    # Create OCR processor
    ocr = OCRFactory.create_processor(language="eng")
    
    if not ocr.is_available():
        print("❌ Tesseract not found. Install with: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)")
        sys.exit(1)
    
    print("✅ OCR is available")
    print(f"  Tesseract path: {ocr.tesseract_path}")
    print(f"  Language: {ocr.language}")
    print(f"  Supported formats: {ocr.supported_formats}")
    
    # Test with a sample (would need actual image file)
    print("\nNote: To test OCR, provide an image or PDF file path.")
    print("Example usage:")
    print("  text, metadata = ocr.extract_text('/path/to/document.pdf')")
    print("  if metadata['success']:")
    print("      print(f'Extracted {len(text)} characters')")