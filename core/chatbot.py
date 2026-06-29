"""Chatbot with RAG using Ollama Qwen2.5."""

import requests
import json
import time
import logging
import threading
from typing import List, Dict, Any, Optional, Generator


MODEL_NAME = "qwen2.5:latest"
AI_ASSISTANT_UNAVAILABLE_MESSAGE = "AI Assistant is temporarily unavailable."
OLLAMA_UNAVAILABLE_MESSAGE = AI_ASSISTANT_UNAVAILABLE_MESSAGE
_OLLAMA_STATUS_CACHE: Dict[str, Any] = {}
_MODEL_LOAD_THREADS: Dict[str, threading.Thread] = {}
logger = logging.getLogger(__name__)


def _is_qwen25_model(model_name: str) -> bool:
    return model_name.lower().startswith("qwen2.5")


def _is_requested_model_available(requested_model: str, available_models: List[str]) -> bool:
    if not _is_qwen25_model(requested_model):
        return False
    return any(_is_qwen25_model(model) for model in available_models)


def check_ollama_status(
    model_name: str = MODEL_NAME,
    ollama_base_url: str = "http://localhost:11434",
    timeout: int = 5,
    cache_seconds: int = 30,
) -> Dict[str, Any]:
    """Return Ollama service and Qwen 2.5 availability without surfacing technical errors."""
    model_name = MODEL_NAME
    cache_key = f"{ollama_base_url}|{model_name}"
    cached = _OLLAMA_STATUS_CACHE.get(cache_key)
    now = time.time()
    if cached and now - cached["checked_at"] < cache_seconds:
        return cached["status"]

    try:
        response = requests.get(f"{ollama_base_url}/api/tags", timeout=timeout)
        if response.status_code != 200:
            logger.error("Ollama tags request failed with status %s: %s", response.status_code, response.text)
            status = {
                "running": False,
                "model_available": False,
                "available_models": [],
                "message": AI_ASSISTANT_UNAVAILABLE_MESSAGE,
            }
            _OLLAMA_STATUS_CACHE[cache_key] = {"checked_at": now, "status": status}
            return status

        models = response.json().get("models", [])
        available_models = [m.get("name", "") for m in models]
        model_available = _is_requested_model_available(model_name, available_models)
        status = {
            "running": True,
            "model_available": model_available,
            "available_models": available_models,
            "message": AI_ASSISTANT_UNAVAILABLE_MESSAGE,
        }
        _OLLAMA_STATUS_CACHE[cache_key] = {"checked_at": now, "status": status}
        return status
    except requests.exceptions.RequestException as exc:
        logger.exception("Ollama status check failed: %s", exc)
        status = {
            "running": False,
            "model_available": False,
            "available_models": [],
            "message": AI_ASSISTANT_UNAVAILABLE_MESSAGE,
        }
        _OLLAMA_STATUS_CACHE[cache_key] = {"checked_at": now, "status": status}
        return status
    except Exception as exc:
        logger.exception("Unexpected Ollama status check error: %s", exc)
        status = {
            "running": False,
            "model_available": False,
            "available_models": [],
            "message": AI_ASSISTANT_UNAVAILABLE_MESSAGE,
        }
        _OLLAMA_STATUS_CACHE[cache_key] = {"checked_at": now, "status": status}
        return status


