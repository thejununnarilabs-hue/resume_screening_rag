# Configuration file for Resume Screening System

# Application Settings
APP_TITLE = "AI-Powered Resume Screening & Candidate Ranking System with RAG"
APP_ICON = "📄"

# File Limits
MAX_RESUMES = 500
MAX_FILE_SIZE_MB = 1024  # Per file
ALLOWED_EXTENSIONS = ['pdf']

# Chunking Configuration
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

# Embedding Model
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
EMBEDDING_BATCH_SIZE = 32

# Ranking Weights
RANKING_WEIGHTS = {
    'skill_match': 0.40,
    'experience_match': 0.30,
    'education_match': 0.10,
    'semantic_similarity': 0.20
}

# Chatbot Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen2.5:latest"
OLLAMA_MODEL = MODEL_NAME
CHATBOT_TEMPERATURE = 0.7
CHATBOT_TOP_P = 0.9
CHATBOT_NUM_PREDICT = 320
OLLAMA_STATUS_CACHE_SECONDS = 30

# ChromaDB Configuration
CHROMA_DB_PATH = "data/chroma_db"
CHROMA_COLLECTION_NAME = "resumes"

# Retrieval Configuration
RETRIEVAL_TOP_K = 5
RERANK_TOP_K = 3

# Session Configuration
SESSION_TIMEOUT_MINUTES = 60
AUTO_CLEANUP = True

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/app.log"

# Evaluation Framework
EVALUATION_EXPORT_PATH = "exports/chatbot_evaluation_metrics.xlsx"
GROUND_TRUTH_PATH = "data/generated_ground_truth"

# Feature Flags
ENABLE_SEMANTIC_CHUNKING = True
ENABLE_RAG_CHATBOT = True
ENABLE_EVALUATION = True
ENABLE_PDF_VIEWER = True
ENABLE_RANKING_VISUALIZATION = True

# UI Configuration
SIDEBAR_EXPANDED = True
LAYOUT_WIDTH = "wide"
SHOW_SESSION_STATS = True
SHOW_PERFORMANCE_METRICS = True
