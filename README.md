# Resume Screening RAG

A local Streamlit application for screening PDF resumes against a job description. It extracts candidate details, indexes resume text in ChromaDB, ranks candidates with semantic and rule-based scoring, and provides a Candidate Intelligence Assistant for RAG-style questions over the current resume set.

The project runs locally. Uploaded resumes, extracted JSON, vector database files, chat sessions, and evaluation exports are stored inside the project folder.

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.9+
- 4GB RAM minimum
- 2GB disk space
- Administrator access (for installation)

### Step 1: Install Ollama (5 mins)
1. Download from https://ollama.ai
2. Install and run
3. In terminal:
```bash
ollama pull qwen2.5
ollama serve  # Keep this running in background
```

### Step 2: Setup Project (2 mins)

**Windows:**
```bash
cd resume_screening_rag
run.bat
```

**Mac/Linux:**
```bash
cd resume_screening_rag
bash run.sh
```

### Step 3: Launch App (1 min)
- Browser opens automatically at `http://localhost:8501`
- System is ready!

---

## 📋 What The Project Does

1. Upload PDF resumes.
2. Extract candidate name, email, phone, skills, education, experience summary, and raw resume text.
3. Process resumes into semantic chunks.
4. Embed resume chunks with `BAAI/bge-base-en-v1.5`.
5. Store chunks in a session-scoped ChromaDB collection.
6. Upload or paste a job description.
7. Extract required skills, preferred skills, experience requirements, education requirements, certifications, and domain signals from the JD.
8. Rank candidates using semantic similarity, skill match, experience match, education match, and BM25 relevance.
9. Open candidate details and preview the original uploaded PDF.
10. Ask chatbot questions about rankings, skills, comparisons, experience, projects, education, and JD fit.
11. Save chatbot evaluation metrics to Excel.

---

## ✨ Main Features

- Multi-resume PDF upload
- Duplicate upload blocking by filename
- Session-based local storage
- Candidate extraction from text-based PDFs
- Structured education extraction
- Job description upload or paste input
- Candidate ranking with score breakdowns
- Ranking filters by name, resume filename, score, and top-N count
- Candidate detail view with contact details, skills, and PDF preview
- Separate Candidate Intelligence Assistant page
- Chat history persistence for current session
- Direct deterministic answers for common ranking, comparison, and skill queries
- RAG answers through local Ollama when deterministic answers are not enough
- Clickable resume filenames in chatbot responses
- Evaluation logging for assistant answers

---

## 💻 First Run Workflow

### 1️⃣ Upload Resumes (1-2 mins)
- Click "Upload Resume"
- Select 5-10 PDF files
- Wait for extraction

### 2️⃣ Process Resumes (2-3 mins)
- Click "Start Processing"
- System chunks and embeds
- Creates vector database

### 3️⃣ Add Job Description (1 min)
- Paste or upload JD
- System extracts requirements

### 4️⃣ Generate Rankings (1 min)
- Click "Generate Rankings"
- View candidate scores

### 5️⃣ Chat with AI (2 mins)
- Ensure Ollama is running
- Ask about candidates:
  - "Which candidates have AWS?"
  - "Why is candidate 1 ranked first?"
  - "Compare candidates 2 and 3"

---

## 🔧 Key Commands

### Windows
```bash
# Run app
run.bat

# Manual startup
venv\Scripts\activate
streamlit run app.py
```

### Mac/Linux
```bash
# Run app
bash run.sh

# Manual startup
source venv/bin/activate
streamlit run app.py
```

### Ollama (All platforms)
```bash
# Start Ollama
ollama serve

# Download Qwen2.5
ollama pull qwen2.5

# List installed models
ollama list
```

---

## 📊 Ranking Algorithm

```
Final Score = Skills Match - 45%
            + Experience Match - 25%
            + Education Match - 10%
            + Projects / Responsibilities Match - 20%
```

---

## 🏗️ Tech Stack

| Area | Technology |
| --- | --- |
| UI | Streamlit |
| PDF parsing | PyPDF2, pdfplumber |
| Embeddings | sentence-transformers |
| Embedding model | `BAAI/bge-base-en-v1.5` |
| Vector store | ChromaDB |
| Local LLM serving | Ollama |
| Chat model | `qwen2.5:latest` |
| Data handling | pandas, numpy |
| Evaluation export | openpyxl, XlsxWriter |

---

