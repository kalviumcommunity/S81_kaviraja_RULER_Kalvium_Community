"""
Relevance Quality Check & Sanity Report CLI Script (Tasks 1 - 5).

Executes known query-chunk relevance tests, evaluates ranking order, documents failing/surprising cases,
and persists sanity report artifacts.
"""

import os
import json
import sys

# Ensure src directory is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from relevance_checker import RelevanceSanityChecker


def main():
    print("==================================================================")
    print("      RAG Pipeline — Relevance Quality Check & Sanity Suite       ")
    print("==================================================================\n")

    outputs_dir = "outputs"
    os.makedirs(outputs_dir, exist_ok=True)

    json_output_path = os.path.join(outputs_dir, "relevance_sanity_results.json")
    txt_output_path = os.path.join(outputs_dir, "relevance_sanity_report.txt")

    print("[Task 1 & 2] Initializing Relevance Sanity Suite & Running Similarity Ranking...")
    checker = RelevanceSanityChecker()
    summary = checker.run_sanity_check()

    print("[Task 4 & 5] Generating Sanity Report and Saving Output Artifacts...")
    checker.generate_sanity_report(
        sanity_summary=summary,
        output_txt_path=txt_output_path,
        output_json_path=json_output_path
    )

    print(f"\n -> Sanity Report text written to: '{txt_output_path}'")
    print(f" -> Sanity Report JSON written to: '{json_output_path}'")

    print("\n==================================================================")
    print("                 RELEVANCE SANITY REPORT SUMMARY                  ")
    print("==================================================================")
    print(f"Total Test Cases: {summary['total_test_count']}")
    print(f"Standard Relevance Passes: {summary['standard_passes']} / {summary['standard_tests_count']} ({summary['pass_rate_percentage']}%)")
    print(f"Standard Relevance Failures: {summary['standard_failures']}")
    print(f"Identified Surprising/Failing Edge Cases: {summary['surprising_cases_count']}")

    fail_case = summary.get("failing_or_surprising_case_summary", {})
    print("\n------------------------------------------------------------------")
    print(f"TASK 3: IDENTIFIED FAILING / SURPRISING CASE ANALYSIS")
    print("------------------------------------------------------------------")
    print(f"Case ID: {fail_case.get('case_id')}")
    print(f"Title: {fail_case.get('title')}")
    print(f"Query: \"{fail_case.get('query')}\"")
    print(f"Top Ranked Chunk ID: {fail_case.get('top_ranked_chunk_id')} (Score: {fail_case.get('top_ranked_score', 0.0):.4f})")
    print(f"Finding: {fail_case.get('relevance_finding')}")
    print(f"Pipeline Implication: {fail_case.get('pipeline_implication')}")
    print("==================================================================\n")


if __name__ == "__main__":
    main()
