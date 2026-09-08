"""
Chunk Re-Ranking for Precision Demo Runner (Tasks 1 to 5).
"""

import os
import sys

# Ensure project root and src are in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.rerank_pipeline import run_reranking_pipeline

if __name__ == "__main__":
    run_reranking_pipeline()