## 📁 Project Structure

```text
resume_screening_rag/
  app.py
    Main Streamlit dashboard.
    Handles session initialization, resume upload, resume processing,
    job description input, ranking, candidate filtering, candidate details,
    PDF preview, and navigation to the chatbot page.

  config.py
    Central configuration for app title, file limits, chunking,
    embedding model, ranking weights, Ollama model, retrieval settings,
    session behavior, export paths, and feature flags.

  requirements.txt
    Python package dependencies.

  run.bat
    Windows launcher script.

  run.sh
    Linux/macOS launcher script.

  README.md
    Main project documentation.

  core/
    __init__.py
      Core package marker.

    candidate_extractor.py
      Extracts candidate fields from resume text.
      Handles names, email, phone, skills, education, experience summary,
      candidate-name validation, phone validation, and final candidate JSON.

    chatbot.py
      Ollama integration.
      Checks model availability, builds the system prompt, calls Qwen 2.5,
      supports non-streaming and streaming generation.

    chroma_manager.py
      ChromaDB wrapper.
      Creates collections, stores chunks, searches embeddings, retrieves
      candidate-specific chunks, deletes candidate data, clears collections.

    chunking.py
      Splits resume text into retrievable chunks.
      Supports paragraph/sentence splitting, section-aware chunking,
      chunk overlap, chunk metadata, and chunk IDs.

    embeddings.py
      Sentence-transformer wrapper.
      Loads `BAAI/bge-base-en-v1.5`, encodes single texts, encodes batches,
      attaches embeddings to chunks, computes similarity.

    evaluation.py
      Chatbot evaluation framework.
      Generates ground-truth QA pairs, calculates precision/recall,
      evaluates faithfulness, relevancy, and ranking quality.

    jd_extractor.py
      Job description parser.
      Extracts required skills, preferred skills, certifications, domain
      experience, experience requirements, education requirements.

    pdf_parser.py
      PDF text extraction utilities.
      Extracts text, metadata, page count, and file information.

    ranking.py
      Candidate ranking engine.
      Calculates skill match, experience match, education match, semantic
      similarity score, final weighted score, BM25 score.

    retrieval.py
      Retrieval and direct-answer engine for the chatbot.
      Parses candidate references, detects ranking and skill queries,
      retrieves similar documents, formats direct answers, compares candidates.

    session_manager.py
      Session file manager.
      Creates session folders, saves uploaded resumes, saves extracted
      candidate JSON, persists chat sessions, clears session data.

  pages/
    chatbot_engine.py
      Dedicated Streamlit chatbot page.
      Manages chat sessions, sidebar chat history, readiness checks,
      retrieval engine setup, deterministic answer handling.

  prompts/
    chatbot_system_prompt.txt
      System prompt rules for the assistant.

    extraction_prompt.txt
      Extraction guidance prompt.

  data/
    session_<id>/
      Runtime session folder created by the app.

      temp_resumes/
        Uploaded resume PDFs for the session.

      extracted_candidates/
        Candidate JSON files extracted from uploaded resumes.

      chroma_db/
        ChromaDB files for embedded resume chunks.

      generated_ground_truth/
        Generated QA pairs for evaluation.

      chat_sessions.json
        Persisted assistant conversations.

  exports/
    chatbot_evaluation_metrics.xlsx
      Evaluation metrics generated by the assistant workflow.

  __pycache__/
    Python cache files generated at runtime.
```

---

## ⚠️ Troubleshooting

### "Cannot connect to Ollama"
- Is Ollama running? → `ollama serve`
- Is port 11434 open? → Check firewall
- Qwen2.5 installed? → `ollama pull qwen2.5`

### "PDF extraction failed"
- Is it a PDF? → Check file format
- Is it text-based? → Scanned images won't work
- Too large? → Try files < 50MB

### "Embedding model loading slowly"
- Normal on first run (~500MB download)
- Will cache for future use
- Check internet connection

### "Streamlit not starting"
- Venv activated? → `source venv/bin/activate` (Mac/Linux)
- Dependencies installed? → `pip install -r requirements.txt`
- Port 8501 in use? → Run on different port: `streamlit run app.py --server.port 8502`

---

## ⏱️ Performance Notes

- First embedding model load: ~2-3 mins
- Processing 100 resumes: ~5-10 mins
- Ranking generation: < 1 sec
- Chatbot response: 5-15 secs

## 💡 Tips & Tricks

