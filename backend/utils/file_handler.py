import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional, BinaryIO
from PIL import Image
import pypdf
import pdfplumber

class FileHandler:
    """Handle file upload and content extraction"""

    @staticmethod
    async def save_file(file_data: bytes, filename: str, upload_dir: Path) -> str:
        """Save uploaded file and return file_id"""
        file_id = str(uuid.uuid4())
        ext = Path(filename).suffix
        new_filename = f"{file_id}{ext}"
        file_path = upload_dir / new_filename

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data)

        return file_id

    @staticmethod
    def get_file_path(file_id: str, upload_dir: Path) -> Optional[Path]:
        """Get file path by file_id"""
        for ext in ['', '.txt', '.md', '.pdf', '.jpg', '.png', '.gif', '.webp', '.json', '.xml', '.csv']:
            path = upload_dir / f"{file_id}{ext}"
            if path.exists():
                return path
        return None

    @staticmethod
    async def extract_text_content(file_path: Path) -> str:
        """Extract text content from file"""
        ext = file_path.suffix.lower()

        if ext in ['.txt', '.md', '.json', '.xml', '.csv', '.py', '.js', '.html', '.css']:
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return await f.read()

        elif ext == '.pdf':
            return await FileHandler._extract_pdf_text(file_path)

        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            return await FileHandler._extract_image_text(file_path)

        else:
            return f"[File content not extractable: {ext}]"

    @staticmethod
    async def _extract_pdf_text(file_path: Path) -> str:
        """Extract text from PDF"""
        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n\n".join(text_parts) if text_parts else "[No text found in PDF]"
        except Exception as e:
            return f"[PDF extraction error: {str(e)}]"

    @staticmethod
    async def _extract_image_text(file_path: Path) -> str:
        """Extract text from image using OCR"""
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False)
            result = ocr.ocr(str(file_path))
            if result and result[0]:
                texts = [line[1][0] for line in result[0]]
                return "\n".join(texts)
            return "[No text found in image]"
        except ImportError:
            return "[OCR not available, please install paddlepaddle and paddleocr]"
        except Exception as e:
            return f"[OCR error: {str(e)}]"

    @staticmethod
    def get_file_type(filename: str) -> str:
        """Get file type category"""
        ext = Path(filename).suffix.lower()
        type_map = {
            '.jpg': 'image', '.jpeg': 'image', '.png': 'image',
            '.gif': 'image', '.webp': 'image',
            '.txt': 'text', '.md': 'text', '.json': 'text',
            '.xml': 'text', '.csv': 'text',
            '.pdf': 'document',
            '.py': 'code', '.js': 'code', '.ts': 'code',
            '.html': 'code', '.css': 'code',
        }
        return type_map.get(ext, 'other')
