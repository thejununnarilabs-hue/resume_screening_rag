# 🎯 GETTING STARTED - Resume Screening System

## Welcome! 👋

You now have a complete, production-ready AI-powered resume screening system. This guide walks you through the first 30 minutes.

---

## ⏱️ Timeline

- **2 mins**: Install Ollama
- **3 mins**: Install Python dependencies  
- **1 min**: Start application
- **5 mins**: Upload sample resumes
- **3 mins**: Process and generate rankings
- **2 mins**: Test chatbot with questions
- **14 mins**: Total time to see it working!

---

## 📋 Prerequisites

Verify you have:
- ✓ Python 3.9+ installed
- ✓ 4GB+ RAM available
- ✓ 2GB free disk space
- ✓ Administrator access (for installation)

---

## 🛠️ Step 1: Install Ollama (2 minutes)

Ollama provides the AI language model for answering questions about candidates.

### 1a. Download
Visit https://ollama.ai and download for your OS (Windows/Mac/Linux)

### 1b. Install & Configure
```bash
# Install and run (this downloads the model ~5GB)
ollama pull qwen2.5

# Start Ollama (keep this terminal open)
ollama serve
```

You should see:
```
time=... level=INFO msg="Ollama is running"
```

✓ Leave Ollama running in background during use

---

## 📦 Step 2: Install Dependencies (3 minutes)

### 2a. Navigate to Project
```bash
cd c:\Users\mthee\Downloads\resume_screening_rag
```

### 2b. Run Startup Script

**Windows:**
```bash
run.bat
```

**Mac/Linux:**
```bash
bash run.sh
```

The script will:
1. ✓ Create Python virtual environment (if needed)
2. ✓ Install all dependencies from requirements.txt
3. ✓ Download embedding model (~500MB, one-time)
4. ✓ Start Streamlit application

---

## 🌐 Step 3: Start Application (1 minute)

After running `run.bat` or `bash run.sh`:

1. Browser opens automatically
2. Navigate to `http://localhost:8501`
3. You see the application interface

If browser doesn't open, manually visit: **http://localhost:8501**

---

## 📤 Step 4: Upload Resumes (5 minutes)

### 4a. In the Application
1. Click **"Upload Resumes"** button
2. Select 5-10 PDF files from your computer
3. System shows upload progress

### 4b. Get Sample Resumes
For testing, use any:
- Your own resumes
- Sample resumes from internet
- OR create simple PDF files with text

### Tips:
- PDFs must be text-based (not scanned images)
- Max 500 files per session
- System auto-detects duplicates

✓ You'll see extracted candidate names and skills in a table

---

## ⚙️ Step 5: Process Resumes (3 minutes)

### 5a. Click "Start Processing"
System will:
1. Extract text from PDFs
2. Create semantic chunks (700-char pieces)
3. Generate AI embeddings
4. Store in vector database

You'll see:
- Processing progress bar
- Chunk statistics
- Vector DB confirmation

### 5b. What's Happening
```
PDF → Extract Text → Chunk Text → Generate Embeddings → Store in DB
```

---

## 📋 Step 6: Add Job Description (2 minutes)

### 6a. Paste or Upload JD

Choose one:
- **Option A**: Paste job description text directly
- **Option B**: Upload a JD PDF file

### 6b. System Extracts
- Required skills (Python, AWS, etc.)
- Preferred skills
- Experience requirements (2 years, 5+ years, etc.)
- Education requirements (BS, MS, etc.)

### 6c. Review Extracted Info
Check the extracted requirements make sense. If not, you can manually adjust.

---

## 🏆 Step 7: Generate Rankings (2 minutes)

### 7a. Click "Generate Rankings"

System calculates scores using:
```
Score = 0.60 × Semantic Match
      + 0.20 × Skill Match  
      + 0.10 × Experience Match
      + 0.10 × Education Match
```

