# Architecture Documentation

## System Overview

The Personal Research Concierge Agent is a **multi-agent system** built on Google's Agent Developer Kit (ADK) that orchestrates intelligent research automation.

---

## Design Principles

### 1. Agent Autonomy
Each agent is responsible for a specific research task and operates independently:
- **UserIntentAgent**: Intent extraction
- **WebSearchAgent**: Web research
- **PDFDocumentAgent**: Document processing
- **SourceSummarizerAgent**: Content summarization
- **FactCheckAgent**: Verification & validation
- **SynthesisAgent**: Brief compilation
- **QualityLoopAgent**: Iterative improvement

### 2. Parallel Execution
Research agents (Web + PDF) run **in parallel** to maximize efficiency:
```python
# Parallel execution pattern
web_results = web_search_agent.search(query)     # ║
doc_results = pdf_agent.process_documents(files)  # ║ Parallel
# Both complete before proceeding                 # ▼
```

### 3. Type Safety
All inter-agent communication uses **Pydantic models**:
```python
UserIntent(topic, scope, style, keywords)
SourceSummary(claim, evidence, source_url, reliability_score)
ResearchBrief(executive_summary, insights, evidence_table, ...)
```

### 4. Memory Persistence
**MemoryBank** stores all context:
- User preferences (topic, style, scope)
- Source cache (all gathered sources)
- Fact-check results
- Quality iteration history

### 5. Observability
Every operation is logged and traced:
- Structured logging with agent context
- Trace IDs for full operation tracking
- Performance metrics (duration, counts)

---

## Agent Specifications

### UserIntentAgent

**Purpose**: Extract structured research intent from natural language

**Input**: `str` - User's research query

**Output**: `UserIntent`
```python
{
  "topic": "quantum computing",
  "scope": "deep",
  "style": "technical",
  "keywords": ["quantum", "computing", "algorithms"],
  "constraints": null
}
```

**Process**:
1. Send query to LLM with intent extraction prompt
2. Parse JSON response
3. Fallback to heuristic extraction if JSON fails
4. Store preferences in MemoryBank
5. Return UserIntent object

**Key Features**:
- Infers scope from keywords (deep, quick, overview, etc.)
- Detects style from context (academic, technical, executive)
- Extracts searchable keywords
- Handles malformed LLM responses gracefully

---

### WebSearchAgent

**Purpose**: Gather web sources in parallel

**Input**: `query: str, num_results: int`

**Output**: `WebSearchResult`
```python
{
  "query": "quantum computing",
  "urls": ["url1", "url2", ...],
  "summaries": ["summary1", "summary2", ...],
  "results": [...]
}
```

**Process**:
1. Execute search via GoogleSearchTool
2. Gather URLs and initial summaries
3. Optionally scrape URLs for full content
4. Enhance summaries with LLM
5. Return structured results

**Parallel Execution**:
```python
# Multiple queries in parallel
queries = ["topic", "keyword1", "keyword2"]
results = [search(q) for q in queries]  # Parallel
```

**Tools Used**:
- GoogleSearchTool (custom)
- WebScraperTool (custom)

---

### PDFDocumentAgent

**Purpose**: Extract and clean text from documents

**Input**: `file_path: str, session_id: Optional[str]`

**Output**: `DocumentAnalysis`
```python
{
  "file_path": "research.pdf",
  "extracted_text": "...",
  "key_sections": ["intro", "methods", ...],
  "metadata": {
    "num_pages": 25,
    "session_id": "pdf_research"
  }
}
```

**Process**:
1. Check/create session for pause/resume support
2. Detect file type (.pdf, .txt, .md)
3. Extract text using PDFProcessorTool
4. Clean and structure content
5. Optionally enhance with LLM analysis
6. Save session state for recovery

**Long-Running Support**:
- Creates session with `session_id`
- Saves progress to SessionManager
- Can pause on error or timeout
- Resume from saved state

**Tools Used**:
- PDFProcessorTool (pdfplumber + PyPDF2)

---

### SourceSummarizerAgent

**Purpose**: Convert raw sources to structured summaries

**Input**: `WebSearchResult | DocumentAnalysis`

