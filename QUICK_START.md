# 🚀 RULER RAG Platform - Quick Start Guide

## What You're Getting

A **production-grade Retrieval-Augmented Generation (RAG) platform** with:

✅ **Beautiful Streamlit UI** - Interactive question & answer interface
✅ **Robust FastAPI Backend** - RESTful API with source attribution
✅ **Citation Verification** - Grounded answers with retrieved sources
✅ **Token Tracking** - Monitor API usage and costs
✅ **Error Handling** - Graceful fallbacks and user feedback
✅ **Professional Design** - Responsive, polished interface

---

## Quick Start (5 minutes)

### Option 1: Automatic Startup (Easiest)

```bash
# Make sure you're in the project root directory
cd /path/to/S81_kaviraja_RULER_Kalvium_Community

# Activate virtual environment (Windows)
.\venv\Scripts\Activate.ps1

# Or on macOS/Linux
source venv/bin/activate

# Start everything with one command
python start_ruler.py
```

That's it! Your browser will automatically open to http://127.0.0.1:8501

### Option 2: Manual Startup (Two Terminals)

**Terminal 1 - Start Backend:**
```bash
python run_ui.py
# You should see: "Uvicorn running on http://127.0.0.1:8000"
```

**Terminal 2 - Start Frontend:**
```bash
streamlit run streamlit_app.py
# You should see: "Local URL: http://localhost:8501"
```

---

## Your First Interaction

1. **Open the Browser**
   - http://127.0.0.1:8501

2. **You'll See:**
   ```
   ⚖️ RULER
   Banking Regulatory RAG Platform
   
   [🟢 API Online | Model: openai/gpt-4o-mini]
   [Session Info | 0 tokens used | 0 messages]
   ```

3. **Ask a Question**
   - Type: `What are AML requirements?`
   - Click: 📤 Send

4. **You'll Get:**
   ```
   ✅ Grounded Answer
   [The answer text here with [1] citation markers]
   
   ⚡ Tokens: Prompt: 256 | Completion: 45 | Total: 301
   
   📚 Retrieved Sources
   ─────────────────────
   📄 Source [1]
   📋 Doc ID: DOC_BRCF_2026_001
   🏷️ Section: AML Compliance
   📄 Page: 1
   🔗 Chunk ID: chunk_001
   
   [Source text preview...]
   ```

5. **Continue Conversing**
   - Ask more questions
   - Track tokens in sidebar
   - View complete chat history

---

## Verify Implementation

### Method 1: Visual Verification (Quick)

After starting the UI, check these indicators:

- [ ] **Top-right shows:** 🟢 API Online
- [ ] **Model shown:** openai/gpt-4o-mini
- [ ] **Ask a question** and get an answer
- [ ] **Sources display** below answer
- [ ] **Token counter** updates after each message
- [ ] **Clear Chat** button works

### Method 2: Automated Testing (Comprehensive)

In a new terminal (while servers are running):

```bash
python test_rag_implementation.py
```

You'll see:

```
╔══════════════════════════════════════════════════════════╗
║  RAG Platform Integration Test Suite                    ║
╚══════════════════════════════════════════════════════════╝

Test: API Status
✅ API Online - Model: gpt-4o-mini
ℹ️  API Key Available: true
ℹ️  Token Chunker Available: true

Test: Chat Functionality
✅ Question: 'What are AML requirements?'
ℹ️  Answer Length: 487 characters
ℹ️  Citations Found: 2
ℹ️  Grounded: True
ℹ️  Response Time: 2.34s

... [more tests] ...

╔══════════════════════════════════════════════════════════╗
║  Test Summary                                           ║
╠══════════════════════════════════════════════════════════╣
✅ PASSED | API Status
✅ PASSED | Chat Functionality
✅ PASSED | Source Display
✅ PASSED | Error Handling
✅ PASSED | Token Tracking

Results:
  Total Tests: 5
  Passed: 5
  Failed: 0
✅ All tests passed! Implementation is complete.
╚══════════════════════════════════════════════════════════╝
```

---

## File Structure

