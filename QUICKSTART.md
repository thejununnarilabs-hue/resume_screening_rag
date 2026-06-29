# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Ollama (5 mins)
1. Download from https://ollama.ai
2. Install and run
3. In terminal: `ollama pull qwen2.5`
4. Ollama should be running: `ollama serve`

### Step 2: Setup Project (2 mins)
```bash
cd resume_screening_rag

# Windows:
run.bat

# Mac/Linux:
bash run.sh
```

### Step 3: Launch App (1 min)
- Browser opens automatically at `http://localhost:8501`
- System is ready!

## First Run Workflow

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

## Key Commands

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

# Download Qwen2.5 (run in another terminal)
ollama pull qwen2.5

# List installed models
ollama list
```

## Troubleshooting

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

## Tips & Tricks

1. **Batch Processing**: Upload 50+ resumes for better ranking insights

2. **Custom Job Descriptions**: More detailed JDs = better matching

3. **Chatbot Questions**: Try specific skills/experiences

4. **Ranking Customization**: View Top 5 through Top 50

5. **Session Management**: "Clear Session" between different batches

## Features Demo

### Try These Questions in Chatbot:
- "Which candidates have Python and machine learning experience?"
- "Who has worked on cloud projects?"
- "Why was candidate 5 ranked higher than candidate 6?"
- "What are candidate 1's main technical skills?"
- "Find candidates with AWS and DevOps experience"

### View Rankings:
- Check semantic similarity scores
- See skill match percentages
- Review experience alignment
- Examine education fit

### Export Candidate Profiles:
- Download resumes
- View embedded PDFs
- Copy contact info

## System Requirements

✓ Python 3.9+
✓ 4GB RAM minimum
✓ 2GB disk space
✓ Ollama installed
✓ Internet for first-time model download

## Performance Notes

- First embedding model load: ~2-3 mins
- Processing 100 resumes: ~5-10 mins
- Ranking generation: < 1 sec
- Chatbot response: 5-15 secs

## Next Steps

1. Check README.md for detailed documentation
2. Review config.py for customization options
3. Explore evaluation reports in exports/
4. Modify ranking weights for your use case

## Support Resources

- **README.md**: Full documentation
- **config.py**: Configuration options
- **core/*.py**: Module documentation
- **prompts/**: System and extraction prompts

## Video Walkthrough

[Placeholder for video tutorial]

Enjoy using the Resume Screening System! 🎉
