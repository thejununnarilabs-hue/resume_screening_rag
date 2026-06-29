"""PDF parsing and text extraction functionality."""

import os
import PyPDF2
from pathlib import Path
from typing import Tuple, Optional


class PDFParser:
    """Handles PDF parsing and text extraction."""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """
        Extract all text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            text_content = []
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            
            return "\n".join(text_content)
        
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_path}: {e}")
            return ""
    
    @staticmethod
    def extract_text_with_metadata(pdf_path: str) -> Tuple[str, dict]:
        """
        Extract text and metadata from PDF.
        
        Returns:
            Tuple of (text_content, metadata_dict)
        """
        try:
            metadata = {}
            text_content = []
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract metadata
                if pdf_reader.metadata:
                    metadata = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                    }
                
                metadata['num_pages'] = len(pdf_reader.pages)
                
                # Extract text
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            
            full_text = "\n".join(text_content)
            return full_text, metadata
        
        except Exception as e:
            print(f"Error extracting text with metadata from {pdf_path}: {e}")
            return "", {}
    
    @staticmethod
    def get_file_info(pdf_path: str) -> dict:
        """Get file information without extracting text."""
        try:
            file_stat = Path(pdf_path).stat()
            
            info = {
                'filename': Path(pdf_path).name,
                'file_size': file_stat.st_size,
                'created': file_stat.st_ctime,
                'modified': file_stat.st_mtime
            }
            
            # Try to get page count
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    info['num_pages'] = len(pdf_reader.pages)
            except:
                info['num_pages'] = 0
            
            return info
        
        except Exception as e:
            print(f"Error getting file info: {e}")
            return {}
