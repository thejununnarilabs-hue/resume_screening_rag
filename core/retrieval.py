"""Retrieval strategies for chatbot context augmentation."""

from typing import List, Dict, Any, Optional
import re

from .candidate_extractor import CandidateExtractor


class RetrievalEngine:
    """Handles semantic search and context retrieval from ChromaDB."""

    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
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
    ADDRESS_PATTERN = re.compile(
        r"\b(address|location|city|state|country|street|road|avenue|lane|linkedin|github|portfolio)\b",
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
    EDUCATION_PATTERN = re.compile(
        r"\b(B\.?\s?(?:Tech|E|Sc|S|A|Com|CA)|M\.?\s?(?:Tech|E|Sc|S|A|Com|CA)|"
        r"Bachelor(?:'s)?|Master(?:'s)?|MBA|MCA|BCA|BBA|Ph\.?\s?D\.?|Doctorate|"
        r"Diploma|Associate|University|College|Institute|School|Academy|CGPA|GPA|(?:19|20)\d{2})\b",
        re.IGNORECASE,
    )
    
    def __init__(self, chroma_manager, embedding_model, ranking_data: Optional[List[Dict]] = None):
        """
        Initialize retrieval engine.
        
        Args:
            chroma_manager: ChromaDB manager instance
            embedding_model: Embedding model instance
            ranking_data: List of ranked candidates
        """
        self.chroma_manager = chroma_manager
        self.embedding_model = embedding_model
        self.ranking_data = ranking_data or []

    @staticmethod
    def query_terms(query: str) -> List[str]:
        """Extract useful terms for direct candidate matching."""
        terms = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{1,}", query)
        stop_words = {
            "which", "candidate", "candidates", "with", "have", "has", "list",
            "compare", "and", "the", "who", "worked", "work", "on", "experience",
            "skills", "skill", "certifications", "certification", "projects",
            "project", "ranked", "first", "why", "was", "among", "from",
            "does", "do", "person", "people", "using", "used", "use", "only",
            "missing", "requested", "rank", "ranking", "current", "session",
            "as", "for", "of", "in", "to", "a", "an", "by", "about", "show",
        }
        return [term for term in terms if term.lower() not in stop_words]
    
    def retrieve_similar_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve similar documents using semantic search.
        
        Args:
            query: User query text
            top_k: Number of results to retrieve
            
        Returns:
            List of retrieved documents with metadata
        """
        try:
            # Encode query
            query_embedding = self.embedding_model.encode_text(query)
            
            # Search in ChromaDB
            results = self.chroma_manager.search(
                query_embedding.tolist(),
                n_results=top_k
            )
            
            if 'error' in results:
                return []
            
            # Format results
            retrieved_docs = []
            
            documents = results.get('documents', [[]])
            ids = results.get('ids', [[]])
            metadatas = results.get('metadatas', [[]])
            distances = results.get('distances', [[]])

            documents = documents[0] if documents and isinstance(documents[0], list) else documents
            ids = ids[0] if ids and isinstance(ids[0], list) else ids
            metadatas = metadatas[0] if metadatas and isinstance(metadatas[0], list) else metadatas
            distances = distances[0] if distances and isinstance(distances[0], list) else distances

            for i in range(len(documents)):
                doc = {
                    'id': ids[i] if i < len(ids) else '',
                    'text': documents[i] if i < len(documents) else '',
                    'metadata': metadatas[i] if i < len(metadatas) else {},
                    'distance': distances[i] if i < len(distances) else 1.0
                }
                retrieved_docs.append(doc)
            
            return retrieved_docs
        
        except Exception as e:
            print(f"Error in semantic retrieval: {e}")
            return []
    
    def rerank_context(self, retrieved_docs: List[Dict[str, Any]],
                      query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Rerank retrieved documents for relevance to query.
        
        Args:
            retrieved_docs: List of retrieved documents
            query: Original query
            top_k: Number of top reranked documents to return
            
        Returns:
            Reranked documents
        """
        if not retrieved_docs:
            return []
        
        # Encode query once
        query_embedding = self.embedding_model.encode_text(query)
        
        # Calculate relevance scores
        scored_docs = []
        for doc in retrieved_docs:
            # Get text embedding (if stored) or calculate
            if 'embedding' in doc['metadata']:
                doc_embedding = doc['metadata']['embedding']
            else:
                # This would require recalculating - skip for efficiency
                doc_embedding = None
            
            # Calculate relevance
            relevance_score = 1.0 - doc.get('distance', 0.5)  # Convert distance to similarity
            
            scored_docs.append({
                'doc': doc,
                'relevance_score': relevance_score
            })
        
        # Sort by relevance
        scored_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Return top K with scores
        return [item['doc'] for item in scored_docs[:top_k]]
    
    def parse_candidate_references(self, query: str) -> List[Dict[str, Any]]:
        """
        Parse candidate reference from query (e.g., "candidate 1", "candidate 5").
        
        Args:
            query: User query
            
        Returns:
            Candidate info rows if found
        """
        references = []
        seen_positions = set()

        def add_reference(candidate_number: int) -> None:
            if 1 <= candidate_number <= len(self.ranking_data) and candidate_number not in seen_positions:
                seen_positions.add(candidate_number)
                references.append(self.ranking_data[candidate_number - 1])

        grouped_pattern = r'candidate\s+((?:\d+\s*(?:,|and)?\s*)+)'
        for group in re.findall(grouped_pattern, query, re.IGNORECASE):
            for match in re.findall(r'\d+', group):
                add_reference(int(match))

        pattern = r'candidate\s+(\d+)'
        for match in re.findall(pattern, query, re.IGNORECASE):
            add_reference(int(match))

        return references

    @staticmethod
    def is_ranking_query(query: str) -> bool:
        """Return True when the user is asking about the current ranking list."""
        query_lower = query.lower()
        ranking_words = [
            "rank", "ranked", "ranking", "top", "first", "second", "third",
            "candidate 1", "candidate 2", "candidate 3", "candidate 4", "candidate 5",
        ]
        if any(word in query_lower for word in ranking_words):
            return True
        return bool(re.search(r"\bcandidate\s+\d+\b", query_lower))

    def is_skill_query(self, query: str) -> bool:
        """Return True when the query asks for skill possession or skill matching."""
        query_lower = query.lower()
        terms = self.query_terms(query)
        if not terms:
            return False
        skill_words = ["skill", "skills", "has", "have", "does", "with", "missing"]
        if any(word in query_lower for word in skill_words):
            return True
        if "," in query and any(word in query_lower for word in ["candidate", "candidates", "who", "which", "list"]):
            return True
        return len(terms) >= 2 and any(word in query_lower for word in ["candidate", "candidates", "who", "which", "list"])

    def parse_candidate_reference(self, query: str) -> Optional[Dict[str, Any]]:
        """Return the first candidate reference for backwards compatibility."""
        references = self.parse_candidate_references(query)
        return references[0] if references else None
    
    def retrieve_candidate_evidence(self, candidate_name: str) -> List[Dict[str, Any]]:
        """
        Retrieve all evidence chunks for a candidate.
        
        Args:
            candidate_name: Name of candidate
            
        Returns:
            List of candidate's resume chunks
        """
        try:
            results = self.chroma_manager.get_candidate_chunks(candidate_name)
            
            if not results or 'documents' not in results:
                return []
            
            # Format as documents
            documents = []
            for i in range(len(results.get('documents', []))):
                doc = {
                    'text': results['documents'][i],
                    'metadata': results['metadatas'][i] if i < len(results.get('metadatas', [])) else {},
                    'candidate_name': candidate_name
                }
                documents.append(doc)
            
            return documents
        
        except Exception as e:
            print(f"Error retrieving candidate evidence: {e}")
            return []
    
    def build_context_for_answer(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Build comprehensive context for answering a query.
        
        Args:
            query: User query
            top_k: Number of relevant documents to retrieve
            
        Returns:
            Context dictionary with retrieved documents and metadata
        """
        context = {
            'query': query,
            'retrieved_documents': [],
            'candidate_references': [],
            'context_type': 'semantic'
        }
        
        candidate_refs = self.parse_candidate_references(query)
        if candidate_refs:
            context['candidate_references'].extend(candidate_refs)
            context['context_type'] = 'candidate_specific'

        if self.is_ranking_query(query) or self.is_skill_query(query):
            context['context_type'] = 'ranking'
            context['ranking_data'] = self.ranking_data
            return context
        
        retrieval_k = min(max(top_k, 8), 12)
        retrieved_docs = self.retrieve_similar_documents(query, retrieval_k)
        
        reranked_docs = self.rerank_context(retrieved_docs, query, top_k=3)

        candidate_evidence = []
        for candidate in candidate_refs:
            candidate_evidence.extend(
                self.retrieve_candidate_evidence(candidate.get('candidate_name', ''))[:4]
            )
        if candidate_evidence:
            reranked_docs = candidate_evidence + reranked_docs
        
        context['retrieved_documents'] = reranked_docs
        context['ranking_data'] = self.ranking_data
        
        return context

    def direct_answer(self, query: str, context: Dict[str, Any]) -> Optional[str]:
        """Answer common structured questions from retrieved evidence and ranking data without an LLM roundtrip."""
        query_lower = query.lower()
        ranking_data = context.get('ranking_data') or self.ranking_data
        if not ranking_data:
            return None

        candidate_refs = self.parse_candidate_references(query)
        if "compare" in query_lower and len(candidate_refs) >= 2:
            return self._format_comparison(candidate_refs[0], candidate_refs[1])

        terms = self.query_terms(query)
        if terms and (self.is_skill_query(query) or candidate_refs):
            requested_skills = self.parse_requested_skills(query, terms, ranking_data)
            candidates_to_check = candidate_refs or ranking_data
            return self._format_skill_matches(
                candidates_to_check,
                requested_skills,
                include_unmatched=bool(candidate_refs),
            )

        if self.is_ranking_query(query):
            if ("why" in query_lower or "reason" in query_lower) and candidate_refs:
                return self._format_ranking_explanation(candidate_refs[0])

            ordinal_candidate = self._candidate_from_ordinal(query_lower, ranking_data)
            if ("why" in query_lower or "reason" in query_lower) and ordinal_candidate:
                return self._format_ranking_explanation(ordinal_candidate)

            top_count = self._top_count(query_lower)
            if top_count:
                return self._format_candidate_list(ranking_data[:top_count], f"Top {top_count} candidates")

            if candidate_refs:
                return self._format_candidate_summary(candidate_refs[0])

            if ordinal_candidate:
                return self._format_candidate_summary(ordinal_candidate)

        if not terms:
            return None

        if any(word in query_lower for word in ["which", "who", "list", "compare"]):
            matches = self._match_candidates_by_terms(terms, ranking_data)
            if matches:
                label = " and ".join(terms)
                lines = [f"Candidates matching {label} experience:"]
                for candidate in matches:
                    evidence = self._candidate_evidence_summary(candidate, terms)
                    lines.append(f"- {candidate.get('candidate_name')}: {evidence}")
                return "\n".join(lines)
            return f"No candidates found with {' and '.join(terms)} evidence."

        return None

    @staticmethod
    def _candidate_skill_values(candidate: Dict[str, Any]) -> List[str]:
        values = []
        for key in ['matched_required_skills', 'matched_preferred_skills', 'skills']:
            raw_value = candidate.get(key, [])
            if isinstance(raw_value, list):
                values.extend(raw_value)
            elif raw_value:
                values.append(raw_value)
        return RetrievalEngine._clean_list(values)

    @staticmethod
    def parse_requested_skills(
        query: str,
        terms: List[str],
        ranking_data: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Return only recognized skill names requested by the user."""
        ranking_data = ranking_data or []
        skill_names = set(CandidateExtractor.SKILL_KEYWORDS)
        for candidate in ranking_data:
            skill_names.update(RetrievalEngine._candidate_skill_values(candidate))

        aliases = {
            "natural language processing": "NLP",
            "google cloud platform": "GCP",
            "amazon web services": "AWS",
            "rest": "REST API",
        }

        requested = []
        query_lower = query.lower()
        known_by_lower = {skill.lower(): skill for skill in skill_names}

        for phrase, canonical in aliases.items():
            if re.search(rf"\b{re.escape(phrase)}\b", query_lower, flags=re.IGNORECASE):
                requested.append(canonical)

        for skill in sorted(skill_names, key=len, reverse=True):
            if re.search(rf"\b{re.escape(skill)}\b", query, flags=re.IGNORECASE):
                requested.append(skill)

        for term in terms:
            canonical = known_by_lower.get(term.lower())
            if canonical:
                requested.append(canonical)

        return RetrievalEngine._clean_list(requested)

    @staticmethod
    def _skills_equivalent(candidate_skill: str, requested_skill: str) -> bool:
        candidate_lower = candidate_skill.lower()
        requested_lower = requested_skill.lower()
        aliases = {
            "nlp": {"nlp", "natural language processing"},
            "natural language processing": {"nlp", "natural language processing"},
            "aws": {"aws", "amazon web services"},
            "amazon web services": {"aws", "amazon web services"},
            "gcp": {"gcp", "google cloud", "google cloud platform"},
            "google cloud": {"gcp", "google cloud", "google cloud platform"},
            "google cloud platform": {"gcp", "google cloud", "google cloud platform"},
            "rest api": {"rest", "rest api"},
            "rest": {"rest", "rest api"},
        }
        if candidate_lower == requested_lower:
            return True
        if requested_lower in aliases and candidate_lower in aliases[requested_lower]:
            return True
        if candidate_lower in aliases and requested_lower in aliases[candidate_lower]:
            return True
        return bool(re.search(rf"\b{re.escape(requested_lower)}\b", candidate_lower))

    @staticmethod
    def _skill_matches(candidate_skills: List[str], requested_skills: List[str]) -> Dict[str, List[str]]:
        matched = []
        missing = []

        for requested in requested_skills:
            has_skill = any(
                RetrievalEngine._skills_equivalent(candidate_skill, requested)
                for candidate_skill in candidate_skills
            )
            if has_skill:
                matched.append(requested)
            else:
                missing.append(requested)

        return {"matched": matched, "missing": missing}

    @staticmethod
    def _format_skill_matches(
        candidates: List[Dict[str, Any]],
        requested_skills: List[str],
        include_unmatched: bool = False,
    ) -> str:
        requested_skills = RetrievalEngine._clean_list(requested_skills)
        if not requested_skills:
            return "No requested skills were found in the question."

        lines = []
        any_match = False

        for candidate in candidates:
            candidate_skills = RetrievalEngine._candidate_skill_values(candidate)
            result = RetrievalEngine._skill_matches(candidate_skills, requested_skills)
            if not result["matched"] and not include_unmatched:
                continue

            any_match = any_match or bool(result["matched"])
            resume_file = RetrievalEngine._clean_resume_filename(candidate.get('pdf_file', 'Not recorded'))
            candidate_block = [
                f"Candidate {candidate.get('rank', '?')}:",
                f"Name: {candidate.get('candidate_name', 'Unknown')} ({resume_file})",
                f"Matched Skills: {', '.join(result['matched'])}",
            ]
            if result["missing"]:
                candidate_block.append(f"Missing Skills: {', '.join(result['missing'])}")
            lines.append("\n".join(candidate_block))

        if any_match or (include_unmatched and len(lines) > 1):
            return "\n\n".join(lines)

        scoped_label = "selected ranked candidates" if candidates else "ranked candidates"
        return (
            f"No {scoped_label} match any of the requested skills: "
            f"{', '.join(requested_skills)}."
        )

    def _match_candidates_by_terms(self, terms: List[str], ranking_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        matches = []
        lowered_terms = [term.lower() for term in terms]
        for candidate in ranking_data:
            searchable = " ".join([
                candidate.get('candidate_name', ''),
                " ".join(candidate.get('matched_required_skills', [])),
                " ".join(candidate.get('matched_preferred_skills', [])),
                " ".join(candidate.get('skills', [])) if isinstance(candidate.get('skills'), list) else str(candidate.get('skills', '')),
                candidate.get('experience_summary', ''),
                " ".join(candidate.get('education', [])) if isinstance(candidate.get('education'), list) else str(candidate.get('education', '')),
            ]).lower()
            if all(term in searchable for term in lowered_terms):
                matches.append(candidate)
        return matches

    @staticmethod
    def _candidate_evidence_summary(candidate: Dict[str, Any], terms: List[str]) -> str:
        matched = candidate.get('matched_required_skills', []) + candidate.get('matched_preferred_skills', [])
        relevant = [skill for skill in matched if any(term.lower() in skill.lower() for term in terms)]
        if relevant:
            return f"matched skills: {', '.join(relevant)}"
        if candidate.get('experience_summary'):
            return candidate.get('experience_summary')
        return f"ranking score {candidate.get('final_score', 0):.1f}%"

    @staticmethod
    def _top_count(query_lower: str) -> Optional[int]:
        match = re.search(r"\btop\s+(\d+)\b", query_lower)
        if match:
            return max(1, int(match.group(1)))
        if "top candidates" in query_lower:
            return 5
        return None

    @staticmethod
    def _candidate_from_ordinal(query_lower: str, ranking_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        ordinal_positions = {
            "first": 1,
            "second": 2,
            "third": 3,
            "fourth": 4,
            "fifth": 5,
        }
        for word, position in ordinal_positions.items():
            if re.search(rf"\b{word}\b", query_lower) and position <= len(ranking_data):
                return ranking_data[position - 1]
        return None

    @staticmethod
    def _format_candidate_list(candidates: List[Dict[str, Any]], title: str) -> str:
        if not candidates:
            return "No ranked candidates are available in the current session."

        lines = [f"{title} from the current ranking list:"]
        for candidate in candidates:
            lines.append(
                f"- Candidate {candidate.get('rank', '?')}: "
                f"{candidate.get('candidate_name', 'Unknown')} - "
                f"Score: {candidate.get('final_score', 0):.1f}%"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_candidate_summary(candidate: Dict[str, Any]) -> str:
        skills = candidate.get('matched_required_skills', []) + candidate.get('matched_preferred_skills', [])
        return "\n".join([
            f"Candidate {candidate.get('rank', '?')} from the current ranking list:",
            f"Name: {candidate.get('candidate_name', 'Unknown')}",
            f"Resume File Name: {candidate.get('pdf_file', 'Not recorded')}",
            f"Score: {candidate.get('final_score', 0):.1f}%",
            f"Matched skills: {', '.join(skills) or 'None recorded'}",
            f"Experience match: {candidate.get('experience_match', 0):.1%}",
            f"Education match: {candidate.get('education_match', 0):.1%}",
        ])

    @staticmethod
    def _format_ranking_explanation(candidate: Dict[str, Any]) -> str:
        skills = candidate.get('matched_required_skills', []) + candidate.get('matched_preferred_skills', [])
        return "\n".join([
            f"Candidate {candidate.get('rank', '?')} is ranked at that position because of the current JD match score.",
            f"Candidate: {candidate.get('candidate_name', 'Unknown')}",
            f"Resume File Name: {candidate.get('pdf_file', 'Not recorded')}",
            f"Score: {candidate.get('final_score', 0):.1f}%",
            f"Matched skills: {', '.join(skills) or 'None recorded'}",
            f"Experience match: {candidate.get('experience_match', 0):.1%}",
            f"Education match: {candidate.get('education_match', 0):.1%}",
        ])     

    @staticmethod
    def _format_comparison(candidate1: Dict[str, Any], candidate2: Dict[str, Any]) -> str:
        if RetrievalEngine._same_candidate(candidate1, candidate2):
            return "Both selected candidates are identical. Please select two different candidates for comparison."

        sanitized1 = RetrievalEngine._comparison_candidate(candidate1)
        sanitized2 = RetrievalEngine._comparison_candidate(candidate2)
        label1 = f"Candidate {candidate1.get('rank', 1)}"
        label2 = f"Candidate {candidate2.get('rank', 2)}"

        def block(label: str, candidate: Dict[str, Any]) -> str:
            return "\n".join([
                f"{label}:",
                f"- Name: {candidate['name']} ({candidate['resume_file']})",
                f"- Match Score: {candidate['match_score']}",
                f"- Skills: {candidate['skills']}",
                f"- Experience Summary: {candidate['experience_summary']}",
                f"- Education: {candidate['education']}",
            ])

        differences = "\n".join([
            "Key Differences:",
            f"- Skills Difference: {RetrievalEngine._skills_difference(sanitized1, sanitized2, label1, label2)}",
            f"- Experience Difference: {RetrievalEngine._experience_difference(candidate1, candidate2, label1, label2)}",
            f"- Education Difference: {RetrievalEngine._education_difference(sanitized1, sanitized2, label1, label2)}",
            f"- Match Score Difference: {RetrievalEngine._score_difference(candidate1, candidate2, label1, label2)}",
        ])

        return "\n\n".join([block(label1, sanitized1), block(label2, sanitized2), differences])

    @staticmethod
    def _same_candidate(candidate1: Dict[str, Any], candidate2: Dict[str, Any]) -> bool:
        file1 = str(candidate1.get('pdf_file', '')).strip().lower()
        file2 = str(candidate2.get('pdf_file', '')).strip().lower()
        if file1 and file2:
            return file1 == file2

        name1 = str(candidate1.get('candidate_name', '')).strip().lower()
        name2 = str(candidate2.get('candidate_name', '')).strip().lower()
        return bool(name1 and name1 == name2)

    @staticmethod
    def _comparison_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
        skills = candidate.get('matched_required_skills', []) + candidate.get('matched_preferred_skills', [])
        if not skills:
            skills = candidate.get('skills', [])

        education = candidate.get('education', [])
        if not isinstance(education, list):
            education = [str(education)]

        clean_skills = RetrievalEngine._clean_list(skills)
        clean_education = RetrievalEngine._clean_education(education)

        return {
            'name': RetrievalEngine._clean_text(candidate.get('candidate_name', 'Unknown')) or 'Unknown',
            'resume_file': RetrievalEngine._clean_resume_filename(candidate.get('pdf_file', 'Not recorded')),
            'match_score': f"{candidate.get('final_score', 0):.1f}%",
            'skills': ', '.join(clean_skills) or 'None recorded',
            'skills_list': clean_skills,
            'experience_summary': RetrievalEngine._clean_text(candidate.get('experience_summary', '')) or 'Not recorded',
            'education': ', '.join(clean_education) or 'Not recorded',
            'education_list': clean_education,
        }

    @staticmethod
    def _clean_text(value: Any) -> str:
        text = str(value or "")
        cleaned_lines = []
        seen = set()
        for raw_line in re.split(r"[\r\n]+", text):
            line = " ".join(raw_line.strip().split())
            if not line:
                continue
            line = RetrievalEngine.EMAIL_PATTERN.sub("", line)
            line = RetrievalEngine.PHONE_PATTERN.sub("", line)
            line = RetrievalEngine.URL_PATTERN.sub("", line)
            line = re.sub(r"\b(?:linkedin|github|portfolio)\b.*", "", line, flags=re.IGNORECASE)
            line = re.sub(r"\b(?:email|e-mail|phone|mobile|contact)\b\s*[:\-]?", "", line, flags=re.IGNORECASE)
            line = RetrievalEngine.LOCATION_VALUE_PATTERN.sub("", line)
            if RetrievalEngine.ADDRESS_PATTERN.search(line):
                continue
            line = re.sub(r"\s{2,}", " ", line)
            line = re.sub(r"\s+([,|/-])\s+", " ", line)
            line = line.strip(" |,-:")
            key = line.lower()
            if line and key not in seen:
                seen.add(key)
                cleaned_lines.append(line)
        return " ".join(cleaned_lines)

    @staticmethod
    def _clean_list(values: List[Any]) -> List[str]:
        cleaned = []
        seen = set()
        for value in values:
            item = RetrievalEngine._clean_text(value)
            if not item:
                continue
            key = item.lower()
            if key not in seen:
                seen.add(key)
                cleaned.append(item)
        return cleaned

    @staticmethod
    def _clean_education(values: List[Any]) -> List[str]:
        cleaned = []
        for value in values:
            item = RetrievalEngine._clean_text(value)
            if item and RetrievalEngine.EDUCATION_PATTERN.search(item):
                cleaned.append(item)
        return RetrievalEngine._clean_list(cleaned)

    @staticmethod
    def _clean_resume_filename(value: Any) -> str:
        filename = str(value or "").strip()
        filename = filename.replace("\\", "/").split("/")[-1]
        return RetrievalEngine._clean_text(filename) or "Not recorded"

    @staticmethod
    def _skills_difference(candidate1: Dict[str, Any], candidate2: Dict[str, Any], label1: str, label2: str) -> str:
        skills1 = set(candidate1['skills_list'])
        skills2 = set(candidate2['skills_list'])
        only_a = sorted(skills1 - skills2)
        only_b = sorted(skills2 - skills1)
        parts = []
        if only_a:
            parts.append(f"{label1} only: {', '.join(only_a)}")
        if only_b:
            parts.append(f"{label2} only: {', '.join(only_b)}")
        return "; ".join(parts) or "No major skill difference recorded."

    @staticmethod
    def _experience_difference(candidate1: Dict[str, Any], candidate2: Dict[str, Any], label1: str, label2: str) -> str:
        exp1 = candidate1.get('experience_match', 0)
        exp2 = candidate2.get('experience_match', 0)
        if exp1 == exp2:
            return "Both candidates have the same experience alignment score."
        stronger = label1 if exp1 > exp2 else label2
        return f"{stronger} has higher experience alignment ({max(exp1, exp2):.1%} vs {min(exp1, exp2):.1%})."

    @staticmethod
    def _education_difference(candidate1: Dict[str, Any], candidate2: Dict[str, Any], label1: str, label2: str) -> str:
        edu1 = set(candidate1['education_list'])
        edu2 = set(candidate2['education_list'])
        only_a = sorted(edu1 - edu2)
        only_b = sorted(edu2 - edu1)
        parts = []
        if only_a:
            parts.append(f"{label1}: {', '.join(only_a)}")
        if only_b:
            parts.append(f"{label2}: {', '.join(only_b)}")
        return "; ".join(parts) or "No major education difference recorded."

    @staticmethod
    def _score_difference(candidate1: Dict[str, Any], candidate2: Dict[str, Any], label1: str, label2: str) -> str:
        score1 = candidate1.get('final_score', 0)
        score2 = candidate2.get('final_score', 0)
        difference = abs(score1 - score2)
        if difference == 0:
            return "Both candidates have the same match score."
        stronger = label1 if score1 > score2 else label2
        return f"{stronger} is higher by {difference:.1f} percentage points."
    
    def format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """
        Format retrieved context for LLM prompt.
        
        Args:
            context: Context dictionary from build_context_for_answer
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        if context.get('ranking_data'):
            context_parts.append("Current Ranking Information:")
            context_parts.append("-" * 40)
            referenced_names = {
                candidate.get('candidate_name')
                for candidate in context.get('candidate_references', [])
            }
            for candidate in context['ranking_data'][:10]:
                context_parts.append(f"Rank: {candidate.get('rank')}")
                context_parts.append(f"Name: {candidate.get('candidate_name')}")
                context_parts.append(f"Score: {candidate.get('final_score', 0):.2f}%")
                context_parts.append(f"Matched Required Skills: {', '.join(candidate.get('matched_required_skills', [])) or 'None recorded'}")
                context_parts.append(f"Matched Preferred Skills: {', '.join(candidate.get('matched_preferred_skills', [])) or 'None recorded'}")
                context_parts.append(f"Missing Required Skills: {', '.join(candidate.get('missing_required_skills', [])) or 'None recorded'}")
                context_parts.append(f"Experience Alignment: {candidate.get('experience_match', 0):.2%}")
                context_parts.append(f"Education Alignment: {candidate.get('education_match', 0):.2%}")
                if candidate.get('candidate_name') in referenced_names:
                    context_parts.append(f"Experience: {candidate.get('experience_summary') or 'Not recorded'}")
                    context_parts.append(f"Education: {', '.join(candidate.get('education', [])) or 'Not recorded'}")
                context_parts.append("")

        if context['retrieved_documents']:
            context_parts.append("Retrieved Resume Information:")
            context_parts.append("-" * 40)
            
            for i, doc in enumerate(context['retrieved_documents'], 1):
                metadata = doc.get('metadata', {})
                candidate_name = metadata.get('candidate_name', 'Unknown')
                
                context_parts.append(f"\n[Source {i}: {candidate_name}]")
                context_parts.append(doc.get('text', '')[:350])
                context_parts.append("")
        
        # Add candidate references
        if context['candidate_references']:
            context_parts.append("\nCandidate Information:")
            context_parts.append("-" * 40)
            
            for candidate in context['candidate_references']:
                context_parts.append(f"Rank: {candidate.get('rank')}")
                context_parts.append(f"Name: {candidate.get('candidate_name')}")
                context_parts.append(f"Score: {candidate.get('final_score', 0):.2f}%")
                context_parts.append("")
        
        return "\n".join(context_parts)
