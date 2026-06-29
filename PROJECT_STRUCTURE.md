# 📁 Project Structure & Architecture

## Complete File Organization

```
resume_screening_rag/
│
├── 📄 app.py                              [Main Application - 1000+ lines]
│   ├── Stage 1: Resume Upload
│   ├── Stage 2: Resume Processing
│   ├── Stage 3: Job Description
│   ├── Stage 4: Candidate Ranking
│   ├── Stage 5: Candidate Details
│   └── Stage 6: Chatbot
│
├── ⚙️ config.py                           [Configuration - 50+ settings]
│   ├── Application settings
│   ├── Model parameters
│   ├── Ranking weights
│   ├── Chunking config
│   └── Feature flags
│
├── 📋 requirements.txt                    [20+ Dependencies]
│   ├── streamlit==1.28.1
│   ├── sentence-transformers==2.2.2
│   ├── chromadb==0.4.13
│   ├── PyPDF2==3.0.1
│   ├── requests==2.31.0
│   └── ... (15 more)
│
├── 🔧 run.bat / run.sh                    [Startup Scripts]
│   └── Auto setup & launch
│
├── 📚 DOCUMENTATION/
│   ├── README.md                          [Complete technical guide]
│   ├── GETTING_STARTED.md                 [First 30 minutes]
│   ├── QUICKSTART.md                      [5-minute setup]
│   ├── DEPLOYMENT.md                      [Production guide]
│   ├── COMPLETION_SUMMARY.md              [What was built]
│   └── PROJECT_STRUCTURE.md               [This file]
│
├── 🔑 CONFIGURATION/
│   ├── config.py                          [Application config]
│   └── .env.example                       [Environment template]
│
├── 📝 PROMPTS/
│   ├── chatbot_system_prompt.txt          [AI system instructions]
│   └── extraction_prompt.txt              [Resume extraction guide]
│
├── 🧠 CORE/ (11 Core Modules)
│   │
│   ├── session_manager.py (150 lines)
│   │   ├── SessionManager class
│   │   ├── File upload & storage
│   │   ├── Duplicate detection (filename)
│   │   ├── Session cleanup
│   │   └── Candidate data persistence
│   │
│   ├── pdf_parser.py (80 lines)
│   │   ├── PDFParser class
│   │   ├── Text extraction
│   │   ├── Metadata extraction
│   │   └── File info retrieval
│   │
│   ├── candidate_extractor.py (250 lines)
│   │   ├── CandidateExtractor class
│   │   ├── Name extraction
│   │   ├── Email/phone extraction
│   │   ├── Skills identification
│   │   ├── Education extraction
│   │   ├── Experience summary
│   │   └── Complete candidate extraction
│   │
│   ├── jd_extractor.py (200 lines)
│   │   ├── JDExtractor class
│   │   ├── Required skills extraction
│   │   ├── Preferred skills extraction
│   │   ├── Experience requirements
│   │   ├── Education requirements
│   │   └── PDF/Text JD processing
│   │
│   ├── chunking.py (250 lines)
│   │   ├── ChunkingEngine class
│   │   ├── Semantic chunking (700 chars)
│   │   ├── Overlap handling (100 chars)
│   │   ├── Section-based chunking
│   │   └── Chunk metadata management
│   │
│   ├── embeddings.py (200 lines)
│   │   ├── EmbeddingModel class
│   │   ├── BAAI/bge-base-en-v1.5 model
│   │   ├── Text encoding
│   │   ├── Batch processing
│   │   ├── Similarity calculation
│   │   └── Model info
│   │
│   ├── chroma_manager.py (250 lines)
│   │   ├── ChromaManager class
│   │   ├── Collection management
│   │   ├── Add/search documents
│   │   ├── Metadata filtering
│   │   ├── Candidate-specific retrieval
│   │   ├── Data deletion
│   │   └── Collection statistics
│   │
│   ├── ranking.py (300 lines)
│   │   ├── RankingEngine class
│   │   ├── Skill matching
│   │   ├── Experience scoring
│   │   ├── Education alignment
│   │   ├── Final score calculation
│   │   ├── Candidate ranking
│   │   └── Top N selection
│   │
│   ├── retrieval.py (250 lines)
│   │   ├── RetrievalEngine class
│   │   ├── Semantic search
│   │   ├── Context reranking
│   │   ├── Candidate reference parsing
│   │   ├── Evidence retrieval
│   │   ├── Context formatting
│   │   └── LLM prompt building
│   │
│   ├── chatbot.py (250 lines)
│   │   ├── OllamaChatbot class
│   │   ├── Ollama connection
│   │   ├── Model availability check
│   │   ├── Response generation
│   │   ├── Streaming responses
│   │   ├── System prompt building
│   │   ├── RAG answer generation
│   │   └── Chat history management
│   │
│   ├── evaluation.py (300 lines)
│   │   ├── EvaluationFramework class
│   │   ├── Ground truth generation
│   │   ├── Precision/Recall calculation
│   │   ├── Faithfulness evaluation
│   │   ├── Relevancy scoring
│   │   ├── Evaluation recording
│   │   ├── JSON export
│   │   └── Summary metrics
│   │
│   └── __init__.py
│       └── Package initialization
│
├── 📊 DATA/ (Auto-created, Session-based)
│   ├── temp_resumes/
│   │   └── [Uploaded PDF files during session]
│   │
│   ├── extracted_candidates/
│   │   └── [JSON files with extracted candidate data]
│   │
│   ├── chroma_db/
│   │   └── [Vector database files]
│   │
│   ├── generated_ground_truth/
│   │   └── [Ground truth QA pairs for evaluation]
│   │
│   └── evaluation_reports/
│       └── [Evaluation metrics and results]
│
├── 📄 EXPORTS/ (Auto-created)
│   └── chatbot_evaluation.xlsx
│       └── [Evaluation report export]
│
└── 📄 PAGES/ (For future expansion)
    └── [Multi-page module support]
```

