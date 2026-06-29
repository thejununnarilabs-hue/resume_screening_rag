# Deployment Guide

## Development vs Production

### Local Development (Current Setup)
- ✓ Single machine
- ✓ No authentication
- ✓ Session-based data
- ✓ Ollama local
- ✓ All data local

### Production Deployment

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

## Performance Optimization

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

## Security Considerations

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

## Monitoring & Logging

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

### Health Checks
```python
def check_system_health():
    health = {
        'embedding_model': embedding_model is not None,
        'chroma_db': chroma_manager.get_collection_stats() is not None,
        'ollama': chatbot.check_model_availability(),
        'disk_space': get_free_disk_space() > 1_000_000_000  # 1GB
    }
    return health
```

## Backup & Recovery

### Automated Backups
```bash
# Backup script
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup data
tar -czf "$BACKUP_DIR/resume_db_$TIMESTAMP.tar.gz" data/

# Backup exports
tar -czf "$BACKUP_DIR/exports_$TIMESTAMP.tar.gz" exports/

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### Recovery Procedure
```bash
# Restore from backup
tar -xzf $BACKUP_DIR/resume_db_$TIMESTAMP.tar.gz -C /
tar -xzf $BACKUP_DIR/exports_$TIMESTAMP.tar.gz -C /

# Restart application
systemctl restart resume-screening
```

## Scaling Considerations

### Vertical Scaling (bigger machine)
- Increase RAM for embedding model
- More CPU cores for parallel processing
- Larger disk for vector DB

### Horizontal Scaling (multiple machines)
- Shared storage (NFS, S3)
- Distributed ChromaDB
- Load balancer (Nginx)
- Session management across servers

```python
# Shared session store (Redis)
import redis

session_store = redis.Redis(host='redis-server', port=6379)

# Save session
session_store.set(session_id, session_data)

# Load session
session_data = session_store.get(session_id)
```

## Load Testing

### Test Resume Processing
```python
import concurrent.futures
import time

def load_test_resume_processing(num_resumes=100):
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(process_resume, f"test_resume_{i}.pdf")
            for i in range(num_resumes)
        ]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error: {e}")
    
    duration = time.time() - start_time
    throughput = num_resumes / duration
    print(f"Processed {num_resumes} resumes in {duration:.2f}s ({throughput:.2f} resumes/sec)")
```

## Troubleshooting Deployment

### High Memory Usage
- Reduce batch size in embeddings
- Enable streaming for large datasets
- Monitor ChromaDB index size

### Slow Ranking Generation
- Index optimization for ChromaDB
- Parallel similarity calculations
- Caching common operations

### Chatbot Timeout
- Increase request timeout
- Optimize retrieval queries
- Pre-cache embeddings

## Environment-Specific Configs

### Development
```python
DEBUG = True
LOG_LEVEL = "DEBUG"
BATCH_SIZE = 16
CHROMA_PERSIST = False
```

### Staging
```python
DEBUG = False
LOG_LEVEL = "INFO"
BATCH_SIZE = 32
CHROMA_PERSIST = True
```

### Production
```python
DEBUG = False
LOG_LEVEL = "WARNING"
BATCH_SIZE = 64
CHROMA_PERSIST = True
ENABLE_MONITORING = True
ENABLE_BACKUP = True
```

## CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy Resume Screening

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -t resume-screening .
      
      - name: Run tests
        run: pytest tests/
      
      - name: Push to registry
        run: docker push myregistry/resume-screening
      
      - name: Deploy
        run: kubectl apply -f k8s/deployment.yaml
```

## Support & Maintenance

### Regular Maintenance
- Update dependencies monthly: `pip install --upgrade -r requirements.txt`
- Clear old session data: `python scripts/cleanup_sessions.py`
- Archive old evaluations: `python scripts/archive_evaluations.py`
- Review logs for errors

### Monitoring Checklist
- [ ] Check disk space weekly
- [ ] Review error logs daily
- [ ] Monitor Ollama service
- [ ] Verify backups complete
- [ ] Update embeddings model quarterly
- [ ] Performance metrics trending
