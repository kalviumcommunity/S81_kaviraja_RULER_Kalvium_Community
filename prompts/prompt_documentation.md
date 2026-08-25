# Prompt Comparison and Documentation

## Task 1 & 2: System Message with Role, Scope, and Constraints
We designed a system message specifically for a RAG assistant acting as an HR assistant. The prompt uses distinct system and user roles to separate instructions from the user's input.

## Task 3: Compare Two Prompt Variations

### Variation 1: Vague Prompt
**System Role:** "You are an assistant that helps staff."
**User Input:** "What is our policy on remote work?"
**Mock Output:** "Employees are allowed to work remotely. Please coordinate with your manager to figure out a suitable schedule."

*Observation:* The vague prompt lacks boundaries. The model might provide overly brief, overly verbose, or inaccurate information. It has no strict instructions on what to do if the question is out of bounds or how long the response should be.

### Variation 2: Clear and Constrained Prompt
**System Role:**
```text
You are an internal HR assistant for our company. Your role is to answer staff questions clearly and safely.
Scope: Only answer questions related to company policies, benefits, and HR procedures. Do not answer technical questions.
Constraints:
- Keep the answer under 3 sentences.
- Maintain a professional and empathetic tone.
- Fallback: If you don't know the answer or it is outside your scope, reply exactly with: "I'm sorry, I don't have that information. Please contact HR directly."
```
**User Input:** "What is our policy on remote work?"
**Mock Output:** "Our remote work policy allows up to 3 days of remote work per week with manager approval. Core hours for availability are 10 AM to 3 PM local time. Please refer to the HR handbook for more details on eligible roles."

*Observation:* This prompt clearly defines the assistant's persona, its topic boundaries, format constraints (length/tone), and a safe fallback mechanism.

## Task 4: Document the Chosen Prompt
**Chosen Prompt:** Variation 2 (Clear and Constrained Prompt)

**Why it works:**
The clear and constrained prompt is significantly better because it defines strict boundaries for the model:
1. **Role and Scope:** By specifying that it's an "internal HR assistant" and can only answer HR-related queries, we reduce the risk of hallucination or answering inappropriate out-of-scope questions (like technical support).
2. **Formatting/Constraints:** Restricting the answer to "under 3 sentences" ensures that outputs remain concise and readable, which is critical for quick staff queries.
3. **Fallback Mechanism:** Explicitly defining an exact fallback phrase ("I'm sorry, I don't have that information...") safely handles edge cases when the RAG retrieval fails or when the user asks something outside the established scope. This makes the assistant highly reliable and safe for production.