---

## Data Flow Architecture

```
INPUT STAGE
├── Upload PDF Resumes
│   ├── Duplicate detection (filename)
│   └── File validation
│
EXTRACTION STAGE
├── PDF text extraction
├── Candidate name extraction
├── Email/phone extraction
├── Skills identification
├── Education extraction
└── Experience summary
│
PROCESSING STAGE
├── Semantic chunking (700 chars, 100 overlap)
├── Embedding generation (BAAI/bge-base-en-v1.5)
├── ChromaDB storage
└── Metadata association
│
JOB DESCRIPTION STAGE
├── PDF/Text extraction
├── Required skills extraction
├── Preferred skills extraction
├── Experience requirements
└── Education requirements
│
RANKING STAGE
├── Semantic similarity (0.60)
├── Skill matching (0.20)
├── Experience alignment (0.10)
├── Education matching (0.10)
└── Final score calculation
│
RETRIEVAL STAGE
├── Semantic search
├── Context reranking
├── Evidence gathering
└── Prompt building
│
GENERATION STAGE
├── Ollama API call
├── Qwen2.5 processing
└── RAG answer generation
│
EVALUATION STAGE
├── Precision@K calculation
├── Recall@K calculation
├── Faithfulness scoring
├── Relevancy evaluation
└── Results export
```

---

## Module Dependencies

```
app.py (Main)
  ├─ session_manager
  │  └─ json, hashlib, pathlib
  │
  ├─ pdf_parser
  │  └─ PyPDF2
  │
  ├─ candidate_extractor
  │  ├─ pdf_parser
  │  └─ re, typing
  │
  ├─ jd_extractor
  │  ├─ pdf_parser
  │  └─ re, typing
  │
  ├─ chunking
  │  └─ re, typing
  │
  ├─ embeddings
  │  ├─ sentence_transformers
  │  └─ numpy
  │
  ├─ chroma_manager
  │  ├─ chromadb
  │  └─ pathlib
  │
  ├─ ranking
  │  └─ numpy
  │
  ├─ retrieval
  │  ├─ chroma_manager
  │  ├─ embeddings
  │  └─ re
  │
  ├─ chatbot
  │  ├─ requests
  │  ├─ json
  │  └─ typing
  │
  └─ evaluation
     ├─ json
     ├─ pathlib
     └─ datetime
```

