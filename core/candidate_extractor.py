"""Candidate information extraction from resumes."""

import re
from typing import Dict, List, Optional
from .pdf_parser import PDFParser


class CandidateExtractor:
    """Extracts candidate information from resume text."""
    
    # Email pattern
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    PHONE_PATTERN = re.compile(
        r"""
        (?<![\w+])
        (?:
            \+\d{1,3}[\s.-]*(?:\d{10}|\d{5}[\s.-]?\d{5}|(?:\(\d{3}\)|\d{3})[\s.-]*\d{3}[\s.-]*\d{4})
            |
            (?:\(\d{3}\)|\d{3})[\s.-]*\d{3}[\s.-]*\d{4}
            |
            \d{5}[\s.-]\d{5}
            |
            \d{10}
        )
        (?!\d)
        """,
        re.VERBOSE,
    )

    URL_PATTERN = re.compile(
        r"(https?://\S+|www\.\S+|\S+\.(?:com|in|org|net|io|co)\S*)",
        re.IGNORECASE,
    )

    LOCATION_VALUE_PATTERN = re.compile(
        r"\b("
        r"india|usa|united states|uk|united kingdom|"
        r"tamil nadu|karnataka|kerala|maharashtra|delhi|telangana|andhra pradesh|"
        r"coimbatore|chennai|bengaluru|bangalore|hyderabad|mumbai|pune|noida|gurgaon|"
        r"kolkata|ahmedabad|jaipur|kochi|trivandrum"
        r")\b",
        re.IGNORECASE,
    )

    SECTION_HEADERS = {
        'summary', 'professional summary', 'profile', 'career objective', 'objective',
        'skills', 'technical skills', 'experience', 'professional experience',
        'work experience', 'employment history', 'projects', 'portfolio',
        'certifications', 'awards', 'contact', 'contact information',
        'personal details', 'education', 'academic', 'academics',
    }
    
    # Education keywords
    EDUCATION_KEYWORDS = {
        'B.S.', 'B.A.', 'B.Tech', 'Bachelor', 'BS', 'BA',
        'M.S.', 'M.A.', 'M.Tech', 'Master', 'MS', 'MA',
        'Ph.D.', 'PhD', 'Doctorate',
        'Associate', 'Diploma', 'Certificate',
        'Computer Science', 'Engineering', 'Information Technology',
        'Business', 'Management', 'Finance', 'Science', 'Arts'
    }

    DEGREE_PATTERN = re.compile(
        r"\b("
        r"B\.?\s?(?:Tech|E|Sc|S|A|Com|CA|BA|BA)|"
        r"M\.?\s?(?:Tech|E|Sc|S|A|Com|CA|BA)|"
        r"Bachelor(?:'s)?|Master(?:'s)?|MBA|MCA|BCA|BBA|"
        r"Ph\.?\s?D\.?|Doctorate|Diploma|Associate"
        r")\b",
        re.IGNORECASE,
    )

    INSTITUTION_PATTERN = re.compile(
        r"\b(university|college|institute|school|academy|technology|polytechnic)\b",
        re.IGNORECASE,
    )

    GRADUATION_YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
    GPA_PATTERN = re.compile(r"\b(?:CGPA|GPA)\s*[:\-]?\s*\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?\b", re.IGNORECASE)
    
    # Common skill keywords
    SKILL_KEYWORDS = {
        # Languages
        'Python', 'Java', 'C++', 'C#', 'JavaScript', 'TypeScript', 'Go', 'Rust',
        'Ruby', 'PHP', 'Swift', 'Kotlin', 'R', 'MATLAB', 'SQL', 'Scala',
        
        # Frameworks
        'Django', 'Flask', 'FastAPI', 'Spring', 'React', 'Angular', 'Vue',
        'Node.js', 'Express', 'TensorFlow', 'PyTorch', 'Keras',
        
        # Databases
        'MongoDB', 'PostgreSQL', 'MySQL', 'Redis', 'Elasticsearch', 'Cassandra',
        'Oracle', 'DynamoDB', 'Firebase',
        
        # Cloud
        'AWS', 'Azure', 'GCP', 'Google Cloud', 'Kubernetes', 'Docker',
        
        # ML/AI
        'Machine Learning', 'NLP', 'Deep Learning', 'RAG', 'LLM',
        'Transformer', 'BERT', 'GPT', 'Computer Vision', 'Neural Networks',
        
        # Other
        'Git', 'Linux', 'DevOps', 'CI/CD', 'REST API', 'GraphQL',
        'Agile', 'Scrum', 'Microservices', 'Docker', 'Kubernetes'
    }

    INVALID_NAME_TERMS = {
        'technical skills', 'skills', 'summary', 'professional summary',
        'career objective', 'objective', 'education', 'experience',
        'professional experience', 'work experience', 'projects',
        'certifications', 'certification', 'contact', 'contact information',
        'resume', 'curriculum vitae', 'profile', 'personal details',
        'employment history', 'work history', 'academic details'
    }
    
    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        """Extract email address from text."""
        match = re.search(CandidateExtractor.EMAIL_PATTERN, text)
        return match.group(0) if match else None
    
    @staticmethod
    def extract_phone(text: str) -> Optional[str]:
        """Extract a complete, display-ready phone number from resume text."""
        for match in CandidateExtractor.PHONE_PATTERN.finditer(text):
            phone = " ".join(match.group(0).strip().split())
            if CandidateExtractor.is_valid_phone(phone):
                return phone
        return None

    @staticmethod
    def is_valid_phone(phone: Optional[str]) -> bool:
        """Validate phone candidates before showing them in candidate tables."""
        if not phone:
            return False

        digits = re.sub(r"\D", "", phone)
        if phone.strip().startswith("+"):
            if digits.startswith("91"):
                return len(digits) == 12
            if digits.startswith("1"):
                return len(digits) == 11
            return 11 <= len(digits) <= 15

        return len(digits) == 10
    
    @staticmethod
    def extract_name_from_text(text: str) -> Optional[str]:
        """
        Extract candidate name from resume text.
        Typically appears at the beginning of the document.
        """
        lines = text.strip().split('\n')[:12]  # Check first page header area
        
        for line in lines:
            line = line.strip()
            if not CandidateExtractor.is_valid_candidate_name(line):
                continue

            # Look for lines that look like names (2-4 words, capitalized)
            if line and len(line) > 3 and len(line) < 60:
                words = line.split()
                if 2 <= len(words) <= 4:
                    if all(word[0].isupper() or word.lower() in ['de', 'van', 'von', 'jr', 'sr', 'iii'] 
                           for word in words if word):
                        return line
        
        return None

    @staticmethod
    def is_valid_candidate_name(name: Optional[str]) -> bool:
        """Return False for section headings, empty values, and generic resume text."""
        if not name:
            return False

        cleaned = ' '.join(str(name).strip().split())
        if not cleaned:
            return False

        lowered = cleaned.lower().strip(':.- ')
        if lowered in CandidateExtractor.INVALID_NAME_TERMS:
            return False

        if any(term == lowered or term in lowered for term in CandidateExtractor.INVALID_NAME_TERMS):
            return False

        if any(token in lowered for token in ['@', 'http', 'www.', 'linkedin', 'github', 'phone', 'email']):
            return False

        if re.search(r'\d', cleaned):
            return False

        words = cleaned.split()
        if not 2 <= len(words) <= 4:
            return False

        alpha_words = [re.sub(r"[^A-Za-z'.-]", '', word) for word in words]
        if any(len(word) < 2 for word in alpha_words):
            return False

        if cleaned.isupper() and lowered in CandidateExtractor.INVALID_NAME_TERMS:
            return False

        return True
    
    @staticmethod
    def extract_name_from_filename(filename: str) -> str:
        """
        Extract candidate name from filename.
        Removes .pdf and common separators.
        """
        name = filename.replace('.pdf', '').replace('.PDF', '')
        # Replace common separators with space
        name = re.sub(r'[_\-]', ' ', name)
        # Clean up spaces
        name = ' '.join(name.split())
        return name
    
    @staticmethod
    def extract_education(text: str) -> List[str]:
        """Extract only structured education information from text."""
        return CandidateExtractor.parse_education(text)

    @staticmethod
    def parse_education(text: str) -> List[str]:
        """Parse degree, institution, graduation year, and GPA lines only."""
        education = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        education_lines = CandidateExtractor._education_section_lines(lines)
        if not education_lines:
            education_lines = lines

        for line in education_lines:
            cleaned = CandidateExtractor._clean_education_line(line)
            if not cleaned:
                continue
            if CandidateExtractor._is_education_line(cleaned):
                education.append(cleaned)

        return CandidateExtractor._dedupe_preserve_order(education)[:5]

    @staticmethod
    def _education_section_lines(lines: List[str]) -> List[str]:
        section_lines = []
        in_education = False

        for line in lines:
            normalized = re.sub(r"[^a-z ]", "", line.lower()).strip()
            is_header = normalized in CandidateExtractor.SECTION_HEADERS
            if normalized in {'education', 'academic', 'academics'} or 'education' == normalized:
                in_education = True
                continue

            if in_education and is_header:
                break

            if in_education:
                section_lines.append(line)

        return section_lines

    @staticmethod
    def _clean_education_line(line: str) -> str:
        cleaned = " ".join(str(line).strip().split())
        cleaned = re.sub(CandidateExtractor.EMAIL_PATTERN, "", cleaned)
        cleaned = CandidateExtractor.PHONE_PATTERN.sub("", cleaned)
        cleaned = CandidateExtractor.URL_PATTERN.sub("", cleaned)
        cleaned = re.sub(r"\b(?:linkedin|github|portfolio)\b.*", "", cleaned, flags=re.IGNORECASE)
        cleaned = CandidateExtractor.LOCATION_VALUE_PATTERN.sub("", cleaned)
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        cleaned = re.sub(r"\s*,\s*\|\s*", " | ", cleaned)
        cleaned = re.sub(r"\s*\|\s*", " | ", cleaned)
        cleaned = re.sub(r"\s*[,|/-]\s*(?=$)", "", cleaned)
        cleaned = re.sub(r"\s+([,/-])\s+", r"\1 ", cleaned)
        cleaned = cleaned.strip(" |,-:")

        lowered = cleaned.lower()
        if not cleaned:
            return ""
        if lowered in CandidateExtractor.SECTION_HEADERS:
            return ""
        if any(term in lowered for term in ["professional summary", "summary", "profile", "career objective"]):
            return ""
        if re.search(r"\b(email|phone|mobile|address|location|linkedin|github|portfolio)\b", lowered):
            return ""
        if "," in cleaned and not CandidateExtractor._is_education_line(cleaned):
            return ""

        return cleaned

    @staticmethod
    def _is_education_line(line: str) -> bool:
        return bool(
            CandidateExtractor.DEGREE_PATTERN.search(line)
            or CandidateExtractor.INSTITUTION_PATTERN.search(line)
            or CandidateExtractor.GPA_PATTERN.search(line)
            or (
                CandidateExtractor.GRADUATION_YEAR_PATTERN.search(line)
                and any(keyword.lower() in line.lower() for keyword in CandidateExtractor.EDUCATION_KEYWORDS)
            )
        )

    @staticmethod
    def _dedupe_preserve_order(items: List[str]) -> List[str]:
        seen = set()
        deduped = []
        for item in items:
            key = item.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
        return deduped
    
    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """Extract skills from resume text."""
        skills = []
        text_lower = text.lower()
        
        for skill in CandidateExtractor.SKILL_KEYWORDS:
            # Case-insensitive search
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                skills.append(skill)
        
        return list(set(skills))  # Remove duplicates
    
    @staticmethod
    def extract_experience_summary(text: str, max_lines: int = 5) -> str:
        """Extract experience section summary."""
        # Look for experience section
        lines = text.split('\n')
        experience_lines = []
        in_experience_section = False
        
        for line in lines:
            line_lower = line.lower()
            
            if any(keyword in line_lower for keyword in ['experience', 'professional', 'work history']):
                in_experience_section = True
                continue
            
            if in_experience_section:
                # Stop if we hit another section
                if any(keyword in line_lower for keyword in ['education', 'skills', 'projects', 'certifications']):
                    break
                
                if line.strip():
                    experience_lines.append(line.strip())
        
        return ' '.join(experience_lines[:max_lines])
    
    @staticmethod
    def extract_from_resume(pdf_path: str, filename: str) -> Dict:
        """
        Extract all candidate information from resume.
        
        Returns:
            Dictionary with extracted candidate data
        """
        # Extract text from PDF
        text, metadata = PDFParser.extract_text_with_metadata(pdf_path)
        
        if not text:
            return {
                'candidate_name': CandidateExtractor.extract_name_from_filename(filename),
                'email': None,
                'phone': None,
                'skills': [],
                'education': [],
                'experience_summary': '',
                'extraction_confidence': 'low',
                'pdf_file': filename
            }
        
        # Extract information
        email = CandidateExtractor.extract_email(text)
        phone = CandidateExtractor.extract_phone(text)
        name_from_text = CandidateExtractor.extract_name_from_text(text)
        name_from_filename = CandidateExtractor.extract_name_from_filename(filename)
        
        # Determine final name. Never allow section headings or generic resume text.
        if CandidateExtractor.is_valid_candidate_name(name_from_text):
            final_name = name_from_text
            confidence = 'high' if (
                name_from_text.lower() in name_from_filename.lower() or
                name_from_filename.lower() in name_from_text.lower()
            ) else 'medium'
        else:
            final_name = name_from_filename
            confidence = 'low'
        
        skills = CandidateExtractor.extract_skills(text)
        education = CandidateExtractor.extract_education(text)
        experience = CandidateExtractor.extract_experience_summary(text)
        
        return {
            'candidate_name': final_name,
            'email': email,
            'phone': phone,
            'skills': skills,
            'education': education,
            'experience_summary': experience,
            'extraction_confidence': confidence,
            'pdf_file': filename,
            'num_pages': metadata.get('num_pages', 0),
            'full_text': text
        }
