# Resume Screening and Candidate Ranking System

A local Streamlit application for uploading PDF resumes, extracting candidate details, ranking candidates against a job description, and asking candidate-intelligence questions through a RAG chatbot.

The app runs locally, stores session data in the project folder, uses ChromaDB for resume retrieval, and uses Ollama with Qwen 2.5 for generated chatbot answers.

## Current Features

- Upload multiple PDF resumes.
- Block duplicate resume uploads by filename.
- Extract candidate name, email, phone, skills, education, and experience summary.
- Parse education into structured education-only lines such as degree, institution, year, and GPA/CGPA.
- Process a job description from PDF upload or pasted text.
- Generate candidate rankings using semantic similarity, skill match, experience match, and education match.
- View ranked candidates with filters for candidate name, resume filename, minimum score, and top-N results.
- Open candidate details from candidate name or resume filename.
- View the original uploaded resume PDF inside the candidate details page.
- Use a dedicated Candidate Intelligence Assistant page for chat.
- Ask ranking, search, comparison, project, skill, education, and experience questions.
- Compare two ranked candidates without exposing contact information.
- Click resume filenames in chatbot responses to navigate to the matching candidate details page.
- Persist chat conversations for the current app session.
- Generate evaluation records for chatbot answers.

## What The App Does Not Do

- It does not support resume formats other than PDF.
- It does not process scanned/image-only resumes unless text can be extracted from the PDF.
- It does not expose model selection in the UI.
- It does not show Ollama health/status messages in the UI.
- It does not allow switching to Llama or any model other than Qwen 2.5.

## Tech Stack

| Area | Tool |
| --- | --- |
| UI | Streamlit |
| PDF parsing | PyPDF2, pdfplumber |
| Embeddings | `BAAI/bge-base-en-v1.5` |
| Vector database | ChromaDB |
| Local LLM | Ollama |
| Chat model | `qwen2.5:latest` |
| Data handling | pandas, numpy |
| Evaluation export | openpyxl, XlsxWriter |

## Project Structure

```text
resume_screening_rag/
  app.py                         Main dashboard
  config.py                      Application configuration
  requirements.txt               Python dependencies
  run.bat                        Windows launcher
  run.sh                         Linux/macOS launcher
  core/
    candidate_extractor.py       Resume candidate extraction
    chatbot.py                   Ollama Qwen 2.5 integration
    chroma_manager.py            ChromaDB collection handling
    chunking.py                  Resume text chunking
    embeddings.py                Sentence-transformer embeddings
    evaluation.py                Chatbot evaluation metrics
    jd_extractor.py              Job description extraction
    pdf_parser.py                PDF text extraction
    ranking.py                   Candidate scoring and ranking
    retrieval.py                 Search, RAG context, direct answers
    session_manager.py           Session file/data management
  pages/
    chatbot_engine.py            Candidate Intelligence Assistant page
  prompts/
    chatbot_system_prompt.txt    Chatbot behavior prompt
    extraction_prompt.txt        Extraction guidance
  data/                          Runtime session data
  exports/                       Evaluation exports
```

## Requirements

- Python 3.9 or newer.
- Ollama installed locally.
- Qwen 2.5 model pulled in Ollama.
- Enough memory for embeddings and local inference. 8 GB RAM is recommended for a smoother run.

## Setup

1. Open a terminal in the project directory.

```bash
cd resume_screening_rag
```

2. Create and activate a virtual environment.

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

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Install and prepare Ollama.

Install Ollama from:

```text
https://ollama.com
```

Pull the required model:

```bash
ollama pull qwen2.5
```

Start Ollama:

```bash
ollama serve
```

The app is hardcoded to use:

```python
MODEL_NAME = "qwen2.5:latest"
```

5. Run the app.

```bash
streamlit run app.py
```

You can also use:

Windows:

```bat
run.bat
```

Linux/macOS:

```bash
chmod +x run.sh
./run.sh
```

## Application Workflow

### 1. Resume Upload

Use Section 1 on the dashboard to upload PDF resumes.

The app:

- Accepts PDF files.
- Blocks duplicate uploads with the same filename.
- Extracts each candidate into session data.
- Displays uploaded candidate name, email, phone, and resume filename.
- Allows removing a selected resume.

Different filenames are treated as different resumes.

### 2. Resume Processing

After uploading resumes, click `Start Processing`.

The app:

- Splits resume text into semantic sections.
- Generates embeddings with `BAAI/bge-base-en-v1.5`.
- Stores resume chunks in a ChromaDB collection.
- Marks resumes as ready for ranking and chatbot retrieval.

### 3. Job Description

After resumes are processed, Section 3 becomes available.

You can:

- Upload a job description PDF.
- Paste job description text.

The app extracts:

- Required skills.
- Preferred skills.
- Experience requirement.
- Education requirements.
- Full job description text.

### 4. Candidate Ranking

Click `Generate Rankings` after the job description is ready.

The ranking uses:

```text
Final Score =
  0.60 * Semantic Similarity
  0.20 * Skill Match
  0.10 * Experience Match
  0.10 * Education Match
```

The current implementation also blends BM25 relevance into the final ranking step.

Ranking results include:

- Candidate name.
- Resume filename.
- Match score.
- Matched required skills.
- Matched preferred skills.
- Missing required skills.
- Experience alignment.
- Education alignment.

### 5. Candidate Details

In the ranking section, click either:

- Candidate name.
- Resume filename.

The Candidate Details section shows:

