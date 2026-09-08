"""
Embedding Fundamentals Demonstration Module

Provides functionality to:
1. Generate real vector embeddings using LLMClient
2. Programmatically verify vector length/dimension consistency across sample texts
3. Calculate cosine similarity between embedding vectors
4. Compare similar vs. dissimilar text pairs
5. Generate formatted, reproducible output files for verification
"""

import math
import os
import json
from typing import List, Dict, Any, Tuple, Optional

try:
    from llm_client import LLMClient
except ImportError:
    from src.llm_client import LLMClient


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Calculate cosine similarity between two numeric vectors of identical length.
    Returns float in range [-1.0, 1.0].
    """
    if not vec_a or not vec_b:
        raise ValueError("Vector inputs cannot be empty.")
    if len(vec_a) != len(vec_b):
        raise ValueError(f"Vector dimensions do not match: {len(vec_a)} vs {len(vec_b)}")

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def verify_vector_dimensions(embeddings: List[List[float]]) -> Dict[str, Any]:
    """
    Programmatically verify that every embedding vector in the input list
    has exactly the same non-zero length and contains valid numeric data.
    """
    if not embeddings:
        return {
            "is_consistent": False,
            "detected_dimension": 0,
            "lengths": [],
            "all_numeric": False,
            "status": "FAIL - Empty input"
        }

    lengths = [len(vec) for vec in embeddings]
    expected_dim = lengths[0]

    is_valid_dim = expected_dim > 0
    all_same = all(length == expected_dim for length in lengths)
    all_numeric = all(
        isinstance(val, (int, float)) and not math.isnan(val) and not math.isinf(val)
        for vec in embeddings
        for val in vec
    )

    is_consistent = is_valid_dim and all_same and all_numeric

    return {
        "is_consistent": is_consistent,
        "detected_dimension": expected_dim,
        "lengths": lengths,
        "all_numeric": all_numeric,
        "status": "PASS" if is_consistent else "FAIL"
    }


def format_vector_preview(vec: List[float], preview_size: int = 4) -> str:
    """Format a floating point vector as a concise preview string."""
    if not vec:
        return "[]"
    head = ", ".join(f"{val:.4f}" for val in vec[:preview_size])
    return f"[{head}, ...]"


class EmbeddingDemonstration:
    """Engine for executing and reporting embedding fundamentals demonstration."""

    def __init__(self, client: Optional[LLMClient] = None):
        self.client = client or LLMClient()

    def run_demonstration(
        self,
        text_a: str = "The customer wants to check their bank account balance.",
        text_b: str = "The user would like to know how much money is available in their account.",
        text_c: str = "A football match was played during heavy rain.",
        output_txt_path: str = os.path.join("outputs", "embedding_demo_output.txt"),
        output_json_path: str = os.path.join("outputs", "embedding_demonstration_results.json")
    ) -> Dict[str, Any]:
        """
        Executes Tasks 1 to 5 of the Embedding Fundamentals Demonstration:
        1. Embed sample texts using real API client
        2. Report and verify vector dimension consistency
        3. Compute cosine similarity (A-B vs A-C)
        4. Validate similar pair scores higher than dissimilar pair
        5. Generate reproducible sample output files
        """
        texts = [text_a, text_b, text_c]

        # Task 1: Generate embeddings
        embeddings, usage = self.client.generate_embeddings(texts)
        if not embeddings or len(embeddings) != 3:
            raise RuntimeError("Failed to generate embeddings for demonstration texts.")

        vec_a, vec_b, vec_c = embeddings[0], embeddings[1], embeddings[2]

        # Task 2: Verify vector dimensions programmatically
        dim_check = verify_vector_dimensions(embeddings)
        detected_dim = dim_check["detected_dimension"]

        # Task 3: Compare similar and dissimilar texts using Cosine Similarity
        sim_ab = cosine_similarity(vec_a, vec_b)
        sim_ac = cosine_similarity(vec_a, vec_c)

        is_similarity_passed = sim_ab > sim_ac

        # Task 5: Build structured results object & formatted text report
        provider = "OpenAI-Compatible API"
        if "openrouter" in self.client.base_url.lower():
            provider = "OpenRouter (OpenAI-Compatible API)"

        results = {
            "demonstration_metadata": {
                "embedding_provider": provider,
                "base_url": self.client.base_url,
                "embedding_model": self.client.embedding_model,
                "texts_embedded_count": len(texts),
                "vector_dimension": detected_dim
            },
            "sample_texts": {
                "Text_A_Original": {
                    "text": text_a,
                    "dimension": len(vec_a),
                    "vector_preview": format_vector_preview(vec_a)
                },
                "Text_B_Similar": {
                    "text": text_b,
                    "dimension": len(vec_b),
                    "vector_preview": format_vector_preview(vec_b)
                },
                "Text_C_Unrelated": {
                    "text": text_c,
                    "dimension": len(vec_c),
                    "vector_preview": format_vector_preview(vec_c)
                }
            },
            "dimension_verification": {
                "expected_dimension": detected_dim,
                "text_a_dimension": len(vec_a),
                "text_b_dimension": len(vec_b),
                "text_c_dimension": len(vec_c),
                "all_dimensions_consistent": dim_check["is_consistent"],
                "verification_status": dim_check["status"]
            },
            "similarity_comparison": {
                "similar_pair": {
                    "pair": "Text A vs Text B (similar meaning)",
                    "cosine_similarity": round(sim_ab, 6)
                },
                "unrelated_pair": {
                    "pair": "Text A vs Text C (unrelated meaning)",
                    "cosine_similarity": round(sim_ac, 6)
                },
                "comparison_check": {
                    "condition": "similarity(Text A, Text B) > similarity(Text A, Text C)",
                    "is_passed": is_similarity_passed,
                    "result_status": "PASS — similar texts scored higher than unrelated texts" if is_similarity_passed else "FAIL"
                }
            },
            "token_usage": usage
        }

        # Build human-readable text output strictly following Task 5 format
        output_lines = [
            "Embedding Demonstration",
            "=======================",
            "",
            "Embedding Provider:",
            f"{provider}",
            "",
            "Embedding Model:",
            f"{self.client.embedding_model}",
            "",
            "Texts Embedded:",
            f"{len(texts)}",
            "",
            "",
            "Text A:",
            f'"{text_a}"',
            "",
            "Vector dimension:",
            f"{len(vec_a)}",
            "",
            "Vector preview:",
            f"{format_vector_preview(vec_a)}",
            "",
            "--------------------------------------------------",
            "",
            "Text B:",
            f'"{text_b}"',
            "",
            "Vector dimension:",
            f"{len(vec_b)}",
            "",
            "Vector preview:",
            f"{format_vector_preview(vec_b)}",
            "",
            "--------------------------------------------------",
            "",
            "Text C:",
            f'"{text_c}"',
            "",
            "Vector dimension:",
            f"{len(vec_c)}",
            "",
            "Vector preview:",
            f"{format_vector_preview(vec_c)}",
            "",
            "==================================================",
            "",
            "Dimension Verification",
            "",
            f"Text A: {len(vec_a)}",
            f"Text B: {len(vec_b)}",
            f"Text C: {len(vec_c)}",
            "",
            f"All dimensions consistent: {'PASS' if dim_check['is_consistent'] else 'FAIL'}",
            "",
            "==================================================",
            "",
            "Cosine Similarity",
            "",
            "Text A vs Text B (similar):",
            f"{sim_ab:.4f}",
            "",
            "Text A vs Text C (unrelated):",
            f"{sim_ac:.4f}",
            "",
            "Result:",
            f"{'PASS — similar texts scored higher than unrelated texts' if is_similarity_passed else 'FAIL — similarity ordering unexpected'}",
        ]

        text_content = "\n".join(output_lines) + "\n"

        # Save sample outputs
        os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)
        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write(text_content)

        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        return results


if __name__ == "__main__":
    demo = EmbeddingDemonstration()
    results = demo.run_demonstration()
    print("Embedding Demonstration Executed Successfully!")
    print(f"Vector Dimension: {results['demonstration_metadata']['vector_dimension']}")
    print(f"Similarity A-B (similar): {results['similarity_comparison']['similar_pair']['cosine_similarity']}")
    print(f"Similarity A-C (unrelated): {results['similarity_comparison']['unrelated_pair']['cosine_similarity']}")
    print(f"Result: {results['similarity_comparison']['comparison_check']['result_status']}")
