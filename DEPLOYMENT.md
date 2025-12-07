# Deployment & Setup Guide

Complete step-by-step guide for deploying the Personal Research Concierge Agent in production environments.

---

## 🚀 Quick Setup (5 Minutes)

### 1. Environment Setup

```bash
# Navigate to project directory
cd "adk agent"

# Activate virtual environment
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install production dependencies
pip install -r requirements.txt
```

### 2. API Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Google API key
# Windows: notepad .env
# macOS/Linux: nano .env
```

Add your keys to `.env`:
```bash
GOOGLE_API_KEY=your_google_gemini_api_key_here
GOOGLE_CSE_ID=your_custom_search_engine_id_here  # Optional
```

### 3. Test Installation

```bash
# Run setup verification
python test_setup.py

# Should see: "✅ All systems ready!"
```

### 4. Run Your First Research

```bash
# Basic usage
python main.py "What are the latest trends in quantum computing?"

# With PDFs
python main.py "AI ethics" --pdfs paper1.pdf paper2.pdf

# Verbose logging
python main.py "Machine learning advances" --verbose
```

---

## 📋 Detailed Setup Instructions

### Getting API Keys

#### Google Gemini API Key (REQUIRED)

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key
4. Add to `.env`: `GOOGLE_API_KEY=your_key_here`

**Free Tier Limits:**
- 60 requests per minute
- 1,500 requests per day
- Sufficient for most research tasks

#### Google Custom Search Engine ID (OPTIONAL but RECOMMENDED)

1. Go to [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" to create a new search engine
3. Under "Sites to search", select "Search the entire web"
4. Create and copy the "Search engine ID" (cx parameter)
5. Add to `.env`: `GOOGLE_CSE_ID=your_cse_id_here`

**Free Tier Limits:**
- 100 searches per day (free)
- 10,000 searches per day (paid: $5/1000 queries)

**Note:** Without CSE ID, the system uses Duck Duck Go as fallback (free but less reliable)

---

## 🔧 Configuration Options

### Environment Variables

Edit `.env` to customize:

```bash
# REQUIRED
GOOGLE_API_KEY=your_key_here

# OPTIONAL - Better search results
GOOGLE_CSE_ID=your_cse_id_here

# Logging
LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/research_concierge.log

# Agent Settings
MAX_SEARCH_RESULTS=10    # Sources per query
MAX_QUALITY_ITERATIONS=3 # Quality improvement loops
TARGET_QUALITY_SCORE=90  # Quality threshold (0-100)

# Performance
WEB_SCRAPE_RATE_LIMIT=10  # Requests per 10 seconds
ENABLE_SEARCH_CACHE=true  # Cache search results
SEARCH_CACHE_TTL=3600     # Cache time (1 hour)
```

### Command Line Options

```bash
# Show all options
python main.py --help

# Common options:
python main.py "query" --max-sources 20      # More sources
python main.py "query" --verbose             # Debug logging
python main.py "query" --output my_file.txt  # Custom output
python main.py "query" --no-interactive      # Script mode
```

---

## 📂 Project Structure

```
adk-agent/
├── main.py                    # Entry point (CLI)
├── requirements.txt           # Production dependencies
├── .env                       # Your configuration (create from .env.example)
├── .env.example               # Configuration template
│
├── src/
│   ├── agents/               # 7 intelligent agents
│   │   ├── user_intent_agent.py
│   │   ├── web_search_agent.py
│   │   ├── pdf_agent.py
│   │   ├── source_summarizer_agent.py
│   │   ├── fact_check_agent.py
│   │   ├── synthesis_agent.py
│   │   └── quality_loop_agent.py
│   │
│   ├── tools/                # Custom tools
│   │   └── __init__.py       # Google Search, PDF, Web scraper
│   │
│   ├── schemas/              # Pydantic models
│   ├── memory/               # Memory & sessions
│   └── utils/                # Logging & observability
│
├── outputs/                  # Research briefs (auto-created)
└── logs/                     # Application logs (auto-created)
```

---

## 🎯 Usage Examples

### Basic Research

```bash
python main.py "What are the latest developments in renewable energy?"
```

### Research with PDFs

```bash
python main.py "Climate change impacts" --pdfs \
  reports/ipcc_2024.pdf \
  papers/climate_study.pdf
```

### Batch Processing (Script Mode)

```bash
# research.sh
#!/bin/bash

queries=(
  "Quantum computing applications"
  "AI in healthcare"
  "Blockchain technology trends"
)

for query in "${queries[@]}"; do
  python main.py "$query" \
    --max-sources 15 \
    --output "outputs/${query// /_}.txt" \
    --no-interactive
done
```

### Custom Output Location

```bash
python main.py "Machine learning" \
  --output ~/Documents/research/ml_brief.txt \
  --max-sources 20
```

### Verbose Debugging

```bash
python main.py "Deep learning" --verbose
# Logs detailed execution to console and logs/research_concierge.log
```

---

## 🐛 Troubleshooting

### "No GOOGLE_API_KEY found"

**Problem:** API key not detected

**Solution:**
1. Ensure `.env` file exists (not `.env.example`)
2. Check `GOOGLE_API_KEY=your_key` is set correctly
3. No spaces around `=`
4. Restart terminal/IDE after setting

### "Rate limit exceeded"

**Problem:** Too many API requests

**Solution:**
1. Wait a few minutes
2. Reduce `MAX_SEARCH_RESULTS` in `.env`
3. Enable caching: `ENABLE_SEARCH_CACHE=true`
4. Consider upgrading to paid tier

### "PDF processing failed"

**Problem:** Can't extract text from PDF

**Solution:**
1. Ensure PDF is not encrypted/password-protected
2. Check file path is correct
3. Try different PDF (some scanned PDFs need OCR)
4. Check logs for specific error

### "Search returns no results"

**Problem:** Web search not working

**Solution:**
1. System automatically falls back to DuckDuckGo
2. For better results, add `GOOGLE_CSE_ID` to `.env`
3. Check internet connection
4. Review `logs/research_concierge.log`

### Import Errors

**Problem:** `ModuleNotFoundError`

**Solution:**
```bash
# Ensure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 📊 Performance Optimization