---

## Session State Management

```
st.session_state Contains:
│
├─ session_manager
│  └─ SessionManager instance
│
├─ current_stage (1-6)
│  ├─ 1: Resume Upload
│  ├─ 2: Resume Processing
│  ├─ 3: Job Description
│  ├─ 4: Ranking
│  ├─ 5: Candidate Details (on-demand)
│  └─ 6: Chatbot
│
├─ candidates []
│  ├─ [0]: {name, email, phone, skills, education, ...}
│  └─ [...]: More candidates
│
├─ jd_data {}
│  ├─ required_skills: [...]
│  ├─ preferred_skills: [...]
│  ├─ experience_requirement: "..."
│  └─ education_requirements: [...]
│
├─ ranking_data []
│  ├─ [0]: {rank, name, score, semantic_sim, ...}
│  └─ [...]: More ranked candidates
│
├─ embedding_model
│  └─ EmbeddingModel instance
│
├─ chroma_manager
│  └─ ChromaManager instance
│
├─ retrieval_engine
│  └─ RetrievalEngine instance
│
├─ chatbot
│  └─ OllamaChatbot instance
│
├─ chunking_engine
│  └─ ChunkingEngine instance
│
├─ evaluation_framework
│  └─ EvaluationFramework instance
│
└─ chat_messages []
   ├─ {role: 'user', content: '...'}
   └─ {role: 'assistant', content: '...'}
```

---

## Ranking Score Calculation

```
For Each Candidate:

1. SEMANTIC SIMILARITY (0.60 weight)
   ├─ Encode candidate full text
   ├─ Encode JD text  
   ├─ Calculate cosine similarity
   └─ Score: 0.0 - 1.0

2. SKILL MATCH (0.20 weight)
   ├─ Extract candidate skills
   ├─ Compare with required skills
   ├─ Compare with preferred skills
   ├─ Calculate match percentage
   └─ Score: 0.0 - 1.0

3. EXPERIENCE MATCH (0.10 weight)
   ├─ Extract candidate experience text
   ├─ Compare with JD experience requirement
   ├─ Keyword matching
   ├─ Text length consideration
   └─ Score: 0.0 - 1.0

4. EDUCATION MATCH (0.10 weight)
   ├─ Extract candidate education
   ├─ Compare with JD requirements
   ├─ Match percentage calculation
   ├─ Education depth bonus
   └─ Score: 0.0 - 1.0

FINAL SCORE = 
    0.60 × Semantic +
    0.20 × Skills +
    0.10 × Experience +
    0.10 × Education
Result: 0.0 - 1.0 (0% - 100%)
```

---

## API Endpoints (Future Enhancement)

```
GET  /api/candidates
     └─ List all candidates

GET  /api/candidates/{id}
     └─ Get candidate details

GET  /api/rankings
     └─ Get current rankings

POST /api/jd
     └─ Upload/update job description

POST /api/chat
     ├─ query: string
     └─ response: string

POST /api/evaluate
     └─ Generate evaluation report

DELETE /api/session
       └─ Clear session
```

---

## Performance Characteristics

```
Operation                Time        Scalability
─────────────────────────────────────────────────
PDF Upload              1-2 sec      Per file
PDF Extraction          5-10 sec     Per file
Text Chunking           1 sec        Per 100 chunks
Embedding Generation    5-10 sec     Per 100 chunks
ChromaDB Storage        1 sec        Per 100 chunks
Ranking Generation      <1 sec       Per 100 candidates
Semantic Search         1-2 sec      Per query
Chatbot Response        5-15 sec     Per question
Session Clear           1-2 sec      All data

Bottlenecks:
├─ Embedding generation (GPU accelerated if available)
├─ Ollama response time (depends on hardware)
└─ PDF extraction (depends on file size)
```

---

## Configuration Impact

