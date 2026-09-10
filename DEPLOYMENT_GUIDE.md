# RULER RAG Platform - Streamlit UI Deployment Guide

## Overview

This guide provides step-by-step instructions to deploy and verify the production-grade Streamlit UI for the RULER Banking Regulatory RAG Platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit UI (Frontend)                     │
│                  http://localhost:8501                          │
│                                                                 │
│  - Question Input & Answer Display                             │
│  - Source Attribution & Citation Inspection                    │
│  - Real-time Token Usage Tracking                              │
│  - Chat History & Session Management                           │
└──────────────────────┬──────────────────────────────────────────┘
                       │ (HTTP Requests)
                       │ /api/chat
                       │ /api/status
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                  FastAPI Backend Server                         │
│                  http://localhost:8000                          │
│                                                                 │
│  - RAG Query Processing                                        │
│  - Document Retrieval & Ranking                                │
│  - LLM Integration (OpenAI)                                    │
│  - Citation Attribution & Grounding                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- **Python**: 3.10 or higher
- **pip**: Latest version
- **Virtual Environment** (recommended)
- **Git**: For version control
- **API Keys**:
  - OpenAI API key (for LLM completions)
  - Chroma DB access (local or cloud)

---

## Installation & Setup

### Step 1: Clone/Navigate to Project

```bash
cd /path/to/S81_kaviraja_RULER_Kalvium_Community
```

### Step 2: Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Verify installation:**
```bash
pip list | grep -E "streamlit|fastapi|openai|chromadb"
```

Expected output:
```
chromadb                  1.5.9
fastapi                   0.95.0+
openai                    3.3.1
streamlit                 1.28.0+
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-4o-mini

# Chroma DB Configuration
CHROMA_DB_PATH=./chroma_db
```

**To get your OpenAI API key:**
1. Go to https://platform.openai.com/account/api-keys
2. Create a new API key
3. Copy and paste it into the `.env` file

---

## Running the Application

### Option A: Sequential Startup (Recommended for First Run)

**Terminal 1: Start the Backend API Server**

```bash
python run_ui.py
```

Expected output:
```
==========================================================
  Starting RAG Studio Web UI on http://localhost:8000     
  - Multi-Turn Structured Chat Playground                 
  - Token-Aware & Character Document Chunker Studio       
  - Exact Source Tracing & Grounding Inspector            
  - JSON Fault Recovery & Validation Lab                  
==========================================================
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**Verify API is running:**
```bash
curl http://127.0.0.1:8000/api/status
```

Expected response:
```json
{
  "status": "online",
  "base_url": "https://api.openai.com/v1",
  "model_name": "gpt-4o-mini",
  "has_api_key": true,
  "token_chunker_available": true,
  "prompt_templates_available": true,
  "recorded_conversations_count": 0
}
```

**Terminal 2: Start the Streamlit Frontend**

```bash
streamlit run streamlit_app.py
```

Expected output:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://[your-ip]:8501

  For better performance, install pyarrow: pip install --upgrade pyarrow
```

**Browser:** Automatically opens http://localhost:8501 (or open manually)

### Option B: Parallel Startup with VS Code

Use the VS Code terminal to split and run both:

```bash
# Terminal 1
python run_ui.py

# Terminal 2 (Open new terminal)
streamlit run streamlit_app.py
```

---

## Verification Checklist

### 1. Check Backend API Status ✅

In the browser at http://localhost:8501:
- Look at the **top-right corner** for the API status indicator
- Should show: **🟢 API Online** and **Model: openai/gpt-4o-mini**

**If showing 🔴 API Offline:**
- Ensure `python run_ui.py` is running
- Check for error messages in Terminal 1
- Verify port 8000 is not in use: `netstat -ano | findstr :8000`

### 2. Test Chat Functionality ✅

**Test Case 1: Standard Query**

1. In the Streamlit UI, type: `What are AML requirements?`
2. Click **📤 Send**
3. Observe:
   - ✅ **Loading spinner** appears: "🔄 Retrieving documents..."
   - ✅ **Success message** displays: "✅ Response generated successfully!"
   - ✅ **Answer** appears in assistant message box
   - ✅ **Grounding status** shows (e.g., "✅ Grounded" in green)

### 3. Verify Source Display ✅

After answering a question, check:
- ✅ **📚 Retrieved Sources** section appears
- ✅ **Each source card shows:**
  - 📄 Source badge with number [1], [2], [3]
  - Filename (e.g., "doc1.txt")
  - 📋 Doc ID
  - 🏷️ Section name
  - 📄 Page number
  - 🔗 Chunk ID
  - **Gray box with source text** preview

- ✅ **Click "Details" button** to expand and see:
  - Full text preview
  - Character span (start-end positions)
  - Chunk index
  - Source file path