1. **Batch Processing**: Upload 50+ resumes for better ranking insights
2. **Custom Job Descriptions**: More detailed JDs = better matching
3. **Chatbot Questions**: Try specific skills/experiences
4. **Ranking Customization**: View Top 5 through Top 50
5. **Session Management**: "Clear Session" between different batches

### Try These Chatbot Questions:
- "Which candidates have Python and machine learning experience?"
- "Who has worked on cloud projects?"
- "Why was candidate 5 ranked higher than candidate 6?"
- "What are candidate 1's main technical skills?"
- "Find candidates with AWS and DevOps experience"

---

## 🔒 Current Limitations

- Only PDF resumes are supported
- Scanned or image-only PDFs work only if extractable text is present
- The chatbot model is fixed to `qwen2.5:latest`
- Model switching is not exposed in the UI
- The app is intended for local use, not multi-user production deployment as-is
- Runtime data in `data/session_<id>/` is disposable session data

---

## 📦 Deployment Guide

### Development vs Production

**Local Development (Current Setup)**
- ✓ Single machine
- ✓ No authentication
- ✓ Session-based data
- ✓ Ollama local
- ✓ All data local

### Production Deployment Options

#### Option 1: Local Server
Best for: Single team, on-premises

```bash
# Setup
pip install -r requirements.txt
ollama pull qwen2.5

# Run on port 80 (needs sudo/admin)
streamlit run app.py --server.port 80 --server.address 0.0.0.0
```

#### Option 2: Docker Container
Best for: Scalability, consistency

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Download embedding model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-en-v1.5')"

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

Build and run:
```bash
docker build -t resume-screening .
docker run -p 8501:8501 -p 11434:11434 resume-screening
```

#### Option 3: Cloud Deployment (AWS, GCP, Azure)

**AWS EC2 + ECS:**
1. Create EC2 instance (t3.large minimum)
2. Install Docker and Ollama
3. Push Docker image to ECR
4. Deploy via ECS/Fargate

**Google Cloud Run:**
1. Containerize application
2. Deploy to Cloud Run
3. Set up Cloud Storage for persistent data
4. Configure Cloud SQL for session management

**Azure Container Instances:**
1. Containerize application
2. Deploy to ACI
3. Use Azure Blob Storage for data
4. Setup App Service for web frontend

---

## ⚡ Performance Optimization

### Database Optimization
```python
# Use persistent ChromaDB
chroma_manager = ChromaManager(
    db_path="/persistent/chroma_db",
    collection_name="resumes"
)

# Increase batch sizes
embedding_model.encode_chunks(chunks, batch_size=64)
```

### Memory Management
```python
# Clear old sessions
session_manager.clear_session()

# Archive old evaluations
evaluation_framework.export_to_json("exports/archive_2024.json")
```

### Caching Strategy
```python
# Cache embeddings
import streamlit as st

@st.cache_resource
def get_embedding_model():
    return EmbeddingModel()

@st.cache_data
def get_candidate_chunks(candidate_name):
    return retrieve_chunks(candidate_name)
```

---

## 🔐 Security Considerations

### Authentication
Add with Streamlit Community Cloud or custom middleware:
```python
import streamlit as st

def require_login():
    if 'authenticated' not in st.session_state:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state.authenticated = True
            else:
                st.error("Invalid credentials")
    
    return st.session_state.get('authenticated', False)

if require_login():
    main()
```

### Data Security
```python
import hashlib
import os

# Encrypt sensitive data
def encrypt_file_path(path):
    return hashlib.sha256(path.encode()).hexdigest()

# Store credentials in environment
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
```

### HTTPS/SSL
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Run with SSL
streamlit run app.py --server.sslCertFile=cert.pem --server.sslKeyFile=key.pem
```

---

## 📊 Monitoring & Logging

### Application Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Resume processed successfully")
logger.error("Error processing resume", exc_info=True)
```

### Performance Monitoring
```python
import time

def monitor_performance(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        logger.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper

@monitor_performance
def process_resume(pdf_path):
    # Processing logic
    pass
```

---

## 🎯 Application Workflow

### 1. Startup And Session Initialization

When `app.py` starts, it initializes Streamlit state and creates a new runtime session:

- Old `data/session_<id>/` folders are cleaned.
- A new `data/session_<uuid>/` folder is created.
- `SessionManager` is initialized for that folder.
- The embedding model is loaded once into session state.
- `ChunkingEngine`, `ChromaManager`, and `EvaluationFramework` are created.
- Dashboard state flags are initialized.

