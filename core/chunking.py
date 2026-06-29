"""Semantic chunking of resume text."""

from typing import List, Dict, Any
import re


class ChunkingEngine:
    """Performs semantic chunking of text."""
    
    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 100):
        """
        Initialize chunking engine.
        
        Args:
            chunk_size: Target size for each chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """Split text into sentences."""
        # Handle common sentence endings and abbreviations
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def split_into_paragraphs(text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
    
    def chunk_text(self, text: str, candidate_name: str = "", 
                   email: str = "", phone: str = "") -> List[Dict[str, Any]]:
        """
        Perform semantic chunking on text.
        
        Args:
            text: Text to chunk
            candidate_name: Name of candidate for metadata
            email: Email for metadata
            phone: Phone for metadata
            
        Returns:
            List of chunks with metadata
        """
        chunks = []
        
        # Split into paragraphs first
        paragraphs = self.split_into_paragraphs(text)
        
        # Combine paragraphs into chunks
        current_chunk = ""
        chunk_id = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, save current chunk
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                # Save chunk
                chunk_obj = self._create_chunk_object(
                    current_chunk, chunk_id, candidate_name, email, phone
                )
                chunks.append(chunk_obj)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                current_chunk = overlap_text + paragraph
                chunk_id += 1
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add final chunk
        if current_chunk:
            chunk_obj = self._create_chunk_object(
                current_chunk, chunk_id, candidate_name, email, phone
            )
            chunks.append(chunk_obj)
        
        return chunks
    
    @staticmethod
    def _get_overlap_text(text: str, overlap_size: int) -> str:
        """Get the last `overlap_size` characters from text."""
        if len(text) <= overlap_size:
            return text
        
        # Try to break at sentence boundary for cleaner overlap
        last_sentence_end = text.rfind('.', len(text) - overlap_size - 50, len(text))
        if last_sentence_end > len(text) - overlap_size - 50:
            return text[last_sentence_end + 1:].strip()
        
        return text[-overlap_size:]
    
    @staticmethod
    def _create_chunk_object(text: str, chunk_id: int, candidate_name: str = "",
                            email: str = "", phone: str = "") -> Dict[str, Any]:
        """Create a chunk object with metadata."""
        return {
            'id': chunk_id,
            'text': text,
            'metadata': {
                'candidate_name': candidate_name,
                'email': email,
                'phone': phone,
                'chunk_size': len(text)
            }
        }
    
    def chunk_by_sections(self, text: str, candidate_name: str = "",
                         email: str = "", phone: str = "") -> List[Dict[str, Any]]:
        """
        Chunk text by identifying sections (Experience, Education, Skills, etc).
        
        Args:
            text: Text to chunk
            candidate_name: Name of candidate
            email: Email for metadata
            phone: Phone for metadata
            
        Returns:
            List of chunks organized by sections
        """
        chunks = []
        
        # Define section headers
        section_patterns = [
            (r'(EXPERIENCE|PROFESSIONAL|WORK HISTORY)', 'experience'),
            (r'(EDUCATION|ACADEMIC)', 'education'),
            (r'(SKILLS|TECHNICAL)', 'skills'),
            (r'(PROJECTS|PORTFOLIO)', 'projects'),
            (r'(CERTIFICATIONS|AWARDS)', 'certifications'),
            (r'(SUMMARY|OBJECTIVE|PROFILE)', 'summary'),
        ]
        
        # Split by sections
        sections = []
        current_pos = 0
        
        for pattern, section_name in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Add text before section as general section
                if current_pos < match.start() and match.start() - current_pos > 50:
                    sections.append({
                        'name': 'general',
                        'text': text[current_pos:match.start()]
                    })
                
                # Find end of this section (next section or end of text)
                next_match = None
                for next_pattern, next_section in section_patterns:
                    if next_pattern == pattern:
                        continue
                    next_match_obj = re.search(next_pattern, text[match.end():], re.IGNORECASE)
                    if next_match_obj:
                        next_match = match.end() + next_match_obj.start()
                        break
                
                section_end = next_match if next_match else len(text)
                sections.append({
                    'name': section_name,
                    'text': text[match.start():section_end]
                })
                current_pos = section_end
        
        # Add remaining text
        if current_pos < len(text):
            sections.append({
                'name': 'other',
                'text': text[current_pos:]
            })
        
        # Create chunks from sections
        chunk_id = 0
        for section in sections:
            section_text = section['text'].strip()
            if not section_text:
                continue
            
            # If section is small, keep it as single chunk
            if len(section_text) <= self.chunk_size:
                chunk_obj = {
                    'id': chunk_id,
                    'text': section_text,
                    'metadata': {
                        'candidate_name': candidate_name,
                        'email': email,
                        'phone': phone,
                        'section': section['name'],
                        'chunk_size': len(section_text)
                    }
                }
                chunks.append(chunk_obj)
                chunk_id += 1
            else:
                # Split large section into smaller chunks
                section_chunks = self.chunk_text(section_text, candidate_name, email, phone)
                for s_chunk in section_chunks:
                    s_chunk['id'] = chunk_id
                    s_chunk['metadata']['section'] = section['name']
                    chunks.append(s_chunk)
                    chunk_id += 1
        
        return chunks
