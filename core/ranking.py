"""Candidate ranking and scoring based on JD match."""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from collections import Counter
import math
import re
from difflib import SequenceMatcher


class RankingEngine:
    """Ranks candidates based on JD match and various criteria."""
    
    # Scoring weights
    WEIGHTS = {
        'skill_match': 0.45,
        'experience_match': 0.25,
        'education_match': 0.10,
        'responsibility_match': 0.20,
    }
    
    def __init__(self):
        """Initialize ranking engine."""
        pass

    SKILL_SYNONYMS = {
        'amazon web services': 'aws',
        'aws cloud': 'aws',
        'natural language processing': 'nlp',
        'google cloud platform': 'gcp',
        'google cloud': 'gcp',
        'rest': 'rest api',
        'restful api': 'rest api',
        'rest apis': 'rest api',
        'nodejs': 'node.js',
        'node js': 'node.js',
        'ci cd': 'ci/cd',
        'cicd': 'ci/cd',
        'postgres': 'postgresql',
        'mongo': 'mongodb',
        'retrieval augmented generation': 'rag',
        'retrieval-augmented generation': 'rag',
        'azure openai': 'azure ai',
        'azure ai': 'azure ai',
        'k8s': 'kubernetes',
    }

    EDUCATION_SYNONYMS = {
        'b.sc': 'bachelor',
        'bsc': 'bachelor',
        'bs': 'bachelor',
        'ba': 'bachelor',
        'b.a': 'bachelor',
        'btech': 'bachelor',
        'b.tech': 'bachelor',
        'be': 'bachelor',
        'b.e': 'bachelor',
        'bachelor': 'bachelor',
        'm.sc': 'master',
        'msc': 'master',
        'ms': 'master',
        'ma': 'master',
        'm.a': 'master',
        'mtech': 'master',
        'm.tech': 'master',
        'me': 'master',
        'm.e': 'master',
        'master': 'master',
        'phd': 'doctorate',
        'ph.d': 'doctorate',
        'doctorate': 'doctorate',
    }

    @staticmethod
    def _normalize_text(value: Any) -> str:
        text = str(value or "").lower()
        text = re.sub(r"[^a-z0-9+#./\s-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _normalize_skill(skill: Any) -> str:
        normalized = RankingEngine._normalize_text(skill)
        normalized = normalized.replace(" / ", "/").replace(" - ", "-")
        normalized = re.sub(r"\s+", " ", normalized).strip(" .-/")
        return RankingEngine.SKILL_SYNONYMS.get(normalized, normalized)

    @staticmethod
    def _normalize_education(value: Any) -> str:
        normalized = RankingEngine._normalize_text(value)
        normalized = re.sub(r"\bm\s*\.?\s*sc\b", "master", normalized)
        normalized = re.sub(r"\bb\s*\.?\s*sc\b", "bachelor", normalized)
        normalized = re.sub(r"\bm\s*\.?\s*tech\b", "master", normalized)
        normalized = re.sub(r"\bb\s*\.?\s*tech\b", "bachelor", normalized)
        normalized = re.sub(r"\bph\s*\.?\s*d\b", "doctorate", normalized)

        tokens = [
            RankingEngine.EDUCATION_SYNONYMS.get(token.strip("."), token.strip("."))
            for token in normalized.split()
        ]
        return " ".join(tokens)

    @staticmethod
    def _dedupe_normalized(values: List[Any], normalizer) -> List[str]:
        deduped = []
        seen = set()
        for value in values or []:
            normalized = normalizer(value)
            if normalized and normalized not in seen:
                seen.add(normalized)
                deduped.append(normalized)
        return deduped

    @staticmethod
    def _token_set(text: str) -> set:
        normalized = RankingEngine._normalize_text(text)
        return {
            token for token in re.findall(r"[a-z0-9+#.]+", normalized)
            if len(token) > 1
        }

    @staticmethod
    def _stem_token(token: str) -> str:
        token = token.lower()
        if token.endswith("ing") and len(token) > 5:
            return token[:-3]
        if token.endswith("ed") and len(token) > 4:
            return token[:-2]
        if token.endswith("s") and len(token) > 3:
            return token[:-1]
        return token

    @staticmethod
    def _responsibility_tokens(text: str) -> set:
        stop_words = {
            'and', 'or', 'the', 'a', 'an', 'to', 'with', 'for', 'of', 'in',
            'on', 'using', 'use', 'you', 'will', 'responsible', 'responsibility',
            'responsibilities',
        }
        return {
            RankingEngine._stem_token(token)
            for token in RankingEngine._token_set(text)
            if token not in stop_words
        }

    @staticmethod
    def _responsibility_similarity(candidate_text: str, responsibility: str) -> float:
        candidate_tokens = RankingEngine._responsibility_tokens(candidate_text)
        responsibility_tokens = RankingEngine._responsibility_tokens(responsibility)
        if not candidate_tokens or not responsibility_tokens:
            return 0.0
        return len(candidate_tokens & responsibility_tokens) / len(responsibility_tokens)

    @staticmethod
    def _text_similarity(candidate_text: str, requirement_text: str) -> float:
        candidate_text = RankingEngine._normalize_text(candidate_text)
        requirement_text = RankingEngine._normalize_text(requirement_text)
        if not candidate_text or not requirement_text:
            return 0.0
        if candidate_text == requirement_text:
            return 1.0

        candidate_tokens = RankingEngine._token_set(candidate_text)
        requirement_tokens = RankingEngine._token_set(requirement_text)
        if not candidate_tokens or not requirement_tokens:
            return 0.0

        coverage = len(candidate_tokens & requirement_tokens) / len(requirement_tokens)
        jaccard = len(candidate_tokens & requirement_tokens) / len(candidate_tokens | requirement_tokens)
        sequence = SequenceMatcher(None, candidate_text, requirement_text).ratio()
        return min((coverage * 0.60) + (jaccard * 0.20) + (sequence * 0.20), 1.0)

    @staticmethod
    def _year_bounds(text: str) -> Optional[Tuple[int, int]]:
        if not text:
            return None
        range_match = re.search(r"\b(\d+)\s*(?:-|to)\s*(\d+)\s*\+?\s*years?\b", text, re.IGNORECASE)
        if range_match:
            low, high = sorted((int(range_match.group(1)), int(range_match.group(2))))
            return low, high

        plus_match = re.search(r"\b(\d+)\s*\+?\s*years?\b", text, re.IGNORECASE)
        if plus_match:
            years = int(plus_match.group(1))
            return years, years

        return None

    @staticmethod
    def _extract_min_years(text: str) -> Optional[float]:
        bounds = RankingEngine._year_bounds(text or "")
        return float(bounds[0]) if bounds else None

    @staticmethod
    def _extract_candidate_years(text: str) -> Optional[float]:
        if not text:
            return None

        patterns = [
            r"\b(?:total\s+)?(?:experience|experienced)\s*(?:of|:|-)?\s*(\d+(?:\.\d+)?)\s*\+?\s*years?\b",
            r"\b(\d+(?:\.\d+)?)\s*\+?\s*years?\s+(?:of\s+)?(?:professional\s+)?experience\b",
            r"\bover\s+(\d+(?:\.\d+)?)\s+years?\s+(?:of\s+)?(?:professional\s+)?experience\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1))
        return None
    
    @staticmethod
    def calculate_skill_match(candidate_skills: List[str],
                             required_skills: List[str],
                             preferred_skills: List[str]) -> float:
        """
        Calculate skill matching score.
        
        Args:
            candidate_skills: List of candidate's skills
            required_skills: List of required skills
            preferred_skills: List of preferred skills
            
        Returns:
            Skill match score (0-1)
        """
        candidate_set = set(RankingEngine._dedupe_normalized(candidate_skills, RankingEngine._normalize_skill))
        required = RankingEngine._dedupe_normalized(required_skills, RankingEngine._normalize_skill)
        preferred = RankingEngine._dedupe_normalized(preferred_skills, RankingEngine._normalize_skill)

        if not required and not preferred:
            return 1.0

        def coverage(skills: List[str]) -> Optional[float]:
            if not skills:
                return None
            matches = sum(1 for skill in skills if skill in candidate_set)
            return matches / len(skills)

        required_score = coverage(required)
        preferred_score = coverage(preferred)

        weighted_parts = []
        if required_score is not None:
            weighted_parts.append((required_score, 0.75))
        if preferred_score is not None:
            weighted_parts.append((preferred_score, 0.25 if required_score is not None else 1.0))

        total_weight = sum(weight for _, weight in weighted_parts)
        if total_weight == 0:
            return 1.0
        return min(sum(score * weight for score, weight in weighted_parts) / total_weight, 1.0)

    @staticmethod
    def get_required_skill_alignment(candidate_skills: List[str],
                                     required_skills: List[str]) -> Dict[str, Any]:
        """Count each required skill once and return matched/missing labels."""
        candidate_lookup = {}
        for skill in candidate_skills or []:
            normalized = RankingEngine._normalize_skill(skill)
            if normalized and normalized not in candidate_lookup:
                candidate_lookup[normalized] = skill

        required_lookup = []
        seen = set()
        for skill in required_skills or []:
            normalized = RankingEngine._normalize_skill(skill)
            if normalized and normalized not in seen:
                seen.add(normalized)
                required_lookup.append((skill, normalized))

        matched = [
            original for original, normalized in required_lookup
            if normalized in candidate_lookup
        ]
        missing = [
            original for original, normalized in required_lookup
            if normalized not in candidate_lookup
        ]
        return {
            "matched_skills": matched,
            "missing_skills": missing,
            "required_skills": len(required_lookup),
            "matched_skill_count": len(matched),
        }
    
    @staticmethod
    def calculate_experience_match(candidate_experience: str,
                                  required_experience: str) -> float:
        """
        Calculate experience matching score.
        
        Args:
            candidate_experience: Candidate's experience summary
            required_experience: Required experience from JD
            
        Returns:
            Experience match score (0-1)
        """
        if not required_experience:
            return 1.0
        if not candidate_experience:
            return 0.0

        semantic_score = RankingEngine._text_similarity(candidate_experience, required_experience)

        required_years = RankingEngine._year_bounds(required_experience)
        if not required_years:
            return semantic_score

        candidate_years = RankingEngine._year_bounds(candidate_experience)
        if not candidate_years:
            return semantic_score

        candidate_high = candidate_years[1]
        required_low = required_years[0]
        year_score = 1.0 if candidate_high >= required_low else candidate_high / max(required_low, 1)
        if year_score >= 1.0 and len(RankingEngine._token_set(required_experience)) <= 3:
            return 1.0
        return min((semantic_score * 0.65) + (year_score * 0.35), 1.0)

    @staticmethod
    def calculate_ats_experience_score(candidate_text: str,
                                       required_experience: str) -> Tuple[float, str, str]:
        """Calculate the 25-point ATS experience score from explicit years."""
        required_years = RankingEngine._extract_min_years(required_experience)
        candidate_years = RankingEngine._extract_candidate_years(candidate_text)

        required_label = required_experience or ""
        candidate_label = f"{candidate_years:g} years" if candidate_years is not None else ""

        if required_years is None or required_years <= 0 or candidate_years is None:
            return 0.0, required_label, candidate_label

        if candidate_years >= required_years:
            return 25.0, required_label, candidate_label
        return (candidate_years / required_years) * 25.0, required_label, candidate_label
    
    @staticmethod
    def calculate_education_match(candidate_education: List[str],
                                 required_education: List[str]) -> float:
        """
        Calculate education matching score.
        
        Args:
            candidate_education: List of candidate's education
            required_education: List of required education
            
        Returns:
            Education match score (0-1)
        """
        required = RankingEngine._dedupe_normalized(required_education, RankingEngine._normalize_education)
        candidate = RankingEngine._dedupe_normalized(candidate_education, RankingEngine._normalize_education)

        if not required:
            return 1.0
        if not candidate:
            return 0.0

        degree_terms = {'bachelor', 'master', 'doctorate', 'diploma', 'associate'}
        degree_requirements = [
            requirement for requirement in required
            if RankingEngine._token_set(requirement) & degree_terms
        ]
        if degree_requirements:
            required = degree_requirements

        matched_scores = []
        for requirement in required:
            best = max(RankingEngine._text_similarity(candidate_item, requirement) for candidate_item in candidate)
            matched_scores.append(best)

        return min(sum(matched_scores) / len(matched_scores), 1.0)

    @staticmethod
    def calculate_ats_education_score(candidate_education: List[str],
                                      required_education: List[str]) -> Tuple[float, str, str, str]:
        """Return exact, related, or no education match using only extracted education text."""
        required = RankingEngine._dedupe_normalized(required_education, RankingEngine._normalize_education)
        candidate = RankingEngine._dedupe_normalized(candidate_education, RankingEngine._normalize_education)
        required_label = ", ".join(required_education or [])
        candidate_label = ", ".join(candidate_education or [])

        if not required or not candidate:
            return 0.0, required_label, candidate_label, "No explicit education comparison available"

        for requirement in required:
            if any(requirement == item or requirement in item or item in requirement for item in candidate):
                return 10.0, required_label, candidate_label, "Exact match: 10"

        degree_terms = {'bachelor', 'master', 'doctorate', 'diploma', 'associate'}
        required_terms = set().union(*(RankingEngine._token_set(item) for item in required))
        candidate_terms = set().union(*(RankingEngine._token_set(item) for item in candidate))
        if required_terms & candidate_terms & degree_terms:
            return 7.0, required_label, candidate_label, "Related degree: 7"

        return 0.0, required_label, candidate_label, "No exact or related degree match: 0"

    @staticmethod
    def get_responsibility_alignment(candidate: Dict[str, Any],
                                     jd_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare every extracted JD responsibility/project against resume evidence."""
        responsibilities = []
        seen = set()
        for responsibility in jd_data.get('responsibilities', []) or []:
            normalized = RankingEngine._normalize_text(responsibility)
            if normalized and normalized not in seen:
                seen.add(normalized)
                responsibilities.append(responsibility)

        candidate_text = " ".join([
            candidate.get('experience_summary', ''),
            " ".join(candidate.get('projects', [])) if isinstance(candidate.get('projects'), list) else str(candidate.get('projects', '')),
            candidate.get('full_text', ''),
        ])

        matched = []
        missing = []
        for responsibility in responsibilities:
            best = RankingEngine._responsibility_similarity(candidate_text, responsibility)
            if best >= 0.60:
                matched.append(responsibility)
            else:
                missing.append(responsibility)

        return {
            "matched_responsibilities": matched,
            "missing_responsibilities": missing,
            "total_responsibilities": len(responsibilities),
            "matched_responsibility_count": len(matched),
        }

    @staticmethod
    def calculate_ats_match(candidate: Dict[str, Any],
                            jd_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the exact ATS JSON score requested by the project."""
        skill_alignment = RankingEngine.get_required_skill_alignment(
            candidate.get('skills', []),
            jd_data.get('required_skills', []),
        )
        required_skill_count = skill_alignment["required_skills"]
        matched_skill_count = skill_alignment["matched_skill_count"]
        skill_score = (
            (matched_skill_count / required_skill_count) * 45.0
            if required_skill_count else 0.0
        )

        candidate_experience_text = " ".join([
            candidate.get('experience_summary', ''),
            candidate.get('full_text', ''),
        ])
        experience_score, required_experience, candidate_experience = RankingEngine.calculate_ats_experience_score(
            candidate_experience_text,
            jd_data.get('experience_requirement', ''),
        )

        education_score, required_education, candidate_education, education_calc = RankingEngine.calculate_ats_education_score(
            candidate.get('education', []),
            jd_data.get('education_requirements', []),
        )

        responsibility_alignment = RankingEngine.get_responsibility_alignment(candidate, jd_data)
        total_responsibilities = responsibility_alignment["total_responsibilities"]
        matched_responsibility_count = responsibility_alignment["matched_responsibility_count"]
        responsibility_score = (
            (matched_responsibility_count / total_responsibilities) * 20.0
            if total_responsibilities else 0.0
        )

        final_score = round(skill_score + experience_score + education_score + responsibility_score, 1)

        return {
            "matched_skills": skill_alignment["matched_skills"],
            "missing_skills": skill_alignment["missing_skills"],
            "required_skills": required_skill_count,
            "matched_skill_count": matched_skill_count,
            "skill_score": round(skill_score, 2),
            "required_experience": required_experience,
            "candidate_experience": candidate_experience,
            "experience_score": round(experience_score, 2),
            "required_education": required_education,
            "candidate_education": candidate_education,
            "education_score": round(education_score, 2),
            "matched_responsibilities": responsibility_alignment["matched_responsibilities"],
            "missing_responsibilities": responsibility_alignment["missing_responsibilities"],
            "responsibility_score": round(responsibility_score, 2),
            "final_score": final_score,
            "calculation": {
                "skills": f"({matched_skill_count}/{required_skill_count}) × 45 = {skill_score:.2f}" if required_skill_count else "(0/0) × 45 = 0",
                "experience": (
                    "candidate experience >= required experience = 25"
                    if experience_score == 25.0
                    else f"({candidate_experience or '0 years'} / {required_experience or 'required experience not found'}) × 25 = {experience_score:.2f}"
                ),
                "education": education_calc,
                "responsibilities": (
                    f"({matched_responsibility_count}/{total_responsibilities}) × 20 = {responsibility_score:.2f}"
                    if total_responsibilities else "(0/0) × 20 = 0"
                ),
            },
        }

    @staticmethod
    def get_skill_alignment(candidate_skills: List[str],
                            required_skills: List[str],
                            preferred_skills: List[str]) -> Dict[str, List[str]]:
        """Return matched and missing JD skills for ranking explanations."""
        candidate_lookup = {}
        for skill in candidate_skills:
            normalized = RankingEngine._normalize_skill(skill)
            if normalized and normalized not in candidate_lookup:
                candidate_lookup[normalized] = skill

        def find_matches(skills: List[str]) -> List[str]:
            matches = []
            for skill in skills:
                normalized = RankingEngine._normalize_skill(skill)
                if normalized in candidate_lookup:
                    matches.append(candidate_lookup[normalized])
            return matches

        matched_required = find_matches(required_skills)
        matched_preferred = find_matches(preferred_skills)
        candidate_normalized = set(candidate_lookup)
        missing_required = [
            skill for skill in required_skills
            if RankingEngine._normalize_skill(skill) not in candidate_normalized
        ]

        return {
            'matched_required_skills': matched_required,
            'matched_preferred_skills': matched_preferred,
            'missing_required_skills': missing_required,
        }
    
    @staticmethod
    def calculate_final_score(semantic_similarity: float,
                             skill_match: float,
                             experience_match: float,
                             education_match: float) -> float:
        """
        Calculate final ranking score using weighted formula.
        
        Formula:
        Final Score = 0.40 * Skills Match
                    + 0.30 * Experience Match
                    + 0.10 * Education Match
                    + 0.20 * Semantic Content Similarity
        
        Args:
            semantic_similarity: Similarity score (0-1)
            skill_match: Skill match score (0-1)
            experience_match: Experience match score (0-1)
            education_match: Education match score (0-1)
            
        Returns:
            Final score (0-1)
        """
        components = {
            'skill_match': skill_match,
            'experience_match': experience_match,
            'education_match': education_match,
            'semantic_similarity': semantic_similarity,
        }
        active_components = {
            name: score for name, score in components.items()
            if score is not None
        }
        active_weight = sum(RankingEngine.WEIGHTS.get(name, 0.0) for name in active_components)
        if active_weight <= 0:
            return 0.0

        final_score = sum(
            RankingEngine.WEIGHTS.get(name, 0.0) * max(min(score, 1.0), 0.0)
            for name, score in active_components.items()
        ) / active_weight

        return min(max(final_score, 0.0), 1.0)  # Clamp to [0, 1]
    
    @staticmethod
    def rank_candidates(candidates: List[Dict[str, Any]],
                       jd_data: Dict[str, Any],
                       semantic_similarities: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Rank all candidates based on JD match.
        
        Args:
            candidates: List of candidate data dictionaries
            jd_data: Extracted JD data
            semantic_similarities: Dict of {candidate_name: similarity_score}
            
        Returns:
            Ranked list of candidates with scores
        """
        ranked_candidates = []
        
        for candidate in candidates:
            candidate_name = candidate.get('candidate_name', '')
            
            # Get semantic similarity from pre-calculated scores
            semantic_sim = semantic_similarities.get(candidate_name, 0.5)
            
            ats_report = RankingEngine.calculate_ats_match(candidate, jd_data)
            skill_alignment = RankingEngine.get_skill_alignment(
                candidate.get('skills', []),
                jd_data.get('required_skills', []),
                jd_data.get('preferred_skills', [])
            )
            skill_score = ats_report['skill_score'] / 45.0 if ats_report['skill_score'] else 0.0
            experience_score = ats_report['experience_score'] / 25.0 if ats_report['experience_score'] else 0.0
            education_score = ats_report['education_score'] / 10.0 if ats_report['education_score'] else 0.0
            responsibility_score = ats_report['responsibility_score'] / 20.0 if ats_report['responsibility_score'] else 0.0
            
            # Create ranking entry
            ranking_entry = {
                'candidate_name': candidate_name,
                'email': candidate.get('email', ''),
                'phone': candidate.get('phone', ''),
                'pdf_file': candidate.get('pdf_file', ''),
                'final_score': ats_report['final_score'],
                'ats_report': ats_report,
                'semantic_similarity': semantic_sim,
                'skill_match': skill_score,
                'experience_match': experience_score,
                'education_match': education_score,
                'responsibility_match': responsibility_score,
                'matched_required_skills': skill_alignment['matched_required_skills'],
                'matched_preferred_skills': skill_alignment['matched_preferred_skills'],
                'missing_required_skills': skill_alignment['missing_required_skills'],
                'matched_responsibilities': ats_report['matched_responsibilities'],
                'missing_responsibilities': ats_report['missing_responsibilities'],
                'skills': candidate.get('skills', []),
                'experience_summary': candidate.get('experience_summary', ''),
                'education': candidate.get('education', [])
            }
            
            ranked_candidates.append(ranking_entry)
        
        # Sort by final score (descending)
        ranked_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Add rank position
        for rank, candidate in enumerate(ranked_candidates, 1):
            candidate['rank'] = rank
        
        return ranked_candidates
    
    @staticmethod
    def get_top_candidates(ranked_candidates: List[Dict[str, Any]],
                          top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Get top N candidates from ranking.
        
        Args:
            ranked_candidates: Full ranked list
            top_n: Number of top candidates to return
            
        Returns:
            Top N candidates
        """
        return ranked_candidates[:top_n]
    
    @staticmethod
    def calculate_bm25_score(candidate_text: str, jd_text: str,
                            k1: float = 1.5, b: float = 0.75) -> float:
        """
        Calculate BM25 (Best Matching 25) score for candidate against JD.
        
        BM25 is a probabilistic relevance framework used in information retrieval.
        It considers term frequency, inverse document frequency, and document length normalization.
        
        Args:
            candidate_text: Candidate's full text (skills, experience, education)
            jd_text: Job description text
            k1: Term frequency saturation parameter (default 1.5)
            b: Length normalization parameter (default 0.75)
            
        Returns:
            BM25 relevance score (0-1, higher is better)
        """
        # Tokenize and normalize
        def tokenize(text: str) -> List[str]:
            """Simple tokenization and lowercasing."""
            return text.lower().split()
        
        candidate_tokens = tokenize(candidate_text)
        jd_tokens = tokenize(jd_text)
        
        if not candidate_tokens or not jd_tokens:
            return 0.0
        
        # Calculate average document length
        avg_doc_length = (len(candidate_tokens) + len(jd_tokens)) / 2.0
        doc_length = len(candidate_tokens)
        
        # Build term frequencies
        jd_term_freq = Counter(jd_tokens)
        candidate_term_freq = Counter(candidate_tokens)
        
        # Calculate IDF for each term in JD
        idf_scores = {}
        total_terms = len(set(jd_tokens))
        
        for term in jd_term_freq:
            # Number of documents containing term (simplified: 0 or 1)
            docs_with_term = 1 if term in candidate_term_freq else 0
            
            # IDF calculation
            idf = math.log(1 + (len(jd_tokens) - docs_with_term + 0.5) / 
                          (docs_with_term + 0.5))
            idf_scores[term] = idf
        
        # Calculate BM25 score
        bm25_score = 0.0
        
        for term, term_freq in jd_term_freq.items():
            if term in candidate_term_freq:
                candidate_freq = candidate_term_freq[term]
                idf = idf_scores.get(term, 0.0)
                
                # BM25 formula
                numerator = idf * candidate_freq * (k1 + 1)
                denominator = candidate_freq + k1 * (1 - b + b * (doc_length / avg_doc_length))
                
                bm25_score += numerator / denominator
        
        # Normalize to 0-1 range
        max_possible_score = sum(idf_scores.values())
        
        if max_possible_score > 0:
            bm25_score = bm25_score / max_possible_score
        
        return min(max(bm25_score, 0.0), 1.0)
    
    @staticmethod
    def rank_candidates_with_bm25(candidates: List[Dict[str, Any]],
                                  jd_data: Dict[str, Any],
                                  semantic_similarities: Dict[str, float],
                                  bm25_weight: float = 0.40) -> List[Dict[str, Any]]:
        """
        Rank candidates with BM25 scoring integrated.
        
        BM25 is retained as an auxiliary relevance signal. The final match
        score remains the normalized weighted score from rank_candidates().
        
        Args:
            candidates: List of candidate data
            jd_data: Extracted JD data
            semantic_similarities: Pre-calculated semantic similarities
            bm25_weight: Weight for BM25 (0.0 - 1.0)
            
        Returns:
            Ranked list with BM25 scores integrated
        """
        # First, get initial rankings
        ranked_candidates = RankingEngine.rank_candidates(
            candidates, jd_data, semantic_similarities
        )
        
        # Calculate BM25 scores for each candidate
        jd_combined_text = f"{' '.join(jd_data.get('required_skills', []))} {jd_data.get('full_text', '')}"
        
        for candidate in ranked_candidates:
            candidate_combined_text = f"{' '.join(candidate.get('skills', []))} {candidate.get('experience_summary', '')}"
            
            bm25_score = RankingEngine.calculate_bm25_score(
                candidate_combined_text,
                jd_combined_text
            )
            
            original_score = candidate['final_score']

            candidate['bm25_score'] = bm25_score
            candidate['original_score'] = original_score
        
        # Re-sort by new final score
        ranked_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Update ranks
        for rank, candidate in enumerate(ranked_candidates, 1):
            candidate['rank'] = rank
        
        return ranked_candidates