### 4. Verify Token Tracking ✅

After each question:
- ✅ **Sidebar shows updated** "Total Tokens Used" counter
- ✅ **After first response:**
  - Example: Total Tokens Used: 450 (or similar number > 0)
- ✅ **Message shows token breakdown:**
  - ⚡ Tokens - Prompt: 300 | Completion: 50 | Total: 350

### 5. Test Error Handling ✅

**Test Case 2: Network Error Simulation**

1. Stop the backend server (press Ctrl+C in Terminal 1)
2. Try to send a message in Streamlit
3. Observe:
   - ✅ Spinning loader for ~5 seconds
   - ✅ **❌ Error message appears:** "Cannot connect to the backend API. Is the server running?"
   - ✅ User message NOT added to chat history
   - ✅ Can attempt again without breaking the UI

**Test Case 3: Out-of-Domain Query**

1. Ask: `Tell me a joke about penguins`
2. Observe:
   - ✅ API responds successfully
   - ✅ Answer appears with ⚠️ status or NO_RETRIEVED_SOURCES flag
   - ✅ Warning message: "⚠️ No relevant sources were found for this query..."

### 6. Test Chat History ✅

1. Ask **3 different questions** (one at a time)
2. Verify:
   - ✅ **All messages appear** in order (user question → assistant answer)
   - ✅ **Sidebar shows** "Messages in Chat: 3"
   - ✅ Each message shows **timestamp**
   - ✅ Can scroll through history

3. **Clear Chat History:**
   - Click **"🔄 Clear Chat History"** button
   - ✅ Conversation disappears
   - ✅ "No messages yet" placeholder appears
   - ✅ Token counter resets to 0
   - ✅ "Messages in Chat" resets to 0

### 7. Test UI Responsiveness ✅

- ✅ Sidebar collapse/expand works
- ✅ Example questions are clickable
- ✅ Text input field is responsive
- ✅ No broken styling or layout issues
- ✅ Mobile-friendly design (try resizing browser)

---

## Sample Test Interactions

### Example 1: Well-Grounded Answer

**User Question:**
```
What are the AML requirements?
```

**Expected Output:**
```
✅ Regulatory Assistant (Grounded)

The Anti-Money Laundering (AML) requirements include measures to prevent 
financial institutions from being used to facilitate money laundering. These 
requirements typically include customer due diligence (CDD), enhanced due diligence 
(EDD), transaction monitoring, and suspicious activity reporting (SAR). [1] [2]

⚡ Tokens - Prompt: 256 | Completion: 47 | Total: 303

📚 Retrieved Sources
─────────────────────────────────────────────

📄 Source [1]
  ✅ Source Badge
  📋 Doc ID: DOC_BRCF_2026_001
  🏷️ Section: AML Compliance
  📄 Page: 1
  🔗 Chunk ID: chunk_001

  [Source text preview showing AML requirements...]

─────────────────────────────────────────────

📄 Source [2]
  ✅ Source Badge
  📋 Doc ID: DOC_BRCF_2026_001
  🏷️ Section: Enhanced Due Diligence
  📄 Page: 2
  🔗 Chunk ID: chunk_002

  [Source text preview showing EDD requirements...]
```

### Example 2: No Sources Found

**User Question:**
```
What's the weather today?
```

**Expected Output:**
```
⚠️ Regulatory Assistant (No Sources)

I don't have information about weather conditions in my regulatory knowledge base.
Please ask me questions about banking regulations, compliance requirements, 
or financial institution policies.

⚡ Tokens - Prompt: 128 | Completion: 32 | Total: 160

⚠️ No relevant sources were found for this query. The answer may be less grounded.
```

### Example 3: API Connection Error

**When Backend is Offline:**
```
🔄 Retrieving documents and generating answer...

❌ Error: Cannot connect to the backend API. Is the server running?
```

---

## Performance Benchmarks

### Expected Response Times

| Scenario | Time | Notes |
|----------|------|-------|
| API Status Check | 100-300ms | Instant indicator update |
| Chat Query (with 2-3 sources) | 3-8 seconds | Depends on LLM API |
| Source Display | <100ms | Local rendering |
| Error Recovery | 5-6 seconds | Timeout + fallback |
| Token Calculation | <50ms | Per message |

### Resource Usage

| Component | CPU | Memory | Notes |
|-----------|-----|--------|-------|
| FastAPI Backend | 5-15% | 150-250 MB | Varies with concurrent requests |
| Streamlit Frontend | 2-8% | 100-200 MB | Increases with chat history |
| Chroma DB | <5% | 50-100 MB | Depends on vector index size |

---

## Debugging & Troubleshooting

### Issue: "Cannot connect to the backend API"

**Solution:**
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# If occupied, kill the process or use different port
kill -9 <PID>

