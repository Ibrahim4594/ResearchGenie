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
# Simple question answering
python main.py "Explain artificial intelligence in simple terms"
```

### Interactive Mode
```bash
# Start interactive session
python main.py
# Then type your questions interactively
```

### With PDF Analysis
```bash
# Analyze PDF documents along with your query
python main.py "Summarize this research paper" --pdfs paper.pdf
```

### Custom Output File
```bash
# Save results to a specific file
python main.py "Research climate change" --output results.txt
```

### Verbose Mode (See What's Happening)
```bash
# Enable detailed logging and progress information
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
# Required - Get from https://aistudio.google.com/apikey
GOOGLE_API_KEY=your_google_api_key_here

# Optional - For Google Custom Search
GOOGLE_CSE_ID=your_custom_search_engine_id

# Optional - Advanced settings
MAX_SEARCH_RESULTS=10
LOG_LEVEL=INFO
```

---

## 🚨 Troubleshooting

**"ModuleNotFoundError" - Missing dependencies**
```bash
# Reinstall all required packages
pip install -r requirements.txt
```

**"API Key error" - Invalid or missing key**
- Ensure `.env` file exists in project root
- Verify API key is correctly configured
- Get your key from: https://aistudio.google.com/apikey
- Check for extra spaces or quotes in .env file

**No output/error - Silent failures**
```bash
# Enable verbose mode to see detailed logs
python main.py "test query" --verbose
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
- ✅ Production-grade multi-agent system architecture
- ✅ Real Google Gemini 2.0 Flash integration
- ✅ Comprehensive research and analysis capabilities
- ✅ Clean, maintainable, and well-documented code
- ✅ Robust error handling and recovery
- ✅ Professional command-line interface

**Quick test instructions:**
```bash
# Install dependencies
pip install -r requirements.txt

# Add your API key to .env file
# Get key from: https://aistudio.google.com/apikey

# Run a test query
python main.py "Your test question here"
```

---

## 🎉 Ready to Use!

**Start researching now:**
```bash
# Activate your virtual environment
.\venv\Scripts\activate

# Run your first query
python main.py "What is quantum computing?"
```

**That's it! Good luck with your research and hackathon! 🚀**

---

Made with passion for the Google ADK Hackathon
