# Token Counting & Cost Estimation Results

**Model:** GPT-4o-mini 
**Pricing:** Input: $0.150/1M tokens, Output: $0.600/1M tokens

---

### Sample 1: Short Question
**Text Preview:** What is the policy for remote work?...
- **Characters:** 35
- **Words:** 7
- **Tokens:** 8
- **Ratio (Chars/Token):** 4.38
- **Ratio (Words/Token):** 0.88
- **Estimated Cost (with 50 token output):** $0.000031

---

### Sample 2: Paragraph
**Text Preview:** Employees are eligible to work remotely for up to ...
- **Characters:** 279
- **Words:** 44
- **Tokens:** 52
- **Ratio (Chars/Token):** 5.37
- **Ratio (Words/Token):** 0.85
- **Estimated Cost (with 50 token output):** $0.000038

---

### Sample 3: Full Document
**Text Preview:** Acme Corp Employee Handbook - Remote Work Policy...
- **Characters:** 866
- **Words:** 133
- **Tokens:** 172
- **Ratio (Chars/Token):** 5.03
- **Ratio (Words/Token):** 0.77
- **Estimated Cost (with 50 token output):** $0.000056

---

### Task 4 Insight
As the document scales, the number of tokens scales linearly but not 1:1 with words.
Generally, 1 token is roughly 4-5 characters or 0.75-0.85 words for standard English text. 
However, long technical words, code, and special formatting can require multiple tokens per word, changing the ratio. Keeping an eye on this ratio is crucial before sending thousands of documents to an LLM context window.
