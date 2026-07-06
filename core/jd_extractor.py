"""Job Description extraction and parsing."""

import re
from typing import Dict, List, Optional
from .pdf_parser import PDFParser


class JDExtractor:
    """Extracts requirements from job descriptions."""
    
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
        'AWS', 'Azure', 'Azure OpenAI', 'Azure AI', 'GCP', 'Google Cloud', 'Kubernetes', 'Docker',
        
        # ML/AI
        'Machine Learning', 'NLP', 'Deep Learning', 'RAG', 'LLM',
        'Transformer', 'BERT', 'GPT', 'Computer Vision', 'Neural Networks',
        
        # Other
        'Git', 'Linux', 'DevOps', 'CI/CD', 'REST API', 'REST APIs', 'GraphQL',
        'Agile', 'Scrum', 'Microservices', 'Docker', 'Kubernetes'
    }
    
    EDUCATION_KEYWORDS = {
        'B.S.', 'B.A.', 'B.Tech', 'Bachelor', 'BS', 'BA',
        'M.S.', 'M.A.', 'M.Tech', 'Master', 'MS', 'MA',
        'Ph.D.', 'PhD', 'Doctorate',
        'Associate', 'Diploma', 'Certificate',
        'Computer Science', 'Engineering', 'Information Technology',
        'Business', 'Management', 'Finance'
    }

    SECTION_ALIASES = {
        'required_skills': [
            'required skills', 'must have', 'must-have', 'mandatory skills',
            'essential skills', 'requirements', 'technical requirements',
            'required qualifications', 'minimum qualifications',
        ],
        'preferred_skills': [
            'preferred skills', 'nice to have', 'nice-to-have', 'good to have',
            'desired skills', 'bonus skills', 'preferred qualifications',
            'plus', 'pluses',
        ],
        'tools': ['tools', 'platforms', 'tooling'],
        'technologies': ['technologies', 'tech stack', 'technology stack', 'frameworks'],
        'certifications': ['certifications', 'certificates', 'licenses'],
        'domain_experience': ['domain experience', 'industry experience', 'domain knowledge'],
        'experience_requirement': ['experience', 'experience requirement', 'minimum experience'],
        'education_requirements': ['education', 'education requirements', 'qualification', 'qualifications'],
        'responsibilities': [
            'responsibilities', 'roles and responsibilities', 'duties',
            'what you will do', 'key responsibilities', 'projects',
            'project responsibilities', 'job responsibilities',
        ],
    }
    
    @staticmethod
    def extract_skills_from_jd(text: str) -> Dict[str, List[str]]:
        """
        Extract required and preferred skills from JD text.
        
        Returns:
            Dict with 'required_skills' and 'preferred_skills'
        """
        text_lower = text.lower()
        sections = JDExtractor.extract_structured_sections(text)
        section_skills = {
            key: JDExtractor.extract_known_terms(value)
            for key, value in sections.items()
        }

        required_skills = list(section_skills.get('required_skills', []))
        preferred_skills = list(section_skills.get('preferred_skills', []))
        preferred_terms = {
            term.lower()
            for key, values in section_skills.items()
            if key == 'preferred_skills'
            for term in values
        }

        for skill in JDExtractor.SKILL_KEYWORDS:
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                if skill == 'Azure' and re.search(r'\bazure\s+(?:openai|ai)\b', text_lower):
                    continue
                if skill == 'REST API' and re.search(r'\brest\s+apis\b', text_lower):
                    continue
                if skill.lower() not in preferred_terms and skill not in required_skills:
                    required_skills.append(skill)

        return {
            'required_skills': JDExtractor.dedupe_preserve_order(required_skills),
            'preferred_skills': JDExtractor.dedupe_preserve_order(preferred_skills),
            'tools': section_skills.get('tools', []),
            'technologies': section_skills.get('technologies', []),
            'certifications': JDExtractor.extract_certifications(text, sections.get('certifications', '')),
            'domain_experience': JDExtractor.extract_domain_experience(sections.get('domain_experience', '')),
        }

    @staticmethod
    def dedupe_preserve_order(items: List[str]) -> List[str]:
        seen = set()
        deduped = []
        for item in items:
            key = re.sub(r"\s+", " ", item.strip().lower()).strip(" .")
            key = {
                "rest apis": "rest api",
                "retrieval augmented generation": "rag",
                "retrieval-augmented generation": "rag",
                "azure openai": "azure ai",
            }.get(key, key)
            if key and key not in seen:
                seen.add(key)
                deduped.append(item.strip())
        return deduped

    @staticmethod
    def extract_structured_sections(text: str) -> Dict[str, str]:
        """Collect text under JD headings across the whole document."""
        sections = {key: "" for key in JDExtractor.SECTION_ALIASES}
        current_key: Optional[str] = None

        for raw_line in JDExtractor.split_inline_headings(text).splitlines():
            line = raw_line.strip()
            if not line:
                continue

            matched_key = JDExtractor.classify_section_heading(line)
            if matched_key:
                current_key = matched_key
                remainder = re.sub(r'^[^:]{1,60}:\s*', '', line).strip()
                if remainder and remainder.lower() != line.lower():
                    sections[current_key] += f"\n{remainder}"
                continue

            if current_key:
                sections[current_key] += f"\n{line}"

        return sections

    @staticmethod
    def split_inline_headings(text: str) -> str:
        """Put common inline section headings on their own lines."""
        aliases = sorted(
            {alias for values in JDExtractor.SECTION_ALIASES.values() for alias in values},
            key=len,
            reverse=True,
        )
        heading_pattern = "|".join(re.escape(alias) for alias in aliases)
        return re.sub(
            rf"(?<!^)\b({heading_pattern})\s*:",
            r"\n\1:",
            text,
            flags=re.IGNORECASE,
        )

    @staticmethod
    def classify_section_heading(line: str) -> Optional[str]:
        lowered = line.lower().strip()
        heading = lowered.split(':', 1)[0].strip()
        heading = re.sub(r'[^a-z0-9+/#.\s-]', '', heading).strip()
        if len(heading.split()) > 8:
            return None

        for key, aliases in JDExtractor.SECTION_ALIASES.items():
            if any(heading == alias or heading.startswith(f"{alias} ") for alias in aliases):
                return key
        return None

    @staticmethod
    def extract_known_terms(text: str) -> List[str]:
        terms = []
        text_lower = text.lower()
        for skill in JDExtractor.SKILL_KEYWORDS:
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                if skill == 'Azure' and re.search(r'\bazure\s+(?:openai|ai)\b', text_lower):
                    continue
                if skill == 'REST API' and re.search(r'\brest\s+apis\b', text_lower):
                    continue
                terms.append(skill)
        terms.extend(JDExtractor.extract_list_items(text))
        return JDExtractor.dedupe_preserve_order(terms)

    @staticmethod
    def extract_list_items(text: str) -> List[str]:
        cleaned = re.sub(r'[•*]', '\n', text)
        pieces = re.split(r'[\n,;|]+', cleaned)
        items = []
        stop_phrases = {'and', 'or', 'with', 'experience', 'knowledge', 'familiarity'}
        for piece in pieces:
            item = re.sub(r'^[-\d.)\s]+', '', piece).strip()
            item = re.sub(r'\s+', ' ', item)
            if not item or len(item) > 70:
                continue
            if item.lower() in stop_phrases:
                continue
            if re.search(r'[A-Za-z+#.]', item):
                items.append(item)
        return items

    @staticmethod
    def extract_certifications(full_text: str, certification_section: str = "") -> List[str]:
        source = f"{certification_section}\n{full_text}"
        patterns = [
            r'\b[A-Z][A-Za-z0-9+/# .-]*Certified[A-Za-z0-9+/# .-]*',
            r'\b[A-Z]{2,6}-\d{2,4}\b',
            r'\b(?:AWS|Azure|Google Cloud|GCP|Microsoft|Cisco|Kubernetes|Terraform)[A-Za-z0-9+/# .-]*(?:Certification|Certified|Associate|Professional|Specialty|Expert)\b',
        ]
        matches = []
        for pattern in patterns:
            matches.extend(re.findall(pattern, source, flags=re.IGNORECASE))
        matches.extend(JDExtractor.extract_list_items(certification_section))
        return JDExtractor.dedupe_preserve_order(matches)

    @staticmethod
    def extract_domain_experience(domain_section: str) -> List[str]:
        return JDExtractor.dedupe_preserve_order(JDExtractor.extract_list_items(domain_section))
    
    @staticmethod
    def extract_experience_requirements(text: str) -> str:
        """Extract years of experience requirement."""
        # Look for patterns like "X years", "X+ years", "X-Y years"
        patterns = [
            r'(\d+)\s*\+?\s*years?',
            r'(\d+)\s*-\s*(\d+)\s*years?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""
    
    @staticmethod
    def extract_education_requirements(text: str) -> List[str]:
        """Extract education requirements from JD."""
        education = []
        
        for keyword in JDExtractor.EDUCATION_KEYWORDS:
            if keyword.lower() in text.lower():
                education.append(keyword)
        
        return education

    @staticmethod
    def extract_responsibilities(text: str) -> List[str]:
        """Extract explicit JD responsibilities and projects."""
        sections = JDExtractor.extract_structured_sections(text)
        responsibility_text = sections.get('responsibilities', '')
        responsibilities = JDExtractor.extract_list_items(responsibility_text)

        if not responsibilities:
            patterns = [
                r'\b(?:responsible for|you will|design|develop|build|implement|deploy|maintain|collaborate|integrate|create|manage|optimize)\b[^.\n]*(?:[.\n]|$)',
            ]
            for pattern in patterns:
                responsibilities.extend(
                    match.strip(" .\n\t-")
                    for match in re.findall(pattern, text, flags=re.IGNORECASE)
                )

        return JDExtractor.dedupe_preserve_order(responsibilities)
    
    @staticmethod
    def extract_from_text(jd_text: str) -> Dict:
        """
        Extract all requirements from job description text.
        
        Args:
            jd_text: Full text of job description
            
        Returns:
            Dictionary with extracted JD requirements
        """
        skills = JDExtractor.extract_skills_from_jd(jd_text)
        experience = JDExtractor.extract_experience_requirements(jd_text)
        education = JDExtractor.extract_education_requirements(jd_text)
        responsibilities = JDExtractor.extract_responsibilities(jd_text)
        
        return {
            'required_skills': skills['required_skills'],
            'preferred_skills': skills['preferred_skills'],
            'tools': skills.get('tools', []),
            'technologies': skills.get('technologies', []),
            'certifications': skills.get('certifications', []),
            'domain_experience': skills.get('domain_experience', []),
            'structured_skills': skills,
            'experience_requirement': experience,
            'education_requirements': education,
            'responsibilities': responsibilities,
            'full_text': jd_text,
            'total_required_skills': len(skills['required_skills']),
            'total_preferred_skills': len(skills['preferred_skills'])
        }
    
    @staticmethod
    def extract_from_pdf(pdf_path: str) -> Dict:
        """
        Extract requirements from job description PDF.
        
        Args:
            pdf_path: Path to JD PDF file
            
        Returns:
            Dictionary with extracted JD requirements
        """
        try:
            text, _ = PDFParser.extract_text_with_metadata(pdf_path)
            if text:
                return JDExtractor.extract_from_text(text)
            else:
                return {
                    'required_skills': [],
                    'preferred_skills': [],
                    'tools': [],
                    'technologies': [],
                    'certifications': [],
                    'domain_experience': [],
                    'structured_skills': {},
                    'experience_requirement': '',
                    'education_requirements': [],
                    'responsibilities': [],
                    'full_text': '',
                    'total_required_skills': 0,
                    'total_preferred_skills': 0,
                    'error': 'Could not extract text from PDF'
                }
        except Exception as e:
            return {
                'required_skills': [],
                'preferred_skills': [],
                'tools': [],
                'technologies': [],
                'certifications': [],
                'domain_experience': [],
                'structured_skills': {},
                'experience_requirement': '',
                'education_requirements': [],
                'responsibilities': [],
                'full_text': '',
                'total_required_skills': 0,
                'total_preferred_skills': 0,
                'error': str(e)
            }