Important state flags include:

```text
resume_processing_done
jd_processing_done
ranking_done
selected_candidate
show_resume_pdf
ranking_data
candidates
chat_sessions
```

### 2. Resume Upload

The dashboard Section 1 accepts PDF files.

For each uploaded resume:

1. The app checks whether a file with the same name already exists.
2. The PDF bytes are saved to `data/session_<id>/temp_resumes/`.
3. `CandidateExtractor.extract_from_resume()` extracts candidate data.
4. Extracted data is saved as JSON in `extracted_candidates/`.
5. The candidate is added to Streamlit session state.

The upload table shows:

- Candidate name.
- Email.
- Phone number.
- Resume filename.

Users can remove a selected resume. Removing a resume deletes its PDF and JSON, clears dependent Chroma/ranking state, and requires resume processing to be run again.

### 3. Resume Processing

Section 2 indexes uploaded resumes for retrieval.

For each candidate:

1. Raw resume text is chunked with `ChunkingEngine`.
2. Chunks include candidate metadata.
3. `EmbeddingModel` generates normalized embeddings.
4. `ChromaManager` stores chunks and embeddings in the session ChromaDB collection.

After processing, `resume_processing_done` becomes true.

### 4. Job Description Processing

Section 3 becomes useful after resumes have been processed.

The user can:

- Upload a job description PDF.
- Paste job description text.

`JDExtractor` returns:

- Required skills.
- Preferred skills.
- Experience requirements.
- Education requirements.
- Certifications.
- Domain experience.
- Full text.

The extracted JD data is stored in `st.session_state.jd_data`.

### 5. Candidate Ranking

After JD processing, the user can generate rankings.

The ranking flow combines:

- JD required/preferred skills.
- JD full text.
- Candidate extracted skills.
- Candidate experience summary.
- Candidate education.
- Semantic similarity from embeddings.
- BM25 relevance over candidate text and JD text.

The base weighted score is:

```text
0.40 * skills match
0.30 * experience match
0.10 * education match
0.20 * semantic content similarity
```

The ranking engine then produces ranked candidate rows with:

- Rank.
- Candidate name.
- Resume filename.
- Final score.
- Semantic similarity.
- Skill match.
- Experience match.
- Education match.
- Matched required skills.
- Matched preferred skills.
- Missing required skills.

### 6. Ranking View And Candidate Details

Section 4 displays ranked candidates with filters:

- Candidate name or resume filename text filter.
- Minimum score.
- Top-N count.

Clicking a candidate name or resume filename selects that candidate.

The Candidate Details section shows:

- Candidate name.
- Email.
- Phone.
- Skills.
- Resume filename.
- Optional embedded PDF preview.

The PDF preview reads the original uploaded resume from `temp_resumes/`.

### 7. Candidate Intelligence Assistant

The chat button opens `pages/chatbot_engine.py`.

The assistant is enabled only when:

- Resumes exist.
- Resume embeddings are ready.
- Rankings exist.

The assistant uses `RetrievalEngine` in two ways:

1. Direct structured answers for questions it can answer deterministically.
2. RAG context plus Ollama/Qwen 2.5 for open-ended questions.

Direct-answer examples:

```text
Which candidates have AWS and NLP?
Why was candidate 1 ranked first?
Compare candidate 1 and candidate 3
Show top 5 candidates
```

Skill-query answers are formatted as separate candidate blocks:

```text
Candidate 1:
Name: Ananya Krishnan (Ananya Krishnan.pdf)
Matched Skills: AWS, NLP

Candidate 2:
Name: Sara Thomas (Sara Thomas.pdf)
Matched Skills: AWS
Missing Skills: NLP
```

Invalid query words such as `as` are ignored unless they are real skills. A candidate is never reported as having a skill unless that skill is present in the extracted resume/ranking data.

### 8. Chatbot RAG Path

When a deterministic answer is not enough:

1. The retrieval engine runs semantic search against ChromaDB.
2. Retrieved documents are reranked.
3. Ranking data and resume evidence are formatted as context.
4. `OllamaChatbot` sends the prompt and context to `qwen2.5:latest`.
5. The response is enhanced with clickable resume links.
6. Evaluation metrics are recorded.