class OllamaChatbot:
    """Chatbot using Ollama with Qwen2.5 model."""
    
    def __init__(self, model_name: str = MODEL_NAME, 
                 ollama_base_url: str = "http://localhost:11434",
                 warm_up: bool = True):
        """
        Initialize Ollama chatbot.
        
        Args:
            model_name: Ollama model name
            ollama_base_url: Base URL for Ollama API
        """
        self.model_name = MODEL_NAME
        self.base_url = ollama_base_url
        self.chat_history = []
        if warm_up:
            self.load_model_async()
    
    def check_model_availability(self) -> bool:
        """Check if Ollama and model are available."""
        status = check_ollama_status(self.model_name, self.base_url)
        return bool(status["running"] and status["model_available"])

    def load_model_async(self) -> None:
        """Load the configured model in the background when it is available."""
        cache_key = f"{self.base_url}|{self.model_name}"
        thread = _MODEL_LOAD_THREADS.get(cache_key)
        if thread and thread.is_alive():
            return

        def load_model() -> None:
            try:
                if not self.check_model_availability():
                    return
                requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": "",
                        "stream": False,
                        "keep_alive": "10m",
                        "options": {"num_predict": 1},
                    },
                    timeout=30,
                )
            except Exception as exc:
                logger.exception("Ollama model warm-up failed: %s", exc)

        _MODEL_LOAD_THREADS[cache_key] = threading.Thread(target=load_model, daemon=True)
        _MODEL_LOAD_THREADS[cache_key].start()
    
    def generate_response(self, prompt: str, context: str = "",
                         temperature: float = 0.7,
                         top_p: float = 0.9,
                         num_predict: int = 320) -> Optional[str]:
        """
        Generate response using Ollama.
        
        Args:
            prompt: User query/prompt
            context: Additional context for the model
            temperature: Sampling temperature (0-1)
            top_p: Nucleus sampling parameter
            
        Returns:
            Generated response text
        """
        try:
            if not self.check_model_availability():
                logger.warning("Ollama model unavailable for request: %s", self.model_name)
                return None

            # Build system prompt with context
            system_prompt = self._build_system_prompt(context)
            
            # Prepare request
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "system": system_prompt,
                "temperature": temperature,
                "top_p": top_p,
                "stream": False,
                "keep_alive": "10m",
                "options": {
                    "num_predict": num_predict,
                },
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '')
                
                # Add to chat history
                self.chat_history.append({
                    'role': 'user',
                    'content': prompt
                })
                self.chat_history.append({
                    'role': 'assistant',
                    'content': generated_text
                })
                
                return generated_text
            else:
                logger.error("Ollama generate failed with status %s: %s", response.status_code, response.text)
                return None
        
        except requests.exceptions.Timeout as exc:
            logger.exception("Ollama generate request timed out: %s", exc)
            return None
        except Exception as e:
            logger.exception("Error generating Ollama response: %s", e)
            return None
    
    def generate_response_stream(self, prompt: str, context: str = "",
                                 temperature: float = 0.7) -> Generator[str, None, None]:
        """
        Generate response with streaming.
        
        Args:
            prompt: User query/prompt
            context: Additional context
            temperature: Sampling temperature
            
        Yields:
            Streamed response chunks
        """
        try:
            if not self.check_model_availability():
                logger.warning("Ollama model unavailable for streaming request: %s", self.model_name)
                yield AI_ASSISTANT_UNAVAILABLE_MESSAGE
                return

            system_prompt = self._build_system_prompt(context)
            
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "system": system_prompt,
                "temperature": temperature,
                "stream": True,
                "keep_alive": "10m",
                "options": {
                    "num_predict": 320,
                },
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                stream=True,
                timeout=120
            )
            
            full_response = ""
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if 'response' in chunk:
                        text = chunk['response']
                        full_response += text
                        yield text
            
            # Add to chat history
            self.chat_history.append({
                'role': 'user',
                'content': prompt
            })
            self.chat_history.append({
                'role': 'assistant',
                'content': full_response
            })
        
        except Exception as e:
            logger.exception("Error in Ollama streaming response: %s", e)
            yield AI_ASSISTANT_UNAVAILABLE_MESSAGE
    
    @staticmethod
    def _build_system_prompt(context: str) -> str:
        """Build system prompt with context."""
        base_prompt = """You are an AI Candidate Intelligence Assistant.

IMPORTANT RULES:
1. Answer only from the retrieved resume information and current ranking data.
2. Never hardcode candidate names or assume missing facts.
3. Always cite candidate names and resume evidence from the provided context.
4. If the retrieved resume and ranking context is insufficient, say there is not enough information.
5. For candidate search questions, return matching candidates with evidence.
6. For project questions, use project and experience evidence.
7. For ranking questions, resolve candidate numbers from the current ranking table and explain matching score, matched skills, experience alignment, and education alignment.
8. For comparison questions, compare scores, required skills, missing skills, experience, and education.

"""
        
        if context:
            base_prompt += f"\nAvailable Information:\n{context}\n"
        
        return base_prompt
    
    def rag_answer(self, query: str, retrieval_context: Dict[str, Any],
                   temperature: float = 0.7) -> Optional[str]:
        """
        Generate answer using RAG (Retrieval-Augmented Generation).
        
        Args:
            query: User query
            retrieval_context: Context from retrieval engine
            temperature: Sampling temperature
            
        Returns:
            Generated answer
        """
        try:
            # Format context for prompt
            formatted_context = self._format_retrieval_context(retrieval_context)
            
            # Build prompt
            prompt = f"""Query: {query}

Answer based on the provided information:"""
            
            # Generate response
            response = self.generate_response(prompt, formatted_context, temperature)
            
            return response
        
        except Exception as e:
            logger.exception("Error in RAG answer: %s", e)
            return None
    
    @staticmethod
    def _format_retrieval_context(context: Dict[str, Any]) -> str:
        """Format retrieval context for prompt."""
        parts = []
        
        # Add retrieved documents
        if context.get('retrieved_documents'):
            parts.append("Retrieved Information:")
            for i, doc in enumerate(context['retrieved_documents'], 1):
                parts.append(f"\n[Document {i}]")
                parts.append(doc.get('text', '')[:400])  # Limit length
        
        # Add candidate info
        if context.get('candidate_references'):
            parts.append("\n\nCandidate Information:")
            for candidate in context['candidate_references']:
                parts.append(f"Candidate: {candidate.get('candidate_name')}")
                parts.append(f"Rank: {candidate.get('rank')}")
                parts.append(f"Matching Score: {candidate.get('final_score', 0):.1%}")
        
        return "\n".join(parts)
    
    def clear_history(self):
        """Clear chat history."""
        self.chat_history = []
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """Get chat history."""
        return self.chat_history
    
    def add_message(self, role: str, content: str):
        """Manually add message to chat history."""
        self.chat_history.append({
            'role': role,
            'content': content
        })
    
    def format_candidate_response(self, candidates_list: List[Dict[str, Any]]) -> str:
        """
        Format chatbot response with candidate information and resume filenames.
        
        Args:
            candidates_list: List of candidate dictionaries with name and pdf_file
            
        Returns:
            Formatted response with candidate names and resume filenames
        """
        if not candidates_list:
            return "No matching candidates found."
        
        response_lines = []
        for idx, candidate in enumerate(candidates_list, 1):
            candidate_name = candidate.get('candidate_name', 'Unknown')
            resume_file = candidate.get('pdf_file', 'resume.pdf')
            score = candidate.get('final_score', 0)
            
            # Format: "1. Candidate Name (resume_file.pdf) - Score: XX%"
            line = f"{idx}. {candidate_name} ({resume_file})"
            
            if score > 0:
                line += f" - Score: {score:.1%}"
            
            response_lines.append(line)
        
        return "\n".join(response_lines)
    
    def extract_candidate_references(self, text: str) -> List[str]:
        """
        Extract candidate references from generated response.
        Used to identify which candidates are mentioned in the answer.
        
        Args:
            text: Generated response text
            
        Returns:
            List of candidate filenames mentioned
        """
        import re
        
        # Pattern to match "filename.pdf" in parentheses
        pattern = r'\(([^)]+\.pdf)\)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        return matches
