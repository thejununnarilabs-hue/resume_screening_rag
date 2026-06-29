"""Candidate ranking and scoring based on JD match."""

from typing import List, Dict, Any, Optional
import numpy as np
from collections import Counter
import math


class RankingEngine:
    """Ranks candidates based on JD match and various criteria."""
    
    # Scoring weights
    WEIGHTS = {
        'semantic_similarity': 0.60,
        'skill_match': 0.20,
        'experience_match': 0.10,
        'education_match': 0.10
    }
    
    def __init__(self):
        """Initialize ranking engine."""
        pass
    
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
        if not required_skills and not preferred_skills:
            return 0.5  # Neutral score if no skills required
        
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        required_lower = [s.lower() for s in required_skills]
        preferred_lower = [s.lower() for s in preferred_skills]
        
        # Count matches
        required_matches = sum(1 for skill in required_lower 
                              if skill in candidate_skills_lower)
        preferred_matches = sum(1 for skill in preferred_lower 
                               if skill in candidate_skills_lower)
        
        # Calculate score (weighted)
        total_required = len(required_lower) or 1
        total_preferred = len(preferred_lower) or 1
        
        required_score = required_matches / total_required
        preferred_score = preferred_matches / total_preferred if preferred_matches > 0 else 0
        
        # Overall skill score (required skills weighted more)
        skill_score = (required_score * 0.7 + preferred_score * 0.3)
        return min(skill_score, 1.0)
    
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
        if not candidate_experience or not required_experience:
            return 0.5
        
        candidate_exp_lower = candidate_experience.lower()
        required_exp_lower = required_experience.lower()
        
        # Check for presence of experience keywords
        keywords = ['experience', 'work', 'project', 'role', 'manager', 'developer',
                   'engineer', 'analyst', 'specialist', 'architect']
        
        keyword_matches = sum(1 for keyword in keywords 
                             if keyword in candidate_exp_lower)
        
        # Check if experience text is substantial
        candidate_quality = min(len(candidate_exp_lower) / 200, 1.0)  # Normalize by 200 chars
        
        return min((keyword_matches * 0.1 + candidate_quality * 0.6), 1.0)
    
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
        if not required_education:
            return 0.5
        
        if not candidate_education:
            return 0.1  # Low score if no education provided
        
        candidate_edu_lower = [e.lower() for e in candidate_education]
        required_edu_lower = [e.lower() for e in required_education]
        
        # Calculate matches
        matches = sum(1 for req in required_edu_lower 
                     for cand in candidate_edu_lower 
                     if req in cand or cand in req)
        
        match_score = matches / len(required_edu_lower) if required_education else 0
        
        # Bonus if candidate has more education than required
        education_depth = min(len(candidate_education) / 3, 1.0)
        
        return min(match_score * 0.7 + education_depth * 0.3, 1.0)

    @staticmethod
    def get_skill_alignment(candidate_skills: List[str],
                            required_skills: List[str],
                            preferred_skills: List[str]) -> Dict[str, List[str]]:
        """Return matched and missing JD skills for ranking explanations."""
        candidate_lookup = {skill.lower(): skill for skill in candidate_skills}

        def find_matches(skills: List[str]) -> List[str]:
            matches = []
            for skill in skills:
                skill_lower = skill.lower()
                if skill_lower in candidate_lookup:
                    matches.append(candidate_lookup[skill_lower])
            return matches

        matched_required = find_matches(required_skills)
        matched_preferred = find_matches(preferred_skills)
        matched_required_lower = {skill.lower() for skill in matched_required}
        missing_required = [skill for skill in required_skills if skill.lower() not in matched_required_lower]

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
        Final Score = 0.60 * Semantic Similarity
                    + 0.20 * Skill Match
                    + 0.10 * Experience Match
                    + 0.10 * Education Match
        
        Args:
            semantic_similarity: Similarity score (0-1)
            skill_match: Skill match score (0-1)
            experience_match: Experience match score (0-1)
            education_match: Education match score (0-1)
            
        Returns:
            Final score (0-1)
        """
        final_score = (
            RankingEngine.WEIGHTS['semantic_similarity'] * semantic_similarity +
            RankingEngine.WEIGHTS['skill_match'] * skill_match +
            RankingEngine.WEIGHTS['experience_match'] * experience_match +
            RankingEngine.WEIGHTS['education_match'] * education_match
        )
        
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
            
            # Calculate individual scores
            skill_score = RankingEngine.calculate_skill_match(
                candidate.get('skills', []),
                jd_data.get('required_skills', []),
                jd_data.get('preferred_skills', [])
            )
            
            experience_score = RankingEngine.calculate_experience_match(
                candidate.get('experience_summary', ''),
                jd_data.get('experience_requirement', '')
            )
            
            education_score = RankingEngine.calculate_education_match(
                candidate.get('education', []),
                jd_data.get('education_requirements', [])
            )
            skill_alignment = RankingEngine.get_skill_alignment(
                candidate.get('skills', []),
                jd_data.get('required_skills', []),
                jd_data.get('preferred_skills', [])
            )
            
            # Calculate final score
            final_score = RankingEngine.calculate_final_score(
                semantic_sim, skill_score, experience_score, education_score
            )
            
            # Create ranking entry
            ranking_entry = {
                'candidate_name': candidate_name,
                'email': candidate.get('email', ''),
                'phone': candidate.get('phone', ''),
                'pdf_file': candidate.get('pdf_file', ''),
                'final_score': final_score,
                'semantic_similarity': semantic_sim,
                'skill_match': skill_score,
                'experience_match': experience_score,
                'education_match': education_score,
                'matched_required_skills': skill_alignment['matched_required_skills'],
                'matched_preferred_skills': skill_alignment['matched_preferred_skills'],
                'missing_required_skills': skill_alignment['missing_required_skills'],
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
        
        Uses formula:
        Final Score = bm25_weight * BM25 Score
                    + (1 - bm25_weight) * Original Ranking Score
        
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
            
            # Blend BM25 with original score
            original_score = candidate['final_score']
            blended_score = (bm25_weight * bm25_score) + ((1 - bm25_weight) * original_score)
            
            candidate['bm25_score'] = bm25_score
            candidate['original_score'] = original_score
            candidate['final_score'] = blended_score
        
        # Re-sort by new final score
        ranked_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Update ranks
        for rank, candidate in enumerate(ranked_candidates, 1):
            candidate['rank'] = rank
        
        return ranked_candidates