If Ollama or the model is unavailable, the assistant returns a short unavailable message instead of exposing raw backend details.

### 9. Clickable Resume Links In Chat

When chatbot output includes a known resume filename, the assistant converts it into a clickable link.

Clicking the resume link:

1. Navigates back to the dashboard.
2. Sets the `resume` query parameter.
3. Selects the matching candidate.
4. Opens candidate details.
5. Shows the resume preview.

### 10. Evaluation

The assistant records evaluation details through `EvaluationFramework`.

Metrics include:

- Precision at K.
- Recall at K.
- Faithfulness.
- Answer relevancy.
- Ranking quality.

Exports are written to:

```text
exports/chatbot_evaluation_metrics.xlsx
```

## Data Flow

```text
PDF resumes
  -> PDFParser
  -> CandidateExtractor
  -> candidate JSON in extracted_candidates/
  -> ChunkingEngine
  -> EmbeddingModel
  -> ChromaManager
  -> ChromaDB in chroma_db/

Job description PDF/text
  -> JDExtractor
  -> JD fields in session state

Candidates + JD + embeddings
  -> RankingEngine
  -> ranking_data in session state

User chatbot question
  -> RetrievalEngine
  -> direct answer or retrieved context
  -> OllamaChatbot when needed
  -> enhanced chat response
  -> EvaluationFramework
```

## Setup

### 1. Create A Virtual Environment

Windows:

```bat
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Ollama And Pull Qwen 2.5

Install Ollama from:

```text
https://ollama.com
```

Pull the model:

```bash
ollama pull qwen2.5
```

Start Ollama:

```bash
ollama serve
```

The app expects Ollama at:

```text
http://localhost:11434
```

### 4. Run The App

```bash
streamlit run app.py
```

Or use the included launchers:

Windows:

```bat
run.bat
```

Linux/macOS:

```bash
chmod +x run.sh
./run.sh
```

## Configuration

Main settings are in `config.py`.

Important defaults:

```python
MAX_RESUMES = 500
MAX_FILE_SIZE_MB = 1024
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
MODEL_NAME = "qwen2.5:latest"
OLLAMA_BASE_URL = "http://localhost:11434"
RETRIEVAL_TOP_K = 5
CHATBOT_NUM_PREDICT = 320
EVALUATION_EXPORT_PATH = "exports/chatbot_evaluation_metrics.xlsx"
```

Ranking weights:

```python
RANKING_WEIGHTS = {
    "skill_match": 0.40,
    "experience_match": 0.30,
    "education_match": 0.10,
    "semantic_similarity": 0.20,
}
```

## Runtime Files

Session data is created under:

```text
data/session_<uuid>/
```

Typical contents:

```text
temp_resumes/
extracted_candidates/
chroma_db/
generated_ground_truth/
chat_sessions.json
```

Evaluation files are stored under:

```text
exports/
```

These folders are generated by the app and can be recreated by running the workflow again.

## Development Commands

Compile-check Python files:

```bash
python -m compileall app.py pages core config.py
```

Run the app:

```bash
streamlit run app.py
```

Search code quickly:

```bash
rg "RankingEngine"
rg "RetrievalEngine"
```

## Troubleshooting

### Chat input is disabled

Complete the dashboard workflow first:

1. Upload resumes.
2. Start resume processing.
3. Add a job description.
4. Generate rankings.

### Chatbot says the assistant is unavailable

Make sure Ollama is running and Qwen 2.5 is installed:

```bash
ollama serve
ollama list
ollama pull qwen2.5
```

### Resume extraction looks incomplete

Use text-based PDFs. Scanned PDFs or image-only resumes may not contain extractable text.

### Rankings are empty

Confirm that resumes were processed and that JD text was extracted before clicking `Generate Rankings`.

### First run is slow

The sentence-transformer embedding model may load or download on first use. Ollama may also take time to load Qwen 2.5 for the first answer.

## Privacy And Data Handling

- Resume files stay local in `data/session_<id>/temp_resumes/`.
- Extracted candidate JSON stays local in `data/session_<id>/extracted_candidates/`.
- Vector data stays local in `data/session_<id>/chroma_db/`.
- Chat sessions are stored in the current session folder.
- LLM generation runs locally through Ollama.
- Candidate comparison answers intentionally avoid exposing contact details.
- Candidate details on the dashboard may still show extracted contact details.

## License

No license file is currently included. Add a license before publishing or distributing this project.