# Restart backend
python run_ui.py
```

### Issue: API Key Not Found

**Solution:**
```bash
# Check .env file exists
ls -la .env

# Verify key is set
echo $OPENAI_API_KEY  # Should print your key

# If not, add to .env:
OPENAI_API_KEY=sk-...
```

### Issue: Streamlit not responding

**Solution:**
```bash
# Clear Streamlit cache
streamlit cache clear

# Restart with fresh cache
streamlit run streamlit_app.py --logger.level=debug
```

### Issue: "Module not found" errors

**Solution:**
```bash
# Verify virtual environment is activated
which python  # Should show path to venv

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check installed packages
pip list
```

### Issue: No sources in response

**Possible causes:**
- Documents not loaded in Chroma DB
- Query doesn't match any indexed documents
- Relevance score threshold too high

**Solution:**
```bash
# Check sample documents exist
ls -la data/

# Verify Chroma DB initialized
python -c "from src.vector_db import VectorDBClient; db = VectorDBClient(); print(db.get_collection_count())"
```

---

## Production Deployment

### For Testing/Development
```bash
streamlit run streamlit_app.py
```

### For Production Deployment

**Using Streamlit Cloud:**
1. Push code to GitHub
2. Connect at https://share.streamlit.io
3. Deploy with one click

**Using Docker:**
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "streamlit_app.py"]
```

**Using Gunicorn + Nginx:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8501 streamlit run streamlit_app.py
```

---

## Verification Output Artifacts

When you run the application successfully, you'll generate:

### 1. Console Logs
**Backend Terminal:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
INFO:     127.0.0.1:8000 POST /api/chat
INFO:     200 OK
```

**Streamlit Terminal:**
```
Local URL: http://localhost:8501
Network URL: http://[IP]:8501
You can now view your Streamlit app in your browser.
```

### 2. Browser Output
- **Streamlit Interface** shows:
  - Green 🟢 API status indicator
  - Chat messages with timestamps
  - Source cards with metadata
  - Token counter incrementing

### 3. Output Files
- `outputs/embedding_demo_output.txt` - Embedding demonstrations
- `outputs/augmented_prompt_sample.json` - Generated prompts with context
- `outputs/grounded_generation_results.json` - Grounded answers with citations

---

## How to Verify Implementation is Complete

### ✅ Checklist for Full Implementation

- [ ] Streamlit UI loads without errors
- [ ] Backend API shows 🟢 Online status
- [ ] Can ask a regulatory question and get an answer
- [ ] Answer shows grounding status (✅ Grounded or ⚠️ No Sources)
- [ ] Retrieved sources display with:
  - [ ] Filename
  - [ ] Doc ID
  - [ ] Section/metadata
  - [ ] Chunk ID
  - [ ] Source text preview
  - [ ] Details button to expand
- [ ] Token usage updates after each message
- [ ] Chat history persists across messages
- [ ] Clear Chat History button works
- [ ] Error states display correctly (when API is down or query fails)
- [ ] Example questions are clickable
- [ ] UI is responsive (no broken layouts)
- [ ] Debug information available in sidebar
- [ ] Session information (token count, message count) updates

### ✅ Production Readiness Indicators

- [ ] No console errors in Streamlit terminal
- [ ] No "Uncaught exception" messages
- [ ] All API requests return HTTP 200 (except deliberate test failures)
- [ ] Response time < 10 seconds for most queries
- [ ] Can handle 100+ messages without slowdown
- [ ] Can recover from network errors gracefully
- [ ] UI remains responsive during API calls

---

## Next Steps

1. **Test with Multiple Questions:** Ask 5-10 different questions and observe source quality
2. **Monitor Token Usage:** Track API costs by monitoring token counts
3. **Inspect Source Quality:** Review if retrieved sources are actually relevant
4. **Test Error Cases:** Deliberately break things to see error handling
5. **Customize Prompts:** Modify `src/prompts/templates.py` for your use case
6. **Add More Documents:** Upload additional regulatory documents to `data/` folder
7. **Tune Retrieval:** Adjust chunk size, overlap, and reranking in `src/filtered_search.py`

---

## Support & Documentation

- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Backend Logs:** Check Terminal 1 for detailed API logs
- **Frontend Logs:** Check Streamlit terminal for React/JS errors
- **Debug Mode:** Enable "Show Debug Information" in Streamlit sidebar

---

## Summary

Your RAG platform is now fully deployed with:

✅ **Production-Grade Streamlit UI** for user interactions
✅ **Robust Backend API** with error handling and logging
✅ **Source Attribution** with citation verification
✅ **Token Tracking** for cost monitoring
✅ **Error Recovery** with graceful fallbacks
✅ **Professional UI** with loading states and feedback

**Start Date:** [When you begin]
**Deployment Status:** ✅ Ready for Testing
