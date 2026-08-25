import tiktoken

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """
    Task 1: Count tokens for a given text using tiktoken.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback for models not yet in tiktoken, use o200k_base or cl100k_base
        encoding = tiktoken.get_encoding("o200k_base")
    
    return len(encoding.encode(text))

def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """
    Task 3: Calculate a simple cost estimate.
    Using GPT-4o-mini pricing as an example:
    Input: $0.150 per 1M tokens
    Output: $0.600 per 1M tokens
    """
    input_cost = (input_tokens / 1_000_000) * 0.150
    output_cost = (output_tokens / 1_000_000) * 0.600
    return input_cost + output_cost

def run_token_analysis():
    # Task 2: Three samples of varying length
    sample_1_short = "What is the policy for remote work?"
    
    sample_2_paragraph = (
        "Employees are eligible to work remotely for up to two days per week, "
        "provided they have completed their probationary period. Remote days must "
        "be approved by the direct manager at least 48 hours in advance. "
        "Core hours of 10 AM to 3 PM must be strictly observed, regardless of location."
    )
    
    sample_3_document = (
        "Acme Corp Employee Handbook - Remote Work Policy\n\n"
        "1. Introduction\n"
        "This policy outlines the guidelines for remote work at Acme Corp. We believe "
        "in offering flexibility while maintaining high productivity and collaboration.\n\n"
        "2. Eligibility\n"
        "All full-time employees who have been with the company for at least 90 days "
        "are eligible. Exceptions require VP approval.\n\n"
        "3. Equipment and Security\n"
        "Employees must use company-issued laptops. Using personal devices for company "
        "work is strictly prohibited due to security constraints. Ensure your home Wi-Fi "
        "is secured with WPA3.\n\n"
        "4. Working Hours\n"
        "While we offer flexibility, core working hours are 10:00 AM to 3:00 PM (EST). "
        "During this time, you are expected to be online and available for meetings.\n\n"
        "5. Performance\n"
        "Remote work is a privilege that can be revoked if performance drops. Managers "
        "will review remote work arrangements quarterly."
    )
    
    samples = [
        ("Short Question", sample_1_short),
        ("Paragraph", sample_2_paragraph),
        ("Full Document", sample_3_document)
    ]
    
    print("=== Token Counting & Cost Estimation ===")
    print("Model: GPT-4o-mini (Input: $0.150/1M, Output: $0.600/1M)\n")
    
    for name, text in samples:
        char_count = len(text)
        word_count = len(text.split())
        token_count = count_tokens(text)
        
        # We'll treat the sample as input to estimate cost, assuming a 50-token output response for context.
        est_cost = estimate_cost(input_tokens=token_count, output_tokens=50)
        
        # Task 4: Show the length-token relationship
        char_per_token = char_count / token_count if token_count else 0
        word_per_token = word_count / token_count if token_count else 0
        
        print(f"--- {name} ---")
        print(f"Text Preview: {text[:50]}...")
        print(f"Characters: {char_count}")
        print(f"Words: {word_count}")
        print(f"Tokens: {token_count}")
        print(f"Ratio (Chars/Token): {char_per_token:.2f}")
        print(f"Ratio (Words/Token): {word_per_token:.2f}")
        print(f"Estimated Cost (with 50 token output): ${est_cost:.6f}\n")
        
    print("=== Task 4 Insight ===")
    print("As the document scales, the number of tokens scales linearly but not 1:1 with words.")
    print("Generally, 1 token is roughly 4 characters or 0.75 words for standard English text.")
    print("However, long technical words, code, and special formatting can require multiple tokens per word,")
    print("changing the ratio. Keeping an eye on this ratio is crucial before sending thousands of documents to an LLM.")

if __name__ == "__main__":
    run_token_analysis()