**Output**: `List[SourceSummary]`
```python
[
  {
    "claim": "Quantum computers use superposition",
    "evidence": "Research shows...",
    "source_url": "https://...",
    "reliability_score": 85,
    "timestamp": "2025-01-15T10:30:00",
    "source_type": "web"
  },
  ...
]
```

**Process**:
1. For each source, extract main claim
2. Identify supporting evidence
3. Calculate reliability score (0-100) based on:
   - Clarity of evidence
   - Specificity of claims
   - Presence of citations/data
4. Store in MemoryBank
5. Return list of SourceSummary objects

**Reliability Scoring**:
- Uses LLM to evaluate source quality
- Considers multiple factors
- Scores 70+ are "high quality"

---

### FactCheckAgent

**Purpose**: Verify claims and detect contradictions

**Input**: `List[SourceSummary]`

**Output**: `List[FactCheckResult]`
```python
[
  {
    "claim": "Quantum supremacy achieved in 2019",
    "verdict": "True",
    "confidence": 0.95,
    "contradictions": [],
    "supporting_sources": ["url1", "url2"]
  },
  ...
]
```

**Process**:
1. Extract unique claims from sources
2. For each claim:
   - Gather supporting evidence
   - Send to LLM for verification
   - Parse verdict (True/False/Unverified)
3. Cross-reference sources to find contradictions
4. Store fact-checks in MemoryBank

**Contradiction Detection**:
```python
# Groups sources by topic
# Compares claims within each group
# Uses LLM to identify conflicts
```

---

### SynthesisAgent

**Purpose**: Create comprehensive research brief

**Input**: `sources, fact_checks, contradictions`

**Output**: `ResearchBrief`

**Process**:
1. Generate executive summary (LLM)
2. Extract top 10 insights from high-reliability sources
3. Build evidence table (all sources)
4. Extract data points (numbers, stats, dates)
5. Build glossary of technical terms
6. Generate suggested reading list
7. Create follow-up questions

**Components**:

| Component | Generation Method |
|-----------|-------------------|
| Executive Summary | LLM with style preference |
| Top Insights | LLM extraction + ranking |
| Evidence Table | Direct from SourceSummary |
| Data Points | Regex pattern matching |
| Glossary | LLM term extraction |
| Suggested Reading | Reliability-sorted sources |
| Next Questions | LLM generation |

---

### QualityLoopAgent

**Purpose**: Iteratively improve research quality

**Input**: `ResearchBrief`

**Output**: `ResearchBrief` (improved)

**Loop Logic**:
```python
current_brief = initial_brief
iteration = 0

while iteration < max_iterations:
    score = evaluate_quality(current_brief)

    if score.overall_score >= 90:
        break  # Target reached

    if score.needs_revision:
        current_brief = improve_brief(current_brief, score)

    iteration += 1

return current_brief
```

**Quality Evaluation**:
```python
QualityScore {
  clarity_score: 0-100,
  correctness_score: 0-100,
  completeness_score: 0-100,
  overall_score: average,
  feedback: "detailed feedback",
  needs_revision: bool
}
```

**Improvement Strategy**:
- Focus on lowest-scoring dimension
- Rewrite executive summary if clarity < 85
- Add more insights if completeness < 85
- Extract additional data points as needed

**Iteration Tracking**:
All iterations stored in MemoryBank:
```python
memory_bank.add_iteration({
  "iteration": 2,
  "quality_score": 87,
  "clarity": 90,
  "correctness": 88,
  "completeness": 84,
  "feedback": "..."
})
```

---

## Data Flow

```
User Query (str)
    ↓
UserIntent (Pydantic)
    ↓
    ├──→ WebSearchResult (Pydantic) ──┐
    │                                  ↓
    └──→ DocumentAnalysis (Pydantic) ─┤
                                       ↓
                            List[SourceSummary] (Pydantic)
                                       ↓
                            List[FactCheckResult] (Pydantic)
                                       ↓
                            ResearchBrief (Pydantic)
                                       ↓
                            QualityScore (Pydantic)
                                       ↓
                            Final ResearchBrief
```

---

## Memory Architecture

