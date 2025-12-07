# Personal Research Concierge Agent

🤖 **AI-Powered Research Assistant using Google Gemini 2.0 Flash**

Built for hackathon - Advanced Multi-agent research system with intelligent CLI interface

---

## 🚀 Quick Start

### 1. Setup (One Time)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Edit `.env` file and add your Google API key:
```
GOOGLE_API_KEY=your_actual_key_here
```

Get your API key: https://aistudio.google.com/apikey

### 3. Run It!

**Easy way - Double click:** `RUN.bat`

**Or in VS Code terminal:**
```bash
.\venv\Scripts\activate
python main.py "What is quantum computing?"
```

---

## 💡 Usage Examples

### Quick Research Query
```bash
python main.py "Explain artificial intelligence in simple terms"
```

### Interactive Mode
```bash
python main.py
# Then type your questions interactively
```

### With PDF Analysis
```bash
python main.py "Summarize this research paper" --pdfs paper.pdf
```

### Custom Output
```bash
python main.py "Research climate change" --output results.txt
```

### Verbose Mode (See What's Happening)
```bash
python main.py "What is machine learning?" --verbose
```

---

## 🌟 Features

✅ Multi-agent architecture with 7 specialized agents
✅ Powered by Google Gemini 2.0 Flash AI
✅ Advanced web search integration (Google Custom Search + DuckDuckGo fallback)
✅ Intelligent PDF document analysis
✅ Built-in fact-checking capabilities
✅ Comprehensive research synthesis
✅ Quality improvement loop for optimal results
✅ Production-ready error handling and recovery
✅ Full logging and observability features

---

## 📁 Project Structure

```
adk agent/
├── main.py                # Main CLI entry point
├── requirements.txt       # Python dependencies
├── .env                   # Configuration (add your API key!)
├── RUN.bat               # Easy startup script
├── src/
│   ├── agents/           # 7 specialized AI agents
│   ├── tools/            # Research tools (search, PDF, etc.)
│   ├── memory/           # Memory and session management
│   ├── schemas/          # Data models
│   └── utils/            # Logging and utilities
└── docs/                 # Documentation
```

---

## 🛠️ Command Line Options

```bash
python main.py [OPTIONS] [QUERY]

Options:
  QUERY                    Your research question
  --pdfs FILE [FILE ...]   PDF files to analyze
  --output, -o FILE        Output file (default: outputs/research_brief.txt)
  --max-sources N          Maximum search results (default: 10)
  --verbose, -v            Show detailed progress
  --help, -h               Show help message
```

---

## 🧪 Test It

```bash
# Simple test
python main.py "Hello, how are you?"

# Research test
python main.py "What are the latest developments in AI?"

# Should see detailed, well-structured response!
```

---

## 📚 Documentation

- **DEPLOYMENT.md** - Complete production deployment guide
- **PRODUCTION_READY.md** - Feature completeness checklist
- **ARCHITECTURE.md** - Detailed system design and architecture
- **README.md** - Comprehensive project documentation
- **PRESENTATION_SCRIPT.md** - Presentation guidelines

---

## ⚙️ Configuration (.env file)

```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional
GOOGLE_CSE_ID=your_custom_search_engine_id
MAX_SEARCH_RESULTS=10
LOG_LEVEL=INFO
```

---

## 🚨 Troubleshooting

**"ModuleNotFoundError"**
```bash
pip install -r requirements.txt
```

**"API Key error"**
- Check `.env` file exists
- Verify API key is correct
- Get key from: https://aistudio.google.com/apikey

**No output/error**
```bash
python main.py "test query" --verbose
# This shows detailed logs
```

---

## 🎯 What It Does

1. **Understands** - Intelligently parses your research question
2. **Searches** - Crawls the web for relevant and credible information
3. **Analyzes** - Processes PDFs and documents if provided
4. **Summarizes** - Condenses information from all sources
5. **Fact-checks** - Verifies claims for accuracy and reliability
6. **Synthesizes** - Combines everything into a comprehensive brief
7. **Improves** - Refines quality through iterative enhancement

**Result:** Professional research brief ready to use immediately!

---

## 🏆 Built With

- **Google Gemini 2.0 Flash API** - Advanced AI model
- **Python 3.13** - Latest Python version
- **Pydantic** - Robust data validation
- **BeautifulSoup4** - Web content extraction
- **PDFPlumber** - Document processing
- **Multi-agent Architecture** - Coordinated task orchestration

---

## 📄 License

MIT License - Free to use and modify

---

## 👨‍💻 For Hackathon Judges

**This project demonstrates:**
- ✅ Production-grade multi-agent system
- ✅ Real Google Gemini 2.0 integration
- ✅ Comprehensive research capabilities
- ✅ Clean, maintainable code
- ✅ Full error handling
- ✅ Professional CLI interface

**To test:**
```bash
pip install -r requirements.txt
# Add API key to .env
python main.py "Your test question here"
```

---

## 🎉 Ready to Use!

**Start researching:**
```bash
.\venv\Scripts\activate
python main.py "What is quantum computing?"
```

**That's it! Good luck with your hackathon! 🚀**