### 7b. View Results
- Candidates ranked by score
- Top 5 to Top 50 dropdown selector
- Visual breakdown of score components
- Contact info for each candidate

### 7c. Interpretation
- **Score above 75%**: Excellent match
- **Score 50-75%**: Good match
- **Score 25-50%**: Partial match
- **Score below 25%**: Consider for second round

---

## 💬 Step 8: Test Chatbot (5 minutes)

### 8a. Make Sure Ollama is Running
Verify `ollama serve` still running in terminal

### 8b. In App - Click "Check Ollama Connection"
Should show: ✓ Ollama is running

### 8c. Ask Questions
Try these example questions:

```
"Which candidates have Python and machine learning?"

"Why was candidate 1 ranked first?"

"Who has AWS and DevOps experience?"

"Compare candidates 1 and 2"

"What are candidate 3's main skills?"
```

### 8d. How It Works
1. Your question sent to AI
2. AI searches all resumes for matching information
3. AI generates answer based on found resume content
4. Answer appears in chat

---

## ✅ First Run Checklist

After completion, verify:

- [ ] Application started at http://localhost:8501
- [ ] Uploaded 5+ resumes successfully
- [ ] Processing completed without errors
- [ ] Job description extracted correctly
- [ ] Rankings generated with scores
- [ ] Chatbot responded to at least 1 question
- [ ] Downloaded at least 1 resume

If all checked: **✓ Congratulations! System working perfectly**

---

## 🚨 If Something Goes Wrong

### Problem: "Cannot connect to Ollama"
```
Solution:
1. Open another terminal window
2. Run: ollama serve
3. Leave that terminal open
4. Refresh browser with app
```

### Problem: "Embedding model loading"
```
Solution:
1. First run downloads ~500MB model
2. This is normal and one-time only
3. Be patient, takes 2-5 minutes
4. Future runs are instant
```

### Problem: "PDF extraction failed"
```
Solutions:
1. Ensure PDF is text-based (not scanned)
2. Try a different PDF file
3. Ensure file isn't password-protected
```

### Problem: "Port 8501 already in use"
```
Solution:
Run on different port:
streamlit run app.py --server.port 8502
Then visit: http://localhost:8502
```

---

## 🎓 Learning the System

### What Each Button Does

| Button | What Happens | Time |
|--------|-------------|------|
| **Upload Resumes** | Selects PDF files | Manual |
| **Start Processing** | Chunks & embeds all resumes | 2-3 min/100 resumes |
| **Generate Rankings** | Calculates candidate scores | <1 second |
| **Check Ollama** | Verifies AI service | 2 sec |
| **Clear Session** | Deletes all session data | 1 sec |

### What Each Stage Does

1. **Upload** → Collect PDF resumes
2. **Process** → Extract text and create embeddings
3. **Job Description** → Extract requirements
4. **Ranking** → Score and rank candidates
5. **Chatbot** → Ask questions, get AI answers

---

## 💡 Pro Tips

### Tip 1: Start Small
- Test with 5-10 resumes first
- Once working, scale up to 100+

### Tip 2: Good Job Descriptions
- More detailed JD = better matching
- Include specific technologies
- Mention years of experience needed

### Tip 3: Ask Specific Questions
✓ Good: "Who has 5+ years AWS experience?"
✗ Bad: "Show me candidates"

✓ Good: "Which candidate has Python and Django?"
✗ Bad: "Any tech people?"

### Tip 4: Use Clear Session
- Between different jobs, click "Clear Session"
- Prevents mixing data from different searches

### Tip 4: Download Resumes
- Click candidate name to see full profile
- Download button available there
- Embedded PDF viewer for quick review

---

## 📊 Sample Workflow

Here's a complete workflow with timing:

```
1. Open app                           (1 min)
   ↓
2. Upload 10 resumes                  (2 min)
   ↓
3. Click "Start Processing"           (3 min)
   ↓
4. Paste job description              (1 min)
   ↓
5. Click "Generate Rankings"          (1 min)
   ↓
6. Review top 5 candidates            (2 min)
   ↓
7. Click candidate name to view profile (1 min)
   ↓
8. Ask chatbot: "Why was X ranked first?" (1 min)
   ↓
9. Download top candidate resumes     (2 min)

Total: ~14 minutes for complete workflow
```

---

## 🔧 Customization (Optional)

All customizable in `config.py`:

```python
# Change ranking weights
RANKING_WEIGHTS = {
    'semantic_similarity': 0.60,  # Change these
    'skill_match': 0.20,
    'experience_match': 0.10,
    'education_match': 0.10
}

# Change chunk size
CHUNK_SIZE = 700  # Increase for larger chunks
CHUNK_OVERLAP = 100  # More overlap = higher recall

# Change AI model
OLLAMA_MODEL = "qwen2.5"  # Can use other Ollama models
```

---

## 📖 Next Steps

### Short Term (This Week)
1. ✓ Run through workflow above
2. ✓ Test with your own job description
3. ✓ Ask various questions in chatbot
4. ✓ Export and review candidate rankings

### Medium Term (This Month)
1. Process 100+ resumes
2. Test different job descriptions
3. Fine-tune ranking weights
4. Create evaluation reports

### Long Term (Going Forward)
1. Deploy to production (see DEPLOYMENT.md)
2. Integrate with your ATS system
3. Set up automated batch processing
4. Monitor and optimize performance

---

## 📚 Documentation Files

After getting familiar, explore:

| File | Learn About |
|------|------------|
| **README.md** | Complete technical details |
| **QUICKSTART.md** | Alternative quick start |
| **DEPLOYMENT.md** | Production deployment |
| **config.py** | All configuration options |
| **core/*.py** | Module implementation details |

---

## 🆘 Getting Help

### In-App Help
1. Hover over buttons for tooltips
2. Read the info boxes (ℹ️) throughout
3. Check sidebar for session stats

### Documentation
1. Start with QUICKSTART.md
2. Then read README.md sections
3. Check specific module docstrings

### Still Stuck?
1. Check Requirements met (Python 3.9+, 4GB RAM)
2. Verify Ollama running (`ollama serve`)
3. Check all dependencies installed (`pip install -r requirements.txt`)
4. Try clearing session and starting fresh

---

## 🎯 Success Criteria

You've successfully set up the system when:

✓ Application opens at http://localhost:8501
✓ Can upload PDF resumes
✓ Processing completes without errors
✓ Rankings generated with scores
✓ Chatbot responds to questions
✓ Can download candidate resumes

---

## 🎉 You're Ready!

Your AI Resume Screening System is ready to use!

**Remember:**
1. Keep `ollama serve` running
2. Use `run.bat` or `bash run.sh` to start app
3. Visit http://localhost:8501
4. Follow the on-screen workflow

---

## 📞 Quick Reference

### Commands
```bash
# Start application
run.bat              # Windows
bash run.sh          # Mac/Linux

# Run Ollama
ollama serve

# Download Ollama model
ollama pull qwen2.5

# List available models
ollama list

# Run on specific port
streamlit run app.py --server.port 8502
```

### URLs
- Application: http://localhost:8501
- Ollama API: http://localhost:11434
- Streamlit Config: ~/.streamlit/config.toml

### Files to Know
- `app.py` - Main application
- `config.py` - Settings
- `requirements.txt` - Dependencies
- `core/` - Core modules
- `data/` - Session data (auto-created)

---

**Congratulations on setting up your Resume Screening System!**

You're now ready to screen resumes using AI. Start by uploading some resumes and follow the workflow. The system will guide you through each step.

**Enjoy! 🚀**

Questions? Check QUICKSTART.md or README.md for more details.

---

**Last Updated**: 2026-06-23  
**Version**: 1.0.0  
**Status**: ✅ Ready to Use