- Candidate name.
- Email address.
- Contact number.
- Skills.
- Resume preview.

Click `Open Resume` to display the uploaded PDF in the page.

### 6. Candidate Intelligence Assistant

Click the chat button in the dashboard top bar to open the assistant page.

The assistant supports questions such as:

```text
Which candidates have AWS experience?
Why was candidate 1 ranked first?
Compare candidate 2 and candidate 4
Who has worked on NLP projects?
Which candidate has Python and SQL?
```

The chatbot uses:

- Ranking data.
- ChromaDB resume retrieval.
- Direct structured answers for common ranking/search/comparison questions.
- Qwen 2.5 through Ollama for generated RAG answers.

All Ollama/model checks happen silently. If the assistant cannot generate an answer because the model is unavailable, the user sees:

```text
AI Assistant is temporarily unavailable.
```

Detailed Ollama errors are logged only in backend logs.

## Clickable Resume Filenames In Chat

When a chatbot response contains a known resume filename, the assistant renders that filename as a clickable link-style control.

Clicking it:

1. Selects the matching candidate.
2. Navigates back to the dashboard.
3. Opens the candidate details section.
4. Shows the resume preview.

This is useful for responses that list candidates or compare resumes.

## Candidate Comparison Behavior

Comparison questions should reference ranked candidate numbers, for example:

```text
Compare candidate 1 and candidate 3
```

Comparison output includes only:

- Candidate name.
- Resume file name.
- Match score.
- Skills.
- Experience summary.
- Education summary.
- Key differences.

Comparison output removes:

- Email IDs.
- Phone numbers.
- LinkedIn links.
- GitHub links.
- Portfolio URLs.
- Street addresses.
- City/state/country details.
- Raw resume text.

If the same resume is selected twice, the app returns:

```text
Both selected candidates are identical. Please select two different candidates for comparison.
```

## Data And Session Storage

Runtime files are stored under `data/session_<id>/`.

Typical session contents:

```text
data/
  session_<id>/
    temp_resumes/             Uploaded PDFs
    extracted_candidates/     Extracted candidate JSON files
    chroma_db/                ChromaDB data
    generated_ground_truth/   Generated evaluation QA
    chat_sessions.json        Assistant chat sessions
```

Evaluation exports are written to:

```text
exports/chatbot_evaluation_metrics.xlsx
```

When a new app session starts, old disposable session folders are cleaned up.

Clicking `Clear Session` deletes current session data and resets the dashboard state.

## Configuration

Main settings are in [config.py](config.py).

Important values:

```python
MAX_RESUMES = 500
MAX_FILE_SIZE_MB = 1024
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
MODEL_NAME = "qwen2.5:latest"
RETRIEVAL_TOP_K = 5
CHATBOT_NUM_PREDICT = 320
```

Ranking weights are defined in both `config.py` and `core/ranking.py`.

The only supported chatbot model is:

```text
qwen2.5:latest
```

Model switching is intentionally disabled.

## Core Modules

| Module | Responsibility |
| --- | --- |
| `core/pdf_parser.py` | Extract text and metadata from PDFs |
| `core/candidate_extractor.py` | Extract candidate fields and structured education |
| `core/jd_extractor.py` | Extract skills, education, and experience requirements from JD |
| `core/chunking.py` | Split resumes into retrievable chunks |
| `core/embeddings.py` | Generate sentence embeddings |
| `core/chroma_manager.py` | Create, search, and clear ChromaDB collections |
| `core/ranking.py` | Score and rank candidates |
| `core/retrieval.py` | Build RAG context and direct structured answers |
| `core/chatbot.py` | Call Ollama with Qwen 2.5 |
| `core/evaluation.py` | Record retrieval and answer quality metrics |
| `core/session_manager.py` | Manage uploaded files and session folders |

## Troubleshooting

### The chatbot says the assistant is unavailable

Check that Ollama is running and Qwen 2.5 is installed:

```bash
ollama serve
ollama list
ollama pull qwen2.5
```

The UI intentionally does not show raw Ollama errors.

### Resume text is missing or poor quality

The PDF may be scanned, image-only, encrypted, or poorly formatted. Use a text-based PDF for best results.

### Rankings are empty

Make sure the workflow was completed in order:

1. Upload resumes.
2. Start resume processing.
3. Upload or paste a job description.
4. Generate rankings.

### Chat input is disabled

The assistant requires processed resumes and generated rankings before it can answer candidate questions.

### First run is slow

The embedding model may download or initialize on first run. Ollama may also take time to load Qwen 2.5 the first time it is used.

## Privacy Notes

- Resume files and extracted data stay local in the project `data/` folder.
- LLM generation is local through Ollama.
- The comparison answer intentionally hides contact information.
- Candidate details on the dashboard still show contact information extracted from resumes.
- Use `Clear Session` to remove current uploaded resumes and generated data.

## Development Notes

Run a basic syntax check:

```bash
python -m py_compile app.py pages/chatbot_engine.py core/*.py config.py
```

Run the app:

```bash
streamlit run app.py
```

Generated cache folders such as `__pycache__` are not required and can be safely deleted.

## License

No license file is currently included. Add a license before distributing or publishing the project.

## Acknowledgments

- Streamlit for the application UI.
- ChromaDB for local vector search.
- BAAI for the `bge-base-en-v1.5` embedding model.
- Ollama for local model serving.
- Qwen 2.5 for local chatbot generation.
#   r e s u m e _ s c r e e n i n g _ r a g  
 