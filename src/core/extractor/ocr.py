"""
Unified OCR Engine - Extracts text from medical documents using multiple strategies.

Supports: PDF, PNG, JPG, JPEG
Strategy Order: pdfplumber (PDF) → pdf2image+tesseract → OCR.space API fallback

Features:
- 6 preprocessing strategies for challenging images
- Confidence scoring across all attempts
- Async-compatible (uses run_in_executor for blocking I/O)
- Automatic fallback between providers
"""

import asyncio
import base64
import io
import os
import tempfile
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, Tuple
from enum import Enum

import cv2
import numpy as np
import pdfplumber
import pytesseract
import requests
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

# Set Tesseract path for Windows
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class OCRError(Exception):
    """Custom exception for OCR processing failures."""
    
    def __init__(self, message: str, file_type: str = "unknown"):
        self.message = message
        self.file_type = file_type
        super().__init__(f"OCR Error [{file_type}]: {message}")


class OCRStrategy(Enum):
    """Enumeration of OCR strategies."""
    PDFPLUMBER = "pdfplumber"
    PDF_TESSERACT = "pdf_tesseract"
    TESSERACT = "tesseract"
    OCR_SPACE_API = "ocr_space_api"


class OCREngine:
    """
    Unified OCR Engine for medical document processing.
    
    Combines local Tesseract OCR with cloud API fallback (OCR.space).
    Supports PDF, PNG, JPG, JPEG formats with 6 preprocessing strategies.
    """
    
    def __init__(self, timeout: int = 30, executor: Optional[ThreadPoolExecutor] = None):
        """
        Initialize OCREngine.
        
        Args:
            timeout: HTTP request timeout in seconds
            executor: ThreadPoolExecutor for async I/O (creates new if None)
        """
        self.timeout = timeout
        self.executor = executor or ThreadPoolExecutor(max_workers=4)
        self.ocr_space_api_key = os.getenv("OCR_SPACE_API_KEY", "")
        
        # Preprocessing strategies (6 total)
        self.preprocessing_strategies = [
            'standard',
            'high_contrast',
            'denoised',
            'sharpened',
            'morphological',
            'adaptive_bilateral'
        ]
        
        # Tesseract configurations for different scenarios
        self.tesseract_configs = [
            r'--oem 3 --psm 6 -l eng -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,-/():% ',
            r'--oem 3 --psm 4 -l eng',
            r'--oem 3 --psm 8 -l eng',
            r'--oem 3 --psm 3 -l eng',
            r'--oem 3 --psm 7 -l eng',
            r'--oem 3 --psm 13 -l eng',
        ]
        
        self.min_confidence_threshold = 0.2
        self.min_text_length = 5
    
    async def extract(self, file_bytes: bytes, file_type: str) -> str:
        """
        Extract text from file bytes.
        
        Args:
            file_bytes: Raw file content
            file_type: File type ('pdf', 'png', 'jpg', 'jpeg')
            
        Returns:
            Extracted text as string
            
        Raises:
            OCRError: If extraction fails completely
        """
        file_type = file_type.lower().strip('.')
        
        if file_type not in ['pdf', 'png', 'jpg', 'jpeg']:
            raise OCRError(
                f"Unsupported file type: {file_type}. Supported: pdf, png, jpg, jpeg",
                file_type
            )
        
        try:
            if file_type == 'pdf':
                return await self._extract_from_pdf(file_bytes)
            else:
                return await self._extract_from_image(file_bytes, file_type)
        except OCRError:
            raise
        except Exception as e:
            raise OCRError(f"Unexpected error during extraction: {str(e)}", file_type)
    
    async def _extract_from_pdf(self, file_bytes: bytes) -> str:
        """
        Extract text from PDF using strategy order:
        1. pdfplumber (text-based PDF)
        2. pdf2image + tesseract (scanned PDF)
        3. OCR.space API (fallback)
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name
        
        try:
            # Strategy 1: Try pdfplumber for text-based PDFs
            text = await self._extract_pdf_pdfplumber(temp_path)
            if text and len(text.strip()) >= self.min_text_length:
                return text
            
            # Strategy 2: pdf2image + tesseract for scanned PDFs
            text = await self._extract_pdf_tesseract(temp_path)
            if text and len(text.strip()) >= self.min_text_length:
                return text
            
            # Strategy 3: OCR.space API fallback
            if self.ocr_space_api_key:
                text = await self._extract_with_ocr_space(file_bytes, 'pdf')
                if text and len(text.strip()) >= self.min_text_length:
                    return text
            
            raise OCRError("All PDF extraction strategies failed", "pdf")
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    async def _extract_from_image(self, file_bytes: bytes, file_type: str) -> str:
        """
        Extract text from image using strategy order:
        1. Local Tesseract with all preprocessing strategies + configs
        2. OCR.space API fallback
        """
        try:
            image = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: Image.open(io.BytesIO(file_bytes))
            )
        except Exception as e:
            raise OCRError(f"Failed to load image: {str(e)}", file_type)
        
        # Strategy 1: Local Tesseract with preprocessing
        results = await self._extract_with_tesseract_strategies(image)
        if results and results['text'] and len(results['text'].strip()) >= self.min_text_length:
            return results['text']
        
        # Strategy 2: OCR.space API fallback
        if self.ocr_space_api_key:
            text = await self._extract_with_ocr_space(file_bytes, file_type)
            if text and len(text.strip()) >= self.min_text_length:
                return text
        
        raise OCRError("All image extraction strategies failed", file_type)
    
    async def _extract_pdf_pdfplumber(self, pdf_path: str) -> str:
        """Extract text from text-based PDF using pdfplumber."""
        try:
            def extract():
                text = ""
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text.strip()
            
            return await asyncio.get_event_loop().run_in_executor(self.executor, extract)
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return ""
    
    async def _extract_pdf_tesseract(self, pdf_path: str) -> str:
        """Extract text from scanned PDF using pdf2image + tesseract."""
        try:
            def extract():
                combined_text = ""
                pages = convert_from_path(pdf_path, dpi=300)
                
                for page_num, page_image in enumerate(pages):
                    text = pytesseract.image_to_string(page_image, config=self.tesseract_configs[0])
                    if text.strip():
                        combined_text += f"--- Page {page_num + 1} ---\n{text}\n"
                
                return combined_text.strip()
            
            return await asyncio.get_event_loop().run_in_executor(self.executor, extract)
        except Exception as e:
            logger.warning(f"pdf2image+tesseract extraction failed: {e}")
            return ""
    
    async def _extract_with_tesseract_strategies(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extract with all 6 preprocessing strategies and multiple Tesseract configs.
        Returns best result by confidence scoring.
        """
        def extract_sync():
            best_result = None
            best_confidence = 0
            all_results = []
            
            for strategy in self.preprocessing_strategies:
                try:
                    preprocessed = self._preprocess_image(image, strategy)
                    
                    for config in self.tesseract_configs:
                        try:
                            text = pytesseract.image_to_string(preprocessed, config=config)
                            
                            if not text.strip():
                                continue
                            
                            # Calculate confidence
                            ocr_data = pytesseract.image_to_data(
                                preprocessed,
                                config=config,
                                output_type=pytesseract.Output.DICT
                            )
                            
                            confidences = [int(c) for c in ocr_data['conf'] if int(c) > 0]
                            avg_confidence = (
                                sum(confidences) / len(confidences) / 100.0 
                                if confidences else 0.5
                            )
                            
                            result = {
                                'text': text.strip(),
                                'confidence': avg_confidence,
                                'strategy': strategy,
                                'config_idx': self.tesseract_configs.index(config)
                            }
                            
                            all_results.append(result)
                            
                            if len(text.strip()) > 10 and avg_confidence > best_confidence:
                                best_confidence = avg_confidence
                                best_result = result
                        
                        except Exception:
                            continue
                
                except Exception:
                    continue
            
            # Return best result or highest confidence available
            if best_result:
                return best_result
            elif all_results:
                all_results.sort(
                    key=lambda x: (len(x['text']), x['confidence']),
                    reverse=True
                )
                return all_results[0]
            else:
                return {'text': '', 'confidence': 0, 'strategy': 'none', 'config_idx': -1}
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, extract_sync)
    
    async def _extract_with_ocr_space(self, file_bytes: bytes, file_type: str) -> str:
        """
        Extract text using OCR.space API (fallback).
        
        Free tier: 500 requests/day, max 1MB
        """
        if not self.ocr_space_api_key:
            return ""
        
        try:
            # Convert to base64
            img_base64 = base64.b64encode(file_bytes).decode('utf-8')
            
            payload = {
                'apikey': self.ocr_space_api_key,
                'base64Image': f'data:image/{file_type};base64,{img_base64}',
                'language': 'eng',
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'OCREngine': 2
            }
            
            def call_api():
                response = requests.post(
                    'https://api.ocr.space/parse/image',
                    data=payload,
                    timeout=self.timeout
                )
                return response.json()
            
            result = await asyncio.get_event_loop().run_in_executor(self.executor, call_api)
            
            if result.get('IsErroredOnProcessing'):
                logger.warning(f"OCR.space API error: {result.get('ErrorMessage')}")
                return ""
            
            parsed_results = result.get('ParsedResults', [])
            if parsed_results:
                return parsed_results[0].get('ParsedText', '').strip()
            
            return ""
        
        except Exception as e:
            logger.warning(f"OCR.space API call failed: {e}")
            return ""
    
    def _preprocess_image(self, image: Image.Image, strategy: str) -> Image.Image:
        """Apply preprocessing strategy to image."""
        if strategy == 'standard':
            return self._preprocess_standard(image)
        elif strategy == 'high_contrast':
            return self._preprocess_high_contrast(image)
        elif strategy == 'denoised':
            return self._preprocess_denoised(image)
        elif strategy == 'sharpened':
            return self._preprocess_sharpened(image)
        elif strategy == 'morphological':
            return self._preprocess_morphological(image)
        elif strategy == 'adaptive_bilateral':
            return self._preprocess_adaptive_bilateral(image)
        else:
            return self._preprocess_standard(image)
    
    def _preprocess_standard(self, image: Image.Image) -> Image.Image:
        """Standard preprocessing: bilateral filter + adaptive threshold."""
        img_array = np.array(image.convert('L'))
        
        denoised = cv2.bilateralFilter(img_array, 9, 75, 75)
        
        adaptive_thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return Image.fromarray(adaptive_thresh)
    
    def _preprocess_high_contrast(self, image: Image.Image) -> Image.Image:
        """High contrast: for faded images."""
        img_array = np.array(image.convert('L'))
        
        equalized = cv2.equalizeHist(img_array)
        
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(equalized)
        
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return Image.fromarray(thresh)
    
    def _preprocess_denoised(self, image: Image.Image) -> Image.Image:
        """Heavy denoising: for noisy images."""
        img_array = np.array(image.convert('L'))
        
        denoised1 = cv2.fastNlMeansDenoising(img_array, None, 10, 7, 21)
        denoised2 = cv2.bilateralFilter(denoised1, 15, 80, 80)
        
        adaptive_thresh = cv2.adaptiveThreshold(
            denoised2, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY, 15, 8
        )
        
        return Image.fromarray(adaptive_thresh)
    
    def _preprocess_sharpened(self, image: Image.Image) -> Image.Image:
        """Sharpening: for blurry images."""
        img_array = np.array(image.convert('L'))
        
        gaussian = cv2.GaussianBlur(img_array, (0, 0), 2.0)
        sharpened = cv2.addWeighted(img_array, 1.5, gaussian, -0.5, 0)
        
        adaptive_thresh = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return Image.fromarray(adaptive_thresh)
    
    def _preprocess_morphological(self, image: Image.Image) -> Image.Image:
        """Morphological operations: for text cleanup."""
        img_array = np.array(image.convert('L'))
        
        _, thresh = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        return Image.fromarray(closing)
    
    def _preprocess_adaptive_bilateral(self, image: Image.Image) -> Image.Image:
        """Adaptive bilateral filtering: multiple passes."""
        img_array = np.array(image.convert('L'))
        
        filtered1 = cv2.bilateralFilter(img_array, 5, 50, 50)
        filtered2 = cv2.bilateralFilter(filtered1, 9, 75, 75)
        filtered3 = cv2.bilateralFilter(filtered2, 13, 100, 100)
        
        adaptive_thresh = cv2.adaptiveThreshold(
            filtered3, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 21, 10
        )
        
        return Image.fromarray(adaptive_thresh)
