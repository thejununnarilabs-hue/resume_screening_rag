"""Evaluation framework for chatbot responses and system performance."""

import json
import re
from difflib import SequenceMatcher
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path


class EvaluationFramework:
    """Evaluates chatbot responses and system metrics."""

    EXCEL_COLUMNS = [
        'timestamp',
        'question',
        'ground_truth',
        'generated_answer',
        'precision_at_k',
        'recall_at_k',
        'faithfulness',
        'answer_relevancy',
        'ranking_quality',
        'ground_truth_available',
    ]
    
    def __init__(self, export_path: str = "exports/metrics.xlsx"):
        """
        Initialize evaluation framework.
        
        Args:
            export_path: Path to export evaluation results
        """
        self.export_path = Path(export_path)
        self.export_path.parent.mkdir(parents=True, exist_ok=True)
        self.evaluations = self._load_existing_evaluations()
        self._ensure_excel_workbook()
    
    def generate_ground_truth_qa(self, candidates: List[Dict[str, Any]],
                                jd_data: Dict[str, Any],
                                ranking_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Generate ground truth QA pairs from candidates and JD.
        
        Args:
            candidates: List of extracted candidates
            jd_data: Extracted JD data
            ranking_data: Ranked candidates data
            
        Returns:
            List of QA pairs for evaluation
        """
        qa_pairs = []
        qa_pairs.append({
            'question': "Which candidate has AWS and NLP experience?",
            'expected_answer': self._generate_keyword_pair_answer(candidates, ["AWS", "NLP"]),
            'category': 'skill_search'
        })

        qa_pairs.append({
            'question': "Who has worked on RAG projects?",
            'expected_answer': self._generate_project_keyword_answer(candidates, "rag"),
            'category': 'project_search'
        })
        
        # QA2: Top candidate question
        if ranking_data:
            top_candidate = ranking_data[0]
            qa_pairs.append({
                'question': "Why was candidate 1 ranked first?",
                'expected_answer': self._generate_ranking_explanation(top_candidate, jd_data),
                'category': 'ranking_explanation'
            })
        
        # QA3: Comparison question
        if len(ranking_data) >= 2:
            cand1, cand2 = ranking_data[0], ranking_data[1]
            qa_pairs.append({
                'question': "Compare candidate 1 and candidate 2",
                'expected_answer': self._generate_comparison(cand1, cand2, jd_data),
                'category': 'comparison'
            })
        
        # QA4: Experience question
        qa_pairs.append({
            'question': f"Who has experience with {jd_data.get('experience_requirement', 'relevant experience')}?",
            'expected_answer': self._generate_experience_answer(candidates, jd_data),
            'category': 'experience_search'
        })

        required_skills = jd_data.get('required_skills', [])
        if required_skills:
            qa_pairs.append({
                'question': f"Which candidates have {required_skills[0]} experience?",
                'expected_answer': self._generate_skill_search_answer(candidates, jd_data),
                'category': 'jd_skill_search'
            })
        
        return qa_pairs

    @staticmethod
    def _find_common_skill_pair(candidates: List[Dict]) -> List[str]:
        """Find two skills that appear together in at least one resume."""
        for candidate in candidates:
            skills = [skill for skill in candidate.get('skills', []) if skill]
            if len(skills) >= 2:
                return skills[:2]
        return []

    @staticmethod
    def _generate_skill_pair_answer(candidates: List[Dict], skills: List[str]) -> str:
        """Generate expected answer for a two-skill search."""
        if len(skills) < 2:
            return "No candidates found with the specified skills."

        required = {skill.lower() for skill in skills}
        matches = []
        for candidate in candidates:
            candidate_skills = {skill.lower() for skill in candidate.get('skills', [])}
            text = candidate.get('full_text', '').lower()
            if all(skill in candidate_skills or skill in text for skill in required):
                matches.append(candidate.get('candidate_name', 'Unknown'))

        if matches:
            return f"Candidates matching {skills[0]} and {skills[1]} experience: {', '.join(matches)}"
        return "No candidates found with the specified skills."

    @staticmethod
    def _generate_keyword_pair_answer(candidates: List[Dict], keywords: List[str]) -> str:
        """Generate expected answer for a fixed, dynamic keyword-pair question."""
        matches = []
        for candidate in candidates:
            if EvaluationFramework._candidate_matches_terms(candidate, keywords):
                matches.append(candidate.get('candidate_name', 'Unknown'))

        label = " and ".join(keywords)
        if matches:
            return f"Candidates matching {label} experience:\n" + "\n".join(f"- {name}" for name in matches)
        return f"No candidates found with {label} experience."

    @staticmethod
    def _candidate_matches_terms(candidate: Dict[str, Any], terms: List[str]) -> bool:
        searchable = " ".join([
            candidate.get('full_text', ''),
            candidate.get('experience_summary', ''),
            " ".join(candidate.get('skills', [])) if isinstance(candidate.get('skills'), list) else str(candidate.get('skills', '')),
            " ".join(candidate.get('education', [])) if isinstance(candidate.get('education'), list) else str(candidate.get('education', '')),
        ]).lower()

        aliases = {
            "nlp": ["nlp", "natural language processing"],
            "aws": ["aws", "amazon web services"],
            "rag": ["rag", "retrieval augmented generation", "retrieval-augmented generation"],
        }
        for term in terms:
            options = aliases.get(term.lower(), [term.lower()])
            if not any(option in searchable for option in options):
                return False
        return True

    @staticmethod
    def _generate_project_keyword_answer(candidates: List[Dict], keyword: str) -> str:
        """Generate expected answer for project or experience keyword searches."""
        matches = []
        keyword_lower = keyword.lower()
        for candidate in candidates:
            searchable = " ".join([
                candidate.get('full_text', ''),
                candidate.get('experience_summary', ''),
                " ".join(candidate.get('projects', [])) if isinstance(candidate.get('projects', []), list) else str(candidate.get('projects', '')),
            ]).lower()
            if keyword_lower in searchable:
                matches.append(candidate.get('candidate_name', 'Unknown'))

        if matches:
            return ", ".join(matches)
        return f"No candidates found with {keyword} project evidence."
    
    @staticmethod
    def _generate_skill_search_answer(candidates: List[Dict], jd_data: Dict) -> str:
        """Generate expected answer for skill search."""
        if not candidates or not jd_data.get('required_skills'):
            return "No candidates found with the specified skills."
        
        matching_candidates = []
        for candidate in candidates:
            candidate_skills_lower = [s.lower() for s in candidate.get('skills', [])]
            required_lower = [s.lower() for s in jd_data.get('required_skills', [])]
            
            if any(skill in candidate_skills_lower for skill in required_lower):
                matching_candidates.append(candidate['candidate_name'])
        
        if matching_candidates:
            return f"Candidates with required skills: {', '.join(matching_candidates)}"
        else:
            return "No candidates found with the specified skills."
    
    @staticmethod
    def _generate_ranking_explanation(candidate: Dict, jd_data: Dict) -> str:
        """Generate expected answer for ranking explanation."""
        return f"""Ranked first because of the highest matching score against the JD.
- Candidate: {candidate['candidate_name']}
- Matching Score: {candidate['final_score']:.1%}
- Matched Skills: {', '.join(candidate.get('matched_required_skills', []) + candidate.get('matched_preferred_skills', [])) or 'None recorded'}
- Missing Required Skills: {', '.join(candidate.get('missing_required_skills', [])) or 'None recorded'}
- Experience Alignment: {candidate['experience_match']:.1%}
- Education Alignment: {candidate['education_match']:.1%}
"""
    
    @staticmethod
    def _generate_comparison(candidate1: Dict, candidate2: Dict, jd_data: Dict) -> str:
        """Generate expected answer for comparison."""
        return f"""Comparison generated from ranking data.

{candidate1['candidate_name']}:
- Overall Score: {candidate1['final_score']:.1%}
- Required Skills Matched: {', '.join(candidate1.get('matched_required_skills', [])) or 'None recorded'}
- Missing Required Skills: {', '.join(candidate1.get('missing_required_skills', [])) or 'None recorded'}
- Experience: {candidate1.get('experience_summary', 'Not recorded')}
- Education: {', '.join(candidate1.get('education', [])) or 'Not recorded'}
- Rank Position: {candidate1.get('rank', 'N/A')}

{candidate2['candidate_name']}:
- Overall Score: {candidate2['final_score']:.1%}
- Required Skills Matched: {', '.join(candidate2.get('matched_required_skills', [])) or 'None recorded'}
- Missing Required Skills: {', '.join(candidate2.get('missing_required_skills', [])) or 'None recorded'}
- Experience: {candidate2.get('experience_summary', 'Not recorded')}
- Education: {', '.join(candidate2.get('education', [])) or 'Not recorded'}
- Rank Position: {candidate2.get('rank', 'N/A')}
"""
    
    @staticmethod
    def _generate_experience_answer(candidates: List[Dict], jd_data: Dict) -> str:
        """Generate expected answer for experience search."""
        candidates_with_exp = [c['candidate_name'] for c in candidates 
                               if c.get('experience_summary')]
        
        if candidates_with_exp:
            return f"Candidates with relevant experience: {', '.join(candidates_with_exp[:5])}"
        else:
            return "No candidates found with documented experience."
    
    def calculate_precision_recall(self, retrieved_docs: List[Dict],
                                   relevant_docs: List[Dict],
                                   k: int = 5) -> Dict[str, float]:
        """
        Calculate Precision@K and Recall@K.
        
        Args:
            retrieved_docs: Retrieved documents
            relevant_docs: Relevant documents
            k: K value for metrics
            
        Returns:
            Dict with precision and recall scores
        """
        # Get top K retrieved docs
        top_k_retrieved = retrieved_docs[:k]
        
        # Count relevant docs in top K
        relevant_count = 0
        for retrieved in top_k_retrieved:
            for relevant in relevant_docs:
                if retrieved.get('metadata', {}).get('candidate_name') == \
                   relevant.get('metadata', {}).get('candidate_name'):
                    relevant_count += 1
        
        # Calculate metrics
        precision = relevant_count / len(top_k_retrieved) if top_k_retrieved else 0
        recall = relevant_count / len(relevant_docs) if relevant_docs else 0
        
        return {
            'precision_at_k': precision,
            'recall_at_k': recall,
            'k': k
        }

    def calculate_answer_precision_recall(self, generated_answer: str,
                                          ground_truth: str,
                                          k: int = 5) -> Dict[str, float]:
        """Calculate simple entity precision/recall from generated answer against ground truth names."""
        expected_names = self._extract_candidate_names(ground_truth)
        predicted_names = self._extract_candidate_names(generated_answer)[:k]

        if not expected_names:
            return {'precision_at_k': 0.0, 'recall_at_k': 0.0, 'k': k}

        expected = {name.lower() for name in expected_names}
        predicted = {name.lower() for name in predicted_names}
        correct = len(expected & predicted)
        precision = correct / len(predicted) if predicted else 0.0
        recall = correct / len(expected) if expected else 0.0
        return {'precision_at_k': precision, 'recall_at_k': recall, 'k': k}

    @staticmethod
    def _extract_candidate_names(text: str) -> List[str]:
        if not text:
            return []

        names = []
        for line in text.splitlines():
            cleaned = line.strip().strip("-*• ").strip()
            if not cleaned or ":" in cleaned[:20]:
                continue
            match = re.match(r"([A-Z][A-Za-z'.-]*(?:\s+[A-Z][A-Za-z'.-]*){0,3})", cleaned)
            if match:
                name = match.group(1).strip()
                if name.lower() not in {"candidates", "no candidates", "ranked", "comparison"}:
                    names.append(name)
        return list(dict.fromkeys(names))
    
    def evaluate_faithfulness(self, generated_answer: str,
                             source_documents: List[Dict]) -> float:
        """
        Evaluate faithfulness of answer to source documents.
        
        Uses simple heuristic: check if key entities from documents appear in answer.
        
        Args:
            generated_answer: Generated answer text
            source_documents: Source documents used
            
        Returns:
            Faithfulness score (0-1)
        """
        if not source_documents:
            return 0.0
        
        answer_lower = generated_answer.lower()
        relevant_entities_found = 0
        
        for doc in source_documents:
            # Extract candidate names and key info
            metadata = doc.get('metadata', {})
            candidate_name = metadata.get('candidate_name', '').lower()
            
            if candidate_name and candidate_name in answer_lower:
                relevant_entities_found += 1
        
        faithfulness = relevant_entities_found / len(source_documents) if source_documents else 0
        return min(faithfulness, 1.0)
    
    def evaluate_answer_relevancy(self, question: str, answer: str) -> float:
        """
        Evaluate relevancy of answer to question.
        
        Uses simple heuristic: check for question keywords in answer.
        
        Args:
            question: Original question
            answer: Generated answer
            
        Returns:
            Relevancy score (0-1)
        """
        if not answer:
            return 0.0
        
        # Extract keywords from question
        keywords = question.lower().split()
        keywords = [k for k in keywords if len(k) > 3]  # Filter short words
        
        # Check how many keywords appear in answer
        answer_lower = answer.lower()
        matching_keywords = sum(1 for k in keywords if k in answer_lower)
        
        relevancy = matching_keywords / len(keywords) if keywords else 0.5
        return min(relevancy, 1.0)

    def evaluate_ranking_quality(self, generated_answer: str,
                                 ranking_data: List[Dict[str, Any]]) -> float:
        """Check whether ranking answers mention candidate names and ranking score details."""
        if not generated_answer or not ranking_data:
            return 0.0

        answer_lower = generated_answer.lower()
        top_names = [candidate.get('candidate_name', '').lower() for candidate in ranking_data[:2]]
        name_hits = sum(1 for name in top_names if name and name in answer_lower)
        score_terms = sum(
            1 for term in ['score', 'skill', 'experience', 'education']
            if term in answer_lower
        )
        return min(((name_hits / max(len(top_names), 1)) * 0.5) + ((score_terms / 4) * 0.5), 1.0)
    
    def record_evaluation(self, timestamp: str, question: str,
                         ground_truth: str, generated_answer: str,
                         precision_k: float, recall_k: float,
                         faithfulness: float, relevancy: float,
                         ranking_quality: float):
        """
        Record evaluation metrics for a single evaluation.
        
        Args:
            timestamp: Evaluation timestamp
            question: Question asked
            ground_truth: Ground truth answer
            generated_answer: Generated answer
            precision_k: Precision@K score
            recall_k: Recall@K score
            faithfulness: Faithfulness score
            relevancy: Answer relevancy score
            ranking_quality: Ranking quality score
        """
        self.evaluations.append({
            'timestamp': timestamp,
            'question': question,
            'ground_truth': ground_truth,
            'generated_answer': generated_answer,
            'precision_at_k': precision_k,
            'recall_at_k': recall_k,
            'faithfulness': faithfulness,
            'answer_relevancy': relevancy,
            'ranking_quality': ranking_quality,
            'ground_truth_available': bool(ground_truth),
        })
        self.export_to_excel()

    @staticmethod
    def find_ground_truth_for_question(question: str, qa_pairs: List[Dict[str, str]]) -> str:
        """Return the expected answer for the closest generated QA question."""
        if not question or not qa_pairs:
            return ""

        normalized_question = EvaluationFramework._normalize_question(question)
        best_score = 0.0
        best_answer = ""

        for pair in qa_pairs:
            expected_question = pair.get('question', '')
            normalized_expected = EvaluationFramework._normalize_question(expected_question)
            if not normalized_expected:
                continue

            if normalized_question == normalized_expected:
                return pair.get('expected_answer', '')

            score = SequenceMatcher(None, normalized_question, normalized_expected).ratio()
            if score > best_score:
                best_score = score
                best_answer = pair.get('expected_answer', '')

        return best_answer if best_score >= 0.72 else ""

    @staticmethod
    def _normalize_question(question: str) -> str:
        """Normalize question text so generated QA can be matched to user wording."""
        normalized = question.lower().strip()
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def export_to_excel(self, filename: Optional[str] = None) -> bool:
        """
        Export chatbot evaluation metrics to an Excel file for backend monitoring.
        This is intentionally backend-only and should not be displayed in the UI.
        """
        try:
            filepath = Path(filename) if filename else self.export_path
            filepath.parent.mkdir(parents=True, exist_ok=True)

            import pandas as pd

            df = pd.DataFrame(self.evaluations, columns=self.EXCEL_COLUMNS)
            df.to_excel(filepath, index=False, sheet_name="chatbot_metrics")
            return True
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False

    def _ensure_excel_workbook(self) -> None:
        """Create the backend metrics workbook with headers if it does not exist."""
        if not self.export_path.exists():
            self.export_to_excel()

    def _load_existing_evaluations(self) -> List[Dict[str, Any]]:
        """Load existing backend metric rows so reruns do not wipe prior scores."""
        try:
            if not self.export_path.exists():
                return []

            import pandas as pd

            df = pd.read_excel(self.export_path, sheet_name="chatbot_metrics")
            if df.empty:
                return []

            df = df.where(pd.notnull(df), "")
            return df.to_dict(orient="records")
        except Exception as e:
            print(f"Error loading existing Excel metrics: {e}")
            return []
    
    def export_to_json(self, filename: Optional[str] = None) -> bool:
        """
        Export evaluation results to JSON.
        
        Args:
            filename: Optional custom filename
            
        Returns:
            True if successful
        """
        try:
            if filename:
                filepath = Path(filename)
            else:
                timestamp = datetime.now().isoformat()
                filepath = self.export_path.parent / f"evaluation_{timestamp}.json"
            
            with open(filepath, 'w') as f:
                json.dump(self.evaluations, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False
    
    def get_summary_metrics(self) -> Dict[str, float]:
        """
        Get summary metrics across all evaluations.
        
        Returns:
            Dictionary with average metrics
        """
        if not self.evaluations:
            return {}
        
        return {
            'avg_precision': sum(e['precision_at_k'] for e in self.evaluations) / len(self.evaluations),
            'avg_recall': sum(e['recall_at_k'] for e in self.evaluations) / len(self.evaluations),
            'avg_faithfulness': sum(e['faithfulness'] for e in self.evaluations) / len(self.evaluations),
            'avg_relevancy': sum(e['answer_relevancy'] for e in self.evaluations) / len(self.evaluations),
            'avg_ranking_quality': sum(e['ranking_quality'] for e in self.evaluations) / len(self.evaluations),
            'total_evaluations': len(self.evaluations)
        }
