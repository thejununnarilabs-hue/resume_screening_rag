"""Session state management for resume screening application."""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class SessionManager:
    """Manages session state, uploaded files, and cleanup."""
    
    def __init__(self, base_data_dir: str = "data"):
        self.base_data_dir = Path(base_data_dir)
        self.temp_resumes_dir = self.base_data_dir / "temp_resumes"
        self.extracted_candidates_dir = self.base_data_dir / "extracted_candidates"
        self.chroma_db_dir = self.base_data_dir / "chroma_db"
        self.ground_truth_dir = self.base_data_dir / "generated_ground_truth"
        self.chat_sessions_file = self.base_data_dir / "chat_sessions.json"
        
        # Ensure directories exist
        for dir_path in [self.temp_resumes_dir, self.extracted_candidates_dir, 
                         self.chroma_db_dir, self.ground_truth_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def cleanup_session_dirs(parent_dir: str = "data", prefix: str = "session_") -> None:
        """Remove old disposable Streamlit session folders."""
        parent_path = Path(parent_dir)
        if not parent_path.exists():
            return

        for legacy_dir in ["temp_resumes", "extracted_candidates", "chroma_db", "generated_ground_truth"]:
            legacy_path = parent_path / legacy_dir
            if legacy_path.exists() and legacy_path.is_dir():
                try:
                    shutil.rmtree(legacy_path)
                except Exception as e:
                    print(f"Error removing legacy session directory {legacy_path}: {e}")

        for session_dir in parent_path.glob(f"{prefix}*"):
            if session_dir.is_dir():
                try:
                    shutil.rmtree(session_dir)
                except Exception as e:
                    print(f"Error removing stale session directory {session_dir}: {e}")
    
    def is_duplicate_file(self, filename: str) -> bool:
        """Check if a resume with the same filename already exists."""
        return (self.temp_resumes_dir / filename).exists()
    
    def save_uploaded_resume(self, file_bytes: bytes, filename: str) -> tuple[bool, str]:
        """
        Save uploaded resume file.
        Returns: (success: bool, message: str)
        """
        try:
            if self.is_duplicate_file(filename):
                return False, "This resume has already been uploaded."
            
            temp_file = self.temp_resumes_dir / filename
            temp_file.write_bytes(file_bytes)
            return True, f"Successfully uploaded {filename}"
        
        except Exception as e:
            return False, f"Error uploading file: {str(e)}"
    
    def save_candidate_data(self, candidate_name: str, data: Dict[str, Any]) -> bool:
        """Save extracted candidate data as JSON."""
        try:
            candidate_file = self.extracted_candidates_dir / f"{candidate_name}.json"
            with open(candidate_file, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving candidate data: {e}")
            return False
    
    def load_candidate_data(self, candidate_name: str) -> Optional[Dict[str, Any]]:
        """Load extracted candidate data."""
        try:
            candidate_file = self.extracted_candidates_dir / f"{candidate_name}.json"
            if candidate_file.exists():
                with open(candidate_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading candidate data: {e}")
        return None
    
    def get_all_candidate_files(self) -> List[str]:
        """Get all extracted candidate JSON files."""
        return [f.stem for f in self.extracted_candidates_dir.glob("*.json")]
    
    def get_all_resume_files(self) -> List[str]:
        """Get all uploaded resume PDF files."""
        return [f.name for f in self.temp_resumes_dir.glob("*.pdf")]
    
    def clear_session(self) -> bool:
        """
        Clear all session data:
        - Uploaded resumes
        - Extracted candidates
        - Chroma collections
        - Rankings
        - Chat history
        - JD data
        """
        try:
            if self.base_data_dir.exists():
                shutil.rmtree(self.base_data_dir)
            
            return True
        except Exception as e:
            print(f"Error clearing session: {e}")
            return False
    
    def save_ground_truth(self, qa_pairs: List[Dict[str, str]], 
                         timestamp: Optional[str] = None) -> bool:
        """Save generated ground truth QA pairs."""
        try:
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            gt_file = self.ground_truth_dir / f"ground_truth_{timestamp}.json"
            with open(gt_file, "w") as f:
                json.dump(qa_pairs, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving ground truth: {e}")
            return False

    def load_latest_ground_truth(self) -> List[Dict[str, str]]:
        """Load the newest generated ground truth QA pairs for this session."""
        try:
            ground_truth_files = sorted(
                self.ground_truth_dir.glob("ground_truth_*.json"),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
            if not ground_truth_files:
                return []

            with open(ground_truth_files[0], "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading ground truth: {e}")
            return []

    def save_chat_sessions(self, chat_sessions: Dict[str, Any], active_chat_id: Optional[str]) -> bool:
        """Persist chatbot conversations so a page refresh does not wipe history."""
        try:
            payload = {
                "active_chat_id": active_chat_id,
                "chat_sessions": chat_sessions,
                "updated_at": datetime.now().isoformat(),
            }
            with open(self.chat_sessions_file, "w") as f:
                json.dump(payload, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving chat sessions: {e}")
            return False

    def load_chat_sessions(self) -> Dict[str, Any]:
        """Load persisted chatbot conversations for the current app session."""
        try:
            if self.chat_sessions_file.exists():
                with open(self.chat_sessions_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading chat sessions: {e}")
        return {"active_chat_id": None, "chat_sessions": {}}
    
    def get_session_stats(self) -> Dict[str, int]:
        """Get current session statistics."""
        return {
            "total_resumes": len(list(self.temp_resumes_dir.glob("*.pdf"))),
            "extracted_candidates": len(list(self.extracted_candidates_dir.glob("*.json"))),
            "chroma_collections": len(list(self.chroma_db_dir.glob("*"))),
            "ground_truth_files": len(list(self.ground_truth_dir.glob("*.json")))
        }