### MemoryBank Structure
```python
{
  "user_preferences": {
    "topic": "...",
    "scope": "...",
    "style": "...",
    "keywords": [...],
    "timestamp": "..."
  },

  "source_cache": [
    {SourceSummary},
    {SourceSummary},
    ...
  ],

  "fact_checks": [
    {FactCheckResult},
    ...
  ],

  "iterations": [
    {
      "iteration": 1,
      "quality_score": 75,
      "feedback": "..."
    },
    ...
  ],

  "research_context": {
    "key": "value",
    ...
  }
}
```

### Session Management
```python
{
  "session_id": {
    "id": "session_123",
    "created_at": "...",
    "status": "active" | "paused" | "closed",
    "metadata": {...},
    "state": {...},
    "memory": MemoryBank()
  }
}
```

---

## Tool Integration

### Google Search Tool
```python
GoogleSearchTool.search(query, num_results) → dict
{
  "query": "...",
  "urls": [...],
  "summaries": [...],
  "raw_results": [...]
}
```

### PDF Processor Tool
```python
PDFProcessorTool.extract_text(file_path) → dict
{
  "file_path": "...",
  "extracted_text": "...",
  "num_pages": 25,
  "metadata": {...},
  "key_sections": [...]
}
```

### Web Scraper Tool
```python
WebScraperTool.scrape_url(url) → dict
{
  "url": "...",
  "title": "...",
  "content": "...",
  "links": [...]
}
```

---

## Error Handling

### Strategy
1. **Graceful degradation**: All agents have fallback behavior
2. **Logging**: Every error logged with context
3. **Session persistence**: Long operations can recover from errors
4. **Partial results**: Return best-effort results even on failures

### Examples

**LLM Response Parsing Fails**:
```python
try:
    data = json.loads(llm_response)
except:
    # Fallback to heuristic parsing
    data = fallback_parse(llm_response)
```

**PDF Processing Fails**:
```python
try:
    text = pdfplumber.extract(file)
except:
    # Fallback to PyPDF2
    text = pypdf2_extract(file)
```

**Search Returns No Results**:
```python
if not urls:
    logger.warning("No search results")
    return WebSearchResult(query=query, urls=[], summaries=[])
```

---

## Performance Considerations

### Parallelization
- Web search and PDF processing run in parallel
- Multiple search queries executed concurrently
- Source summarization can be batched

### Caching
- MemoryBank caches all sources
- Prevents re-processing same data
- Supports session export/import

### Rate Limiting
- Tools implement respectful delays
- API calls are logged and monitored
- Fallbacks prevent cascade failures

---

## Extension Points

### Add New Agent
```python
class CustomAgent:
    def __init__(self, client: genai.Client):
        self.client = client

    def process(self, input_data) -> OutputSchema:
        # Your logic here
        pass
```

### Add New Tool
```python
class CustomTool:
    def __init__(self):
        self.name = "custom_tool"

    def execute(self, params) -> dict:
        # Your logic here
        pass

# Create ADK declaration
def create_custom_tool_declaration() -> types.Tool:
    return types.Tool(
        function_declarations=[
            types.FunctionDeclaration(...)
        ]
    )
```

### Modify Quality Metrics
```python
# In QualityLoopAgent
self.target_score = 95  # Higher threshold
self.max_iterations = 5  # More iterations
```

---

## Testing Strategy

### Unit Tests
- Test each agent independently
- Mock LLM responses
- Verify schema compliance

### Integration Tests
- Test agent pipelines
- Verify data flow
- Check memory persistence

### End-to-End Tests
- Full research queries
- Quality threshold validation
- Output format verification

---

## Deployment Considerations

### Environment Setup
```bash
python -m venv venv
pip install -r requirements.txt
export GOOGLE_API_KEY="..."
```

### Resource Requirements
- **Memory**: ~500MB for typical research
- **Disk**: Logs and outputs grow over time
- **API**: Gemini API rate limits apply

### Monitoring
- Check `logs/research_concierge.log`
- Monitor trace_context for bottlenecks
- Track quality scores over time

---

**Version**: 1.0.0
**Last Updated**: 2025-01-15
