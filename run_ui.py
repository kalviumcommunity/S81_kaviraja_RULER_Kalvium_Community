"""
Launcher script for RAG Studio Web UI.
Starts the FastAPI backend and serves the frontend on http://localhost:8000
"""

import sys
import os
import uvicorn

# Ensure project root and src are on python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

if __name__ == "__main__":
    print("==========================================================")
    print("  Starting RAG Studio Web UI on http://localhost:8000     ")
    print("  - Multi-Turn Structured Chat Playground                 ")
    print("  - Token-Aware & Character Document Chunker Studio       ")
    print("  - Exact Source Tracing & Grounding Inspector            ")
    print("  - JSON Fault Recovery & Validation Lab                  ")
    print("==========================================================")
    uvicorn.run("src.server:app", host="127.0.0.1", port=8000, reload=False)