```
S81_kaviraja_RULER_Kalvium_Community/
├── streamlit_app.py                 # ✨ NEW - Main Streamlit UI
├── test_rag_implementation.py        # ✨ NEW - Automated test suite
├── start_ruler.py                   # ✨ NEW - Startup manager
├── DEPLOYMENT_GUIDE.md              # ✨ NEW - Full deployment guide
├── run_ui.py                        # Backend server launcher
├── requirements.txt                 # Updated with Streamlit
├── data/
│   ├── doc1.txt
│   ├── doc2.txt
│   └── ...
├── src/
│   ├── server.py                    # FastAPI backend
│   ├── vector_db.py
│   ├── context_injection.py
│   ├── citation_attribution.py
│   └── ... [other backend modules]
├── chroma_db/                       # Vector database
├── outputs/                         # Generated outputs
└── frontend/                        # Original HTML/CSS/JS frontend
```

---

## Key Features Explained

### 1. Question Input & Answer Display

```
💬 Ask a Regulatory Question
[Text input field]
[📤 Send button]
```

- Type any compliance question
- Get grounded answers from documents
- Track response quality

### 2. Source Attribution

```
📚 Retrieved Sources
┌──────────────────────────────┐
│ 📄 Source [1]                │
│ 📋 Doc ID: DOC_BRCF_2026_001 │
│ 🏷️ Section: AML Compliance   │
│ 📄 Page: 1                   │
│ 🔗 Chunk ID: chunk_001       │
│                              │
│ [Source text preview...]     │
│ [Details button ▼]           │
└──────────────────────────────┘
```

Click **Details** to see:
- Full text of source
- Character span (exact location)
- Chunk metadata
- Document path

### 3. Session Tracking

```
🎛️ Controls (Sidebar)
├─ Session Information
│  ├─ Total Tokens Used: 543
│  └─ Messages in Chat: 3
├─ 🔄 Clear Chat History
└─ 🔧 Settings
   └─ ☑️ Show Debug Information
```

### 4. Example Prompts

```
📌 Example Questions
┌────────────────────────────────────────┐
│ 💡 What are AML requirements?         │
│ 💡 Explain Basel IV Liquidity         │
│ 💡 What are payment thresholds?       │
│ 💡 Compliance requirements?            │
└────────────────────────────────────────┘
```

Click any to use as starting point

---

## What's Behind the Scenes

### Streamlit UI (`streamlit_app.py`)
- **Lines 1-100**: Imports and styling (CSS)
- **Lines 100-150**: Session state initialization
- **Lines 150-300**: API interaction functions
  - `check_api_status()` - Verify backend is online
  - `query_rag_api()` - Send question and get grounded answer
- **Lines 300-500**: UI rendering functions
  - `render_chat_message()` - Display Q&A pairs
  - `render_source_card()` - Show sources with metadata
  - `render_chat_interface()` - Main chat area
- **Lines 500+**: Main app entry point

### Backend API (`src/server.py`)
- **`/api/status`** - Returns model name, API key status
- **`/api/chat`** - Takes question, returns grounded answer with citations
- **`/api/chunk`** - Chunks documents into tokens
- **`/api/trace`** - Traces citations to source text

### Integration Flow

```
User Types Question
         ↓
[streamlit_app.py] sends HTTP POST to /api/chat
         ↓
[src/server.py] receives request
         ↓
Retrieves relevant chunks from Chroma DB
         ↓
Injects chunks into prompt context
         ↓
Calls OpenAI API for grounded completion
         ↓
Attribution engine verifies citations
         ↓
Response with citations returned to Streamlit
         ↓
[streamlit_app.py] renders answer + sources
         ↓
User sees grounded answer with sources
```

---

## Common Questions

### Q: How do I change the port?

**For Streamlit:**
```bash
streamlit run streamlit_app.py --server.port 8080
```

**For FastAPI:**
Edit `run_ui.py`:
```python
uvicorn.run("src.server:app", host="127.0.0.1", port=9000)
```

### Q: Where do I see API errors?

**Check:**
1. **Browser console** - F12 → Console tab
2. **Streamlit terminal** - Error messages with 🔴 emoji
3. **Backend terminal** - Shows API request logs

### Q: How do I add my own documents?

1. Add `.txt` files to the `data/` folder
2. Restart the application
3. Ask questions about the new documents