### For Faster Execution

```bash
# Reduce sources
MAX_SEARCH_RESULTS=5

# Skip quality loop (less accurate but faster)
MAX_QUALITY_ITERATIONS=1

# Use cache
ENABLE_SEARCH_CACHE=true
```

### For Better Quality

```bash
# More sources
MAX_SEARCH_RESULTS=20

# More improvement iterations
MAX_QUALITY_ITERATIONS=5
TARGET_QUALITY_SCORE=95

# Add PDFs for depth
python main.py "query" --pdfs doc1.pdf doc2.pdf doc3.pdf
```

### For Production Deployment

```bash
# Enable all optimizations
ENABLE_SEARCH_CACHE=true
SEARCH_CACHE_TTL=7200  # 2 hours

# Rate limiting
WEB_SCRAPE_RATE_LIMIT=5  # More conservative

# Comprehensive logging
LOG_LEVEL=INFO
LOG_FILE=logs/production.log
```

---

## 🔒 Security Best Practices

### 1. Protect API Keys

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use environment variables in production
export GOOGLE_API_KEY="your_key"
export GOOGLE_CSE_ID="your_cse_id"
```

### 2. Rate Limiting

```python
# Built-in rate limiting prevents abuse
# Configured in src/tools/__init__.py
@limits(calls=10, period=10)  # 10 calls per 10 seconds
```

### 3. Input Validation

```python
# All inputs are validated via Pydantic schemas
# See src/schemas/__init__.py
```

---

## 📈 Monitoring & Logging

### Log Files

```bash
# View real-time logs
tail -f logs/research_concierge.log

# Search logs
grep "ERROR" logs/research_concierge.log
grep "Quality Score" logs/research_concierge.log
```

### Log Levels

- **DEBUG**: Detailed execution information
- **INFO**: Standard operation logs (recommended)
- **WARNING**: Potential issues
- **ERROR**: Errors that didn't stop execution
- **CRITICAL**: Fatal errors

### Memory Export

Research sessions are automatically saved:
```bash
outputs/memory_session_<timestamp>.json
```

Contains:
- User preferences
- All sources gathered
- Fact-check results
- Quality iteration history

---

## 🚢 Production Deployment

### Option 1: Local Server

```bash
# Run as background service (Linux/macOS)
nohup python main.py "query" --no-interactive > output.log 2>&1 &

# Windows
start /B python main.py "query" --no-interactive
```

### Option 2: Docker (Recommended)

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV GOOGLE_API_KEY=""
ENV LOG_LEVEL="INFO"

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
```

Build and run:
```bash
docker build -t research-concierge .
docker run -e GOOGLE_API_KEY="your_key" \
  research-concierge "quantum computing"
```

### Option 3: Cloud Deployment

**AWS Lambda:**
- Package project as zip
- Set environment variables
- Configure timeout (10+ minutes)
- Use Lambda layers for dependencies

**Google Cloud Run:**
- Containerize with Docker
- Deploy to Cloud Run
- Set memory to 2GB+
- Configure timeout appropriately

---

## 🧪 Testing

### Unit Tests

```bash
# Run tests (if pytest installed)
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Integration Test

```bash
# Test full pipeline
python main.py "test query" --max-sources 3
```

### Verify Setup

```bash
python test_setup.py
```

---

## 📚 Additional Resources

### Documentation
- **README.md** - Project overview
- **ARCHITECTURE.md** - Technical details
- **QUICKSTART.md** - 5-minute guide
- **DEPLOYMENT.md** - This file

### API Documentation
- [Google Gemini API](https://ai.google.dev/docs)
- [Google Custom Search](https://developers.google.com/custom-search)
- [Google ADK](https://ai.google.dev/adk)

### Community
- GitHub Issues: Report bugs
- Discussions: Ask questions
- Wiki: Community guides

---

## 🎓 Advanced Configuration

### Custom Agent Parameters

Edit agent files in `src/agents/` to customize behavior:

```python
# src/agents/quality_loop_agent.py
self.max_iterations = 5  # Default: 3
self.target_score = 95   # Default: 90
```

### Custom Tools

Add new tools in `src/tools/__init__.py`:

```python
class CustomTool:
    def __init__(self):
        self.name = "custom_tool"

    def execute(self, params):
        # Your implementation
        pass
```

### Custom Schemas

Add new data models in `src/schemas/__init__.py`:

```python
from pydantic import BaseModel

class CustomSchema(BaseModel):
    field1: str
    field2: int
```

---

## 🔄 Updating

```bash
# Pull latest changes
git pull origin main

# Upgrade dependencies
pip install --upgrade -r requirements.txt

# Clear cache
rm -rf outputs/*.json
rm -rf logs/*
```

---

## ✅ Pre-Submission Checklist

Before submitting your hackathon project:

- [ ] `.env` file created with valid `GOOGLE_API_KEY`
- [ ] Tested with `python test_setup.py`
- [ ] Run successful research query
- [ ] Verified output in `outputs/research_brief.txt`
- [ ] Checked logs in `logs/research_concierge.log`
- [ ] Reviewed README.md
- [ ] All dependencies installed
- [ ] No errors in console
- [ ] Quality score ≥ 85 on test query

---

**Status:** ✅ PRODUCTION READY

**Version:** 1.0.0

**Last Updated:** 2025-01-15

Need help? Check the troubleshooting section or review the logs!