```
Parameter                Impact            Recommendation
────────────────────────────────────────────────────────
CHUNK_SIZE              
├─ 500      → More chunks, finer detail        For short text
├─ 700      → Balanced (DEFAULT)               Recommended
└─ 1000     → Fewer chunks, less detail        For long docs

CHUNK_OVERLAP
├─ 50       → Less redundancy, faster         For speed
├─ 100      → Balanced (DEFAULT)              Recommended
└─ 200      → More context, slower            For accuracy

EMBEDDING_BATCH_SIZE
├─ 16       → Lower memory, slower            Small RAM
├─ 32       → Balanced (DEFAULT)              Recommended
└─ 64       → Higher throughput, more RAM     Large RAM

RETRIEVAL_TOP_K
├─ 3        → Focused retrieval               For clarity
├─ 5        → Balanced (DEFAULT)              Recommended
└─ 10       → Broader search, longer response For exploration

RANKING_WEIGHTS
├─ Semantic: 0.60       Most important (content match)
├─ Skills:   0.20       Important (required skills)
├─ Exp:      0.10       Secondary (experience level)
└─ Edu:      0.10       Secondary (education level)
```

---

## Extensibility Points

```
Easy Modifications:
├─ config.py
│  ├─ Change ranking weights
│  ├─ Adjust chunk sizes
│  └─ Modify feature flags
│
├─ core/candidate_extractor.py
│  ├─ Add custom extraction patterns
│  ├─ Add new skill keywords
│  └─ Improve name detection
│
├─ core/jd_extractor.py
│  ├─ Enhanced job description parsing
│  ├─ Custom skill mappings
│  └─ Industry-specific requirements
│
├─ core/chatbot.py
│  ├─ Different Ollama models
│  ├─ Custom system prompts
│  └─ Response formatting
│
└─ app.py
   ├─ Additional UI stages
   ├─ New visualizations
   └─ Export formats
```

---

## Security Considerations

```
Current (Development):
├─ No authentication
├─ Local data only
├─ No HTTPS
└─ Single user

For Production, Add:
├─ User authentication
├─ Data encryption
├─ HTTPS/SSL
├─ Access logging
├─ Data backup
├─ Rate limiting
└─ Input validation
```

---

## Testing Strategy

```
Unit Tests (Per Module):
├─ test_session_manager.py
├─ test_pdf_parser.py
├─ test_candidate_extractor.py
├─ test_chunking.py
├─ test_embeddings.py
├─ test_ranking.py
├─ test_chatbot.py
└─ test_evaluation.py

Integration Tests:
├─ test_full_workflow.py
├─ test_ranking_accuracy.py
├─ test_chatbot_quality.py
└─ test_evaluation_metrics.py

Performance Tests:
├─ test_batch_processing.py
├─ test_memory_usage.py
└─ test_response_time.py
```

---

## Deployment Topology

```
Single Machine (Development):
  Browser → Streamlit (localhost:8501)
                ↓
            Python App
                ↓
          ┌─────┴─────┐
          ↓           ↓
        Ollama    Local Files
      (port 11434)  (data/)

Cloud Deployment (AWS):
  Users → Load Balancer
            ↓
    ┌──────┴──────┐
    ↓             ↓
  App1       App2 (Scaled)
    └──────┬──────┘
           ↓
    ┌──────┴──────┐
    ↓             ↓
  Shared     Ollama
  Storage    Cluster
```

---

## Maintenance Checklist

```
Daily:
├─ Monitor logs
├─ Check error rate
└─ Verify backups

Weekly:
├─ Review performance metrics
├─ Update dependencies
└─ Clean old sessions

Monthly:
├─ Run load tests
├─ Update embedding model
├─ Review security logs
└─ Archive old evaluations

Quarterly:
├─ Full system audit
├─ Performance optimization
├─ Dependency upgrade review
└─ Disaster recovery test
```

---

**Project Architecture Documentation Complete**

For more details, see:
- README.md - Technical reference
- GETTING_STARTED.md - First run guide
- DEPLOYMENT.md - Production deployment
- config.py - All settings