### Q: Can I use a different LLM?

Yes! Edit `.env` file:
```bash
OPENAI_BASE_URL=https://your-api-endpoint.com/v1
OPENAI_MODEL_NAME=your-model-name
OPENAI_API_KEY=your-api-key
```

### Q: What if I don't have an OpenAI key?

The app includes mock responses for testing:
```bash
# In Streamlit, check "Show Debug Information" to enable mock mode
# Or modify streamlit_app.py to set use_mock=True
```

### Q: How much does this cost?

Cost depends on:
- **Tokens used**: ~$0.0001-0.001 per 1000 tokens (varies by model)
- **Chroma DB storage**: Free for local usage
- **UI hosting**: Free locally, ~$5-50/month on cloud

Monitor in sidebar: "Total Tokens Used"

---

## Troubleshooting

### ❌ "Cannot connect to the backend API"

```bash
# Check if API is running on port 8000
netstat -ano | findstr :8000

# If nothing shown, start backend:
python run_ui.py
```

### ❌ "API Key not found"

```bash
# Create .env file
echo OPENAI_API_KEY=sk-... > .env

# Or export as environment variable
set OPENAI_API_KEY=sk-...  # Windows
export OPENAI_API_KEY=sk-...  # macOS/Linux
```

### ❌ Streamlit not installing

```bash
# Try with pip3
pip3 install streamlit requests

# Or update pip first
python -m pip install --upgrade pip
pip install streamlit
```

### ❌ "Module not found" errors

```bash
# Make sure virtual environment is active
# Windows
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate

# Reinstall all packages
pip install -r requirements.txt --force-reinstall
```

### ❌ No sources in responses

This is normal for out-of-domain questions. The app correctly:
- Detects when no relevant sources match
- Returns ⚠️ "No Sources" indicator
- Prevents hallucinations

---

## Next Steps

1. **Explore the UI**
   - Ask different questions
   - Check source quality
   - Monitor token usage

2. **Customize Prompts**
   - Edit `src/prompts/templates.py`
   - Adjust system role for specific domain
   - Fine-tune temperature and other parameters

3. **Add More Documents**
   - Place `.txt` or `.pdf` files in `data/` folder
   - Restart application
   - Ask questions about new content

4. **Deploy to Production**
   - See `DEPLOYMENT_GUIDE.md` for cloud options
   - Use Docker for containerization
   - Set up monitoring and logging

5. **Integrate with Other Systems**
   - Use `/api/chat` endpoint from any app
   - Batch process with `/api/chunk`
   - Reference `src/server.py` for API spec

---

## Architecture Summary

```
┌─────────────────────────────────────────────┐
│         Streamlit Web Interface             │
│  • Question input                           │
│  • Real-time answer display                 │
│  • Source inspection                        │
│  • Session tracking                         │
└────────────────┬────────────────────────────┘
                 │ HTTP API Calls
                 ↓
┌─────────────────────────────────────────────┐
│        FastAPI Backend (http://127.0.0.1:8000)  │
│  • Query processing                         │
│  • Document retrieval                       │
│  • Citation verification                    │
│  • Token management                         │
└────────────────┬────────────────────────────┘
                 │
     ┌───────────┼───────────┐
     ↓           ↓           ↓
┌─────────┐ ┌──────────┐ ┌──────────┐
│ Chroma  │ │ OpenAI   │ │ Prompt   │
│ Vector  │ │ LLM      │ │ Templates│
│ DB      │ │ API      │ │          │
└─────────┘ └──────────┘ └──────────┘
```

---

## Support

- **Documentation**: See `DEPLOYMENT_GUIDE.md`
- **Tests**: Run `python test_rag_implementation.py`
- **API Docs**: http://127.0.0.1:8000/docs (when running)
- **Issues**: Check terminal output and browser console

---

## Summary

✅ **Implementation Complete**
- Streamlit UI with professional design
- Full backend integration
- Source attribution with citations
- Token tracking and cost monitoring
- Error handling and graceful fallbacks
- Automated testing suite
- Comprehensive documentation

**Ready to use!** Start with:
```bash
python start_ruler.py
```

Then open http://127.0.0.1:8501 and start asking questions! 🎉
