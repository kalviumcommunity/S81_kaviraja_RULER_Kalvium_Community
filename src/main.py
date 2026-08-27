"""
RAG Application Starter - Hyperparameter Experiments & Entry Point.
Executes parameter experiments across temperature, max_tokens, top_p, and stop sequences.
Generates structured comparison logs for factual, grounded RAG applications.
"""

import os
from parameter_experiments import run_parameter_experiments


def main():
    sample_log_path = os.path.join("outputs", "sample_output.txt")
    experiments_log_path = os.path.join("outputs", "parameter_experiments_output.txt")

    os.makedirs("outputs", exist_ok=True)
    if os.path.exists(sample_log_path):
        os.remove(sample_log_path)
    if os.path.exists(experiments_log_path):
        os.remove(experiments_log_path)

    print("==================================================================")
    print("      RAG Assistant - LLM Hyperparameter Tuning Suite             ")
    print("==================================================================")

    # Run parameter experiments and log outputs
    run_parameter_experiments(log_file=sample_log_path)
    run_parameter_experiments(log_file=experiments_log_path)

    print(f"[SUCCESS] Parameter experiments completed successfully.")
    print(f"Log outputs generated at:\n - '{sample_log_path}'\n - '{experiments_log_path}'")


if __name__ == "__main__":
    main()
